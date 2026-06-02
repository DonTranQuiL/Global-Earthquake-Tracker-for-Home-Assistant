DOMAIN = "global_earthquakes"

# Changed to the 7-Day feed so we have enough data to fill the map!
URL_USGS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"

CONF_INSTANCE_NAME = "instance_name"
CONF_MONITORED_COUNTRIES = "monitored_countries"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MIN_MAG_USA = "min_mag_usa"
CONF_MIN_MAG_GLOBAL = "min_mag_global"
CONF_MAP_MARKERS = "map_markers"

DEFAULT_SCAN_INTERVAL = 300
DEFAULT_MIN_MAG_USA = 2.5
DEFAULT_MIN_MAG_GLOBAL = 4.5
DEFAULT_MAP_MARKERS = 20

PLATFORMS = ["sensor"]
