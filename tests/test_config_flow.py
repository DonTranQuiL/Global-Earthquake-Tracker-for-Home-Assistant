import pytest
from unittest.mock import patch
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.global_earthquakes.const import (
    DOMAIN,
    CONF_INSTANCE_NAME,
    CONF_MONITORED_COUNTRIES,
    CONF_SCAN_INTERVAL,
    CONF_MIN_MAG_USA,
    CONF_MIN_MAG_GLOBAL,
    CONF_MAP_MARKERS,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom components during testing."""
    yield


@pytest.mark.asyncio
async def test_form_user_success(hass):
    """Test we can create an entry through the user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.global_earthquakes.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INSTANCE_NAME: "World Quakes",
                CONF_MIN_MAG_USA: 3.0,
                CONF_MIN_MAG_GLOBAL: 5.0,
                CONF_MONITORED_COUNTRIES: ["ALL"],
                CONF_MAP_MARKERS: 10,
                CONF_SCAN_INTERVAL: 600,
            },
        )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Earthquakes (World Quakes)"
    assert result2["data"][CONF_INSTANCE_NAME] == "World Quakes"
    assert result2["data"][CONF_MIN_MAG_USA] == 3.0
    assert result2["data"][CONF_MIN_MAG_GLOBAL] == 5.0
    assert result2["data"][CONF_MONITORED_COUNTRIES] == ["ALL"]
    assert result2["data"][CONF_MAP_MARKERS] == 10
    assert result2["data"][CONF_SCAN_INTERVAL] == 600


@pytest.mark.asyncio
async def test_options_flow(hass):
    """Test options flow to update thresholds and regions dynamically."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_INSTANCE_NAME: "Global",
            CONF_MIN_MAG_USA: 2.5,
            CONF_MIN_MAG_GLOBAL: 4.5,
            CONF_MAP_MARKERS: 20,
        },
        options={CONF_SCAN_INTERVAL: 300},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MIN_MAG_USA: 4.0,
            CONF_MIN_MAG_GLOBAL: 6.0,
            CONF_MONITORED_COUNTRIES: ["USA", "Japan"],
            CONF_MAP_MARKERS: 5,
            CONF_SCAN_INTERVAL: 1200,
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_MIN_MAG_USA] == 4.0
    assert result2["data"][CONF_MONITORED_COUNTRIES] == ["USA", "Japan"]
    assert result2["data"][CONF_MAP_MARKERS] == 5
