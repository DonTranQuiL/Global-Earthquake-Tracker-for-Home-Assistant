import logging
from datetime import timedelta, datetime, timezone
import asyncio

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, 
    URL_USGS, 
    CONF_MONITORED_COUNTRIES, 
    CONF_MIN_MAG_USA, 
    CONF_MIN_MAG_GLOBAL
)
from .cache import GlobalEarthquakeCache

_LOGGER = logging.getLogger(__name__)

# Full list of European nations for the 'EUROPE' macro selection
EUROPEAN_COUNTRIES = [
    "Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bosnia and Herzegovina", 
    "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia", "Finland", 
    "France", "Germany", "Gibraltar", "Greece", "Hungary", "Ireland", "Iceland", 
    "Italy", "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta", 
    "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia", "Norway", 
    "Poland", "Portugal", "Romania", "San Marino", "Serbia", "Slovakia", "Slovenia", 
    "Spain", "Sweden", "Switzerland", "Turkey", "Ukraine", "United Kingdom", "Vatican"
]


class GlobalEarthquakeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        self.hass = hass
        self.instance_name = config_entry.data["instance_name"]
        
        # Read user configurations for Dual Thresholds & Countries
        self.min_mag_usa = config_entry.options.get(CONF_MIN_MAG_USA, config_entry.data.get(CONF_MIN_MAG_USA, 2.5))
        self.min_mag_global = config_entry.options.get(CONF_MIN_MAG_GLOBAL, config_entry.data.get(CONF_MIN_MAG_GLOBAL, 4.5))
        self.monitored_countries = config_entry.options.get(CONF_MONITORED_COUNTRIES, config_entry.data.get(CONF_MONITORED_COUNTRIES, ["ALL"]))
        
        self.cache = GlobalEarthquakeCache(hass, self.instance_name)
        self.last_data = []
        self.error_count = 0
        self.last_update_success_timestamp = None

        scan_interval = config_entry.options.get("scan_interval", config_entry.data.get("scan_interval", 300))
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan_interval)
        )

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        
        try:
            async with session.get(URL_USGS) as response:
                if response.status != 200:
                    _LOGGER.error("USGS API returned status code %s", response.status)
                    return self.last_data

                feed_data = await response.json()
                events = []

                for feature in feed_data.get("features", []):
                    props = feature.get("properties", {})
                    geometry = feature.get("geometry", {})
                    coordinates = geometry.get("coordinates", [0, 0, 0]) # [lon, lat, depth]

                    magnitude = props.get("mag")
                    if magnitude is None:
                        continue

                    place_str = props.get("place", "Unknown Location")
                    
                    # 1. SMART MAGNITUDE FILTERING (USA vs Global)
                    is_usa_quake = any(state in place_str for state in [", CA", ", Alaska", ", Hawaii", ", NV", ", TX", "United States", ", WA", ", OR"])
                    
                    if is_usa_quake and magnitude < self.min_mag_usa:
                        continue
                    elif not is_usa_quake and magnitude < self.min_mag_global:
                        continue

                    # 2. ADVANCED COUNTRY MATCHING
                    is_matched = "ALL" in self.monitored_countries
                    if not is_matched:
                        for country in self.monitored_countries:
                            # Match if user selected the full Europe group
                            if country == "EUROPE":
                                if any(euro_country.lower() in place_str.lower() for euro_country in EUROPEAN_COUNTRIES):
                                    is_matched = True
                                    break
                            
                            # Match if user selected USA specifically
                            elif country == "USA" and is_usa_quake:
                                is_matched = True
                                break
                            
                            # Match specific countries
                            elif country.lower() in place_str.lower():
                                is_matched = True
                                break

                    # If the earthquake doesn't match the selected regions, skip it
                    if not is_matched:
                        continue

                    # 3. BUILD THE EVENT OBJECT
                    epoch_time = props.get("time", 0) / 1000.0
                    dt = datetime.fromtimestamp(epoch_time, tz=timezone.utc)
                    time_str = dt.strftime("%d-%m-%Y %H:%M:%S UTC")

                    # Event Type (e.g., Earthquake, Quarry blast)
                    raw_type = props.get("type", "unknown")
                    event_type = raw_type.capitalize()
                    
                    # Tsunami flag (1 = Warning Issued, 0 = No Warning)
                    tsunami_flag = props.get("tsunami", 0)
                    tsunami_warning = True if tsunami_flag == 1 else False

                    # Alert Level (Green, Yellow, Orange, Red) - Handle nulls safely
                    raw_alert = props.get("alert")
                    alert_level = raw_alert.capitalize() if raw_alert else "None"

                    # Significance Score
                    sig_score = props.get("sig", 0)

                    events.append({
                        "id": feature.get("id"),
                        "location": place_str,
                        "magnitude": round(float(magnitude), 1),
                        "time": time_str,
                        "depth_km": round(float(coordinates[2]), 1) if len(coordinates) > 2 else 0.0,
                        "latitude": coordinates[1],
                        "longitude": coordinates[0],
                        "event_type": event_type,
                        "tsunami_warning": tsunami_warning,
                        "alert_level": alert_level,
                        "significance": sig_score,
                        "url": props.get("url")
                    })

                # Sort events so the strongest earthquake is always index 0
                events.sort(key=lambda x: x["magnitude"], reverse=True)

                self.last_data = events
                await self.hass.async_add_executor_job(self.cache.save_cache, events)
                self.error_count = 0
                self.last_update_success_timestamp = dt_util.utcnow()
                
                return self.last_data

        except Exception as err:
            self.error_count += 1
            _LOGGER.error("Error updating global earthquake data: %s", err)
            return self.last_data