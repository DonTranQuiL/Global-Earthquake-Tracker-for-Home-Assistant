import pytest
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.global_earthquakes.const import (
    DOMAIN,
    CONF_INSTANCE_NAME,
    CONF_MIN_MAG_USA,
    CONF_MIN_MAG_GLOBAL,
    CONF_MONITORED_COUNTRIES,
    CONF_MAP_MARKERS,
    CONF_SCAN_INTERVAL,
)

# =========================================================================
# 1. CONFIG & OPTIONS FLOW TESTS
# =========================================================================


@pytest.mark.asyncio
async def test_config_flow_success(hass: HomeAssistant):
    """Test successful initial config flow entry registration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_INSTANCE_NAME: "World Seismic",
            CONF_MIN_MAG_USA: 3.0,
            CONF_MIN_MAG_GLOBAL: 5.0,
            CONF_MONITORED_COUNTRIES: ["ALL"],
            CONF_MAP_MARKERS: 15,
            CONF_SCAN_INTERVAL: 300,
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Earthquakes (World Seismic)"
    assert result2["data"][CONF_MIN_MAG_USA] == 3.0


@pytest.mark.asyncio
async def test_options_flow_update(hass: HomeAssistant):
    """Test options flow successfully updates thresholds and countries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Earthquakes (World Seismic)",
        data={CONF_INSTANCE_NAME: "World Seismic"},
        options={
            CONF_MIN_MAG_GLOBAL: 5.0,
            CONF_MONITORED_COUNTRIES: ["ALL"],
            CONF_MAP_MARKERS: 20,
        },
        entry_id="eq_options_test",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MIN_MAG_USA: 2.5,
            CONF_MIN_MAG_GLOBAL: 4.0,
            CONF_MONITORED_COUNTRIES: ["EUROPE", "Japan"],
            CONF_MAP_MARKERS: 10,
            CONF_SCAN_INTERVAL: 600,
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_MONITORED_COUNTRIES] == ["EUROPE", "Japan"]


# =========================================================================
# 2. COORDINATOR & DYNAMIC SENSOR TESTS
# =========================================================================


@pytest.mark.asyncio
async def test_coordinator_and_dynamic_sensors(hass: HomeAssistant, aioclient_mock):
    """Test USGS data fetching, smart filtering, and dynamic sensor spawning."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Earthquakes (Global Test)",
        data={
            CONF_INSTANCE_NAME: "Global Test",
            CONF_MIN_MAG_USA: 2.5,
            CONF_MIN_MAG_GLOBAL: 4.5,
            CONF_MONITORED_COUNTRIES: ["ALL"],
            CONF_MAP_MARKERS: 20,
            CONF_SCAN_INTERVAL: 300,
        },
        entry_id="eq_live_test",
    )
    entry.add_to_hass(hass)

    # Mock a USGS GeoJSON response with 3 earthquakes
    mock_usgs_payload = {
        "features": [
            {
                "id": "eq_japan",
                "properties": {
                    "mag": 6.1,
                    "place": "Tokyo, Japan",
                    "time": 1700000000000,
                    "type": "earthquake",
                    "tsunami": 1,
                    "alert": "yellow",
                },
                "geometry": {"coordinates": [139.0, 35.0, 10.0]},
            },
            {
                "id": "eq_cali_large",
                "properties": {
                    "mag": 3.5,
                    "place": "Los Angeles, CA",
                    "time": 1700000000000,
                    "type": "earthquake",
                    "tsunami": 0,
                },
                "geometry": {"coordinates": [-118.0, 34.0, 5.0]},
            },
            {
                "id": "eq_cali_small",  # Should be filtered out because it is < 2.5 in the USA
                "properties": {
                    "mag": 1.5,
                    "place": "San Francisco, CA",
                    "time": 1700000000000,
                    "type": "earthquake",
                    "tsunami": 0,
                },
                "geometry": {"coordinates": [-122.0, 37.0, 5.0]},
            },
        ]
    }

    aioclient_mock.get(
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson",
        json=mock_usgs_payload,
    )

    # Patch the cache so we don't write files during tests
    with (
        patch(
            "custom_components.global_earthquakes.cache.GlobalEarthquakeCache.load_cache",
            return_value=[],
        ),
        patch(
            "custom_components.global_earthquakes.cache.GlobalEarthquakeCache.save_cache"
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # 1. Verify the Static Main Sensor
    main_sensor = hass.states.get(
        "sensor.earthquake_tracker_global_test_latest_magnitude"
    )
    assert main_sensor is not None
    # Highest magnitude should be the state
    assert main_sensor.state == "6.1"

    # 2. Verify Smart Filtering (Coordinator should only have 2 events, small Cali quake is filtered out)
    assert main_sensor.attributes.get("monitored_events_count") == 2

    # 3. Verify Dynamic Sensors Spawned Correctly
    # HA slugifies "6.1M - Tokyo, Japan" into "6_1m_tokyo_japan"
    japan_sensor = hass.states.get(
        "sensor.earthquake_tracker_global_test_6_1m_tokyo_japan"
    )
    assert japan_sensor is not None
    assert japan_sensor.state == "6.1"

    # Tsunami warning was set to 1, so the custom icon path should reflect the tsunami pin
    assert (
        japan_sensor.attributes.get("entity_picture")
        == "/global_earthquakes_assets/tsunami.png"
    )

    # Verify the larger California quake spawned
    cali_sensor = hass.states.get(
        "sensor.earthquake_tracker_global_test_3_5m_los_angeles_ca"
    )
    assert cali_sensor is not None
    assert cali_sensor.state == "3.5"
