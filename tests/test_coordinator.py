import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.global_earthquakes.const import DOMAIN
from custom_components.global_earthquakes.coordinator import GlobalEarthquakeCoordinator

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield

@pytest.fixture
def mock_cache():
    cache = MagicMock()
    cache.save_cache = MagicMock()
    return cache

def _get_mock_feed(features):
    return {"features": features}

@pytest.mark.asyncio
@patch("custom_components.global_earthquakes.coordinator.async_get_clientsession")
@patch("custom_components.global_earthquakes.coordinator.GlobalEarthquakeCache")
async def test_coordinator_successful_refresh(mock_cache_cls, mock_get_session, hass: HomeAssistant, mock_cache):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"instance_name": "Test"},
        options={
            "min_mag_usa": 2.5,
            "min_mag_global": 4.5,
            "monitored_countries": ["ALL"],
            "scan_interval": 300
        }
    )
    mock_cache_cls.return_value = mock_cache
    coord = GlobalEarthquakeCoordinator(hass, entry)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = _get_mock_feed([
        {
            "id": "eq1",
            "properties": {
                "mag": 5.5,
                "place": "10km W of Tokyo, Japan",
                "time": 1600000000000,
                "type": "earthquake",
                "tsunami": 1,
                "alert": "yellow",
                "sig": 100
            },
            "geometry": {
                "coordinates": [139.69, 35.68, 20.0]
            }
        }
    ])
    
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_resp
    mock_get_session.return_value = mock_session

    result = await coord._async_update_data()
    assert len(result) == 1
    assert result[0]["magnitude"] == 5.5
    assert result[0]["tsunami_warning"] is True
    assert result[0]["location"] == "10km W of Tokyo, Japan"
    assert result[0]["depth_km"] == 20.0
    mock_cache.save_cache.assert_called_once()

@pytest.mark.asyncio
@patch("custom_components.global_earthquakes.coordinator.async_get_clientsession")
@patch("custom_components.global_earthquakes.coordinator.GlobalEarthquakeCache")
async def test_coordinator_filtering_logic(mock_cache_cls, mock_get_session, hass: HomeAssistant, mock_cache):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"instance_name": "Test"},
        options={
            "min_mag_usa": 3.0,
            "min_mag_global": 5.0,
            "monitored_countries": ["USA", "EUROPE"],
        }
    )
    mock_cache_cls.return_value = mock_cache
    coord = GlobalEarthquakeCoordinator(hass, entry)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = _get_mock_feed([
        # USA eq under threshold (2.9 < 3.0) -> skip
        {"id": "eq_usa_small", "properties": {"mag": 2.9, "place": "San Francisco, CA", "time": 0}, "geometry": {"coordinates": [0,0,0]}},
        # USA eq over threshold -> keep (Notice we added ", CA" so it maps as USA)
        {"id": "eq_usa_big", "properties": {"mag": 3.5, "place": "Los Angeles, CA", "time": 0}, "geometry": {"coordinates": [0,0,0]}},
        # Global eq under threshold (4.9 < 5.0) -> skip
        {"id": "eq_global_small", "properties": {"mag": 4.9, "place": "Italy", "time": 0}, "geometry": {"coordinates": [0,0,0]}},
        # Global eq over threshold and in EUROPE -> keep
        {"id": "eq_europe_big", "properties": {"mag": 5.5, "place": "Rome, Italy", "time": 0}, "geometry": {"coordinates": [0,0,0]}},
        # Global eq over threshold but not in monitored countries (e.g. Japan) -> skip
        {"id": "eq_japan", "properties": {"mag": 6.0, "place": "Japan", "time": 0}, "geometry": {"coordinates": [0,0,0]}},
    ])
    
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_resp
    mock_get_session.return_value = mock_session

    result = await coord._async_update_data()
    assert len(result) == 2
    ids = [r["id"] for r in result]
    assert "eq_europe_big" in ids
    assert "eq_usa_big" in ids

@pytest.mark.asyncio
@patch("custom_components.global_earthquakes.coordinator.async_get_clientsession")
@patch("custom_components.global_earthquakes.coordinator.GlobalEarthquakeCache")
async def test_coordinator_exception_handling(mock_cache_cls, mock_get_session, hass: HomeAssistant, mock_cache):
    entry = MockConfigEntry(domain=DOMAIN, data={"instance_name": "Test"})
    mock_cache_cls.return_value = mock_cache
    coord = GlobalEarthquakeCoordinator(hass, entry)
    coord.last_data = []

    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Connection Error")
    mock_get_session.return_value = mock_session
    
    result = await coord._async_update_data()
    assert coord.error_count == 1
    assert result == []