import logging
import os
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.http import (
    StaticPathConfig,
)  # <--- NEW IMPORT FOR HA 2024+
from .const import DOMAIN, PLATFORMS
from .coordinator import GlobalEarthquakeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # --- NEW: REGISTER LOCAL IMAGES FOLDER (UPDATED FOR MODERN HA) ---
    local_media_path = hass.config.path(f"custom_components/{DOMAIN}/www")
    if os.path.exists(local_media_path):
        # Using the new async method required by newer Home Assistant versions
        await hass.http.async_register_static_paths(
            [StaticPathConfig("/global_earthquakes_assets", local_media_path, True)]
        )
    else:
        _LOGGER.warning(
            "The 'www' folder does not exist at %s. Custom map pins will not load.",
            local_media_path,
        )
    # -----------------------------------------

    coordinator = GlobalEarthquakeCoordinator(hass, entry)
    coordinator.last_data = await hass.async_add_executor_job(
        coordinator.cache.load_cache
    )

    if coordinator.last_data:
        coordinator.data = coordinator.last_data
        entry.async_create_background_task(
            hass, coordinator.async_request_refresh(), "global_eq_bg_refresh"
        )
    else:
        await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def handle_refresh(call: ServiceCall):
        for coord in hass.data[DOMAIN].values():
            await coord.async_request_refresh()

    async def handle_clear_files(call: ServiceCall):
        for coord in hass.data[DOMAIN].values():
            await hass.async_add_executor_job(coord.cache.clear_cache)
            if hasattr(coord, "clear_debug_file"):
                await hass.async_add_executor_job(coord.clear_debug_file)

    hass.services.async_register(DOMAIN, "refresh", handle_refresh)
    hass.services.async_register(DOMAIN, "clear_files", handle_clear_files)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
