from unittest.mock import MagicMock

import pytest
from homeassistant.const import EntityCategory
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.global_earthquakes.const import DOMAIN
from custom_components.global_earthquakes.sensor import (
    EarthquakeLastUpdateSensor,
    GlobalEarthquakeEventSensor,
    GlobalEarthquakeHistorySensor,
    GlobalEarthquakeSensor,
    async_setup_entry,
)


@pytest.fixture
def mock_coordinator():
    coord = MagicMock()
    coord.data = [
        {
            "id": "eq1",
            "magnitude": 6.5,
            "location": "Tokyo, Japan",
            "event_type": "earthquake",
            "tsunami_warning": True,
            "alert_level": "Red",
            "significance": 500,
            "time": "01-01-2026 12:00:00 UTC",
            "depth_km": 10.0,
            "latitude": 35.0,
            "longitude": 139.0,
            "url": "http://example.com",
        }
    ]
    coord.last_update_success_timestamp = "2026-01-01T12:05:00Z"
    return coord


def test_static_sensors(mock_coordinator):
    main_sensor = GlobalEarthquakeSensor(mock_coordinator, "Test Instance")
    update_sensor = EarthquakeLastUpdateSensor(mock_coordinator, "Test Instance")

    assert main_sensor.native_value == 6.5
    assert main_sensor.unique_id == "global_eq_test_instance_main_magnitude"

    attrs = main_sensor.extra_state_attributes
    assert attrs["location"] == "Tokyo, Japan"
    assert attrs["tsunami_warning"] is True
    assert attrs["monitored_events_count"] == 1

    assert update_sensor.native_value == "2026-01-01T12:05:00Z"
    assert update_sensor.entity_category == EntityCategory.DIAGNOSTIC


def test_dynamic_event_sensor(mock_coordinator):
    event_sensor = GlobalEarthquakeEventSensor(mock_coordinator, "Test Instance", "eq1")

    assert event_sensor.native_value == 6.5
    assert event_sensor.name == "6.5M - Tokyo, Japan"
    assert event_sensor.entity_picture == "/global_earthquakes_assets/tsunami.png"

    attrs = event_sensor.extra_state_attributes
    assert attrs["latitude"] == 35.0
    assert attrs["longitude"] == 139.0

    # Test despawning state when data drops off
    mock_coordinator.data = []
    assert event_sensor.name == "Despawning Event..."
    assert event_sensor.native_value is None


@pytest.mark.asyncio
async def test_async_setup_entry_manager(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"instance_name": "Test Instance"},
        options={"map_markers": 1},
        entry_id="test_entry_id",
    )

    coord = MagicMock()
    coord.data = [{"id": "eq1", "magnitude": 5.0}]

    hass.data.setdefault(DOMAIN, {})["test_entry_id"] = coord

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)

    assert async_add_entities.call_count >= 1
    assert coord.async_add_listener.called


async def test_float_map_markers_from_number_selector(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"instance_name": "Test Instance"},
        options={"map_markers": 2.0},
        entry_id="float_entry",
    )
    coord = MagicMock()
    coord.data = [{"id": f"eq{i}", "magnitude": 5.0} for i in range(5)]
    hass.data.setdefault(DOMAIN, {})["float_entry"] = coord
    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)
    dynamic = async_add_entities.call_args_list[-1].args[0]
    assert len(dynamic) == 2
    assert all(isinstance(e, GlobalEarthquakeEventSensor) for e in dynamic)


@pytest.mark.parametrize("data", [None, {"not": "a list"}, []])
async def test_update_entities_non_list_data(hass, data):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"instance_name": "Test Instance"},
        options={"map_markers": 20.0},
        entry_id="nonlist_entry",
    )
    coord = MagicMock()
    coord.data = data
    hass.data.setdefault(DOMAIN, {})["nonlist_entry"] = coord
    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry, async_add_entities)
    # Only the three static sensors; no event sensors and no exception.
    assert async_add_entities.call_count == 1
    assert coord.async_add_listener.called


def test_large_attributes_unrecorded():
    assert "history" in GlobalEarthquakeSensor._unrecorded_attributes
    assert "events" in GlobalEarthquakeHistorySensor._unrecorded_attributes
