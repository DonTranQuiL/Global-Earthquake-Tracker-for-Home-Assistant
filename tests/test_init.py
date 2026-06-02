import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.global_earthquakes.const import DOMAIN, PLATFORMS
from custom_components.global_earthquakes import async_setup_entry, async_unload_entry, update_listener

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield

@pytest.fixture
def mock_coordinator_deps():
    # FIX: Patch directly in the coordinator where the cache is loaded
    with patch("custom_components.global_earthquakes.coordinator.GlobalEarthquakeCache") as mock_cache_cls, \
         patch("custom_components.global_earthquakes.GlobalEarthquakeCoordinator") as mock_coord_cls:
        
        mock_cache = MagicMock()
        mock_cache.load_cache = MagicMock(return_value=[])
        mock_cache.clear_cache = MagicMock()
        mock_cache_cls.return_value = mock_cache

        mock_coord = MagicMock()
        mock_coord.last_data = []
        mock_coord.cache = mock_cache
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord.async_request_refresh = AsyncMock()
        mock_coord_cls.return_value = mock_coord
        
        yield mock_cache, mock_coord

@pytest.mark.asyncio
async def test_setup_entry_no_cache(hass: HomeAssistant, mock_coordinator_deps):
    mock_cache, mock_coord = mock_coordinator_deps
    entry = MockConfigEntry(domain=DOMAIN, data={"instance_name": "Test"})
    entry.add_to_hass(hass)

    hass.http = AsyncMock()
    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=True), \
         patch("os.path.exists", return_value=True):
        assert await async_setup_entry(hass, entry) is True
        mock_coord.async_config_entry_first_refresh.assert_called_once()
        hass.http.async_register_static_paths.assert_called_once()

@pytest.mark.asyncio
async def test_setup_entry_with_cache(hass: HomeAssistant, mock_coordinator_deps):
    mock_cache, mock_coord = mock_coordinator_deps
    mock_cache.load_cache.return_value = [{"id": "eq1", "magnitude": 5.0}]
    mock_coord.last_data = mock_cache.load_cache.return_value

    entry = MockConfigEntry(domain=DOMAIN, data={"instance_name": "Test"})
    entry.add_to_hass(hass)

    hass.http = AsyncMock()
    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=True):
        assert await async_setup_entry(hass, entry) is True
        mock_coord.async_config_entry_first_refresh.assert_not_called()

@pytest.mark.asyncio
async def test_unload_and_services(hass: HomeAssistant, mock_coordinator_deps):
    mock_cache, mock_coord = mock_coordinator_deps
    entry = MockConfigEntry(domain=DOMAIN, data={"instance_name": "Test"})
    entry.add_to_hass(hass)
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = mock_coord
    hass.http = AsyncMock()

    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=True):
        await async_setup_entry(hass, entry)

    await hass.services.async_call(DOMAIN, "refresh", blocking=True)
    mock_coord.async_request_refresh.assert_called_once()

    await hass.services.async_call(DOMAIN, "clear_files", blocking=True)
    mock_cache.clear_cache.assert_called_once()

    with patch("homeassistant.config_entries.ConfigEntries.async_reload") as mock_reload:
        await update_listener(hass, entry)
        mock_reload.assert_called_once_with(entry.entry_id)

    with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms", return_value=True) as mock_unload:
        assert await async_unload_entry(hass, entry) is True
        mock_unload.assert_called_once_with(entry, PLATFORMS)
        assert entry.entry_id not in hass.data[DOMAIN]