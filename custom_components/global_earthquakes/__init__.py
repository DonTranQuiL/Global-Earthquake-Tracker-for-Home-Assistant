"""The Global Earthquakes integration."""

import logging
import os

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import GlobalEarthquakeCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
ASSETS_URL = "/global_earthquakes_assets"
CARD_FILE = "earthquake-history-card.js"
CARD_VERSION = "1.0.7"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the bundled map icons, the card and the services once."""
    hass.data.setdefault(DOMAIN, {})
    www = os.path.join(os.path.dirname(__file__), "www")
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(ASSETS_URL, www, True)]
        )
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, f"{ASSETS_URL}/{CARD_FILE}?v={CARD_VERSION}")
    except Exception as err:
        _LOGGER.warning("Could not register the Global Earthquakes card: %s", err)

    async def handle_refresh(call: ServiceCall) -> None:
        for coord in list(hass.data.get(DOMAIN, {}).values()):
            await coord.async_request_refresh()

    async def handle_clear_files(call: ServiceCall) -> None:
        for coord in list(hass.data.get(DOMAIN, {}).values()):
            await hass.async_add_executor_job(coord.cache.clear_cache)
            coord.history_data = []  # Drop in-memory history
            if hasattr(coord, "clear_debug_file"):
                await hass.async_add_executor_job(coord.clear_debug_file)

    hass.services.async_register(DOMAIN, "refresh", handle_refresh)
    hass.services.async_register(DOMAIN, "clear_files", handle_clear_files)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one earthquake tracker instance."""
    coordinator = GlobalEarthquakeCoordinator(hass, entry)

    # Load structured cache containing both live and history tracks
    cache_data = await hass.async_add_executor_job(coordinator.cache.load_cache)
    coordinator.last_data = cache_data.get("live", [])
    coordinator.history_data = cache_data.get("history", [])

    if coordinator.last_data:
        # Populate states from cache and schedule the next automatic refresh
        coordinator.async_set_updated_data(coordinator.last_data)
    else:
        await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
