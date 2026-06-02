import json
import os
import logging

_LOGGER = logging.getLogger(__name__)

class GlobalEarthquakeCache:
    def __init__(self, hass, instance_name):
        self.hass = hass
        current_dir = os.path.dirname(__file__)
        safe_name = (
            "".join(x for x in instance_name if x.isalnum() or x in " _-")
            .strip()
            .replace(" ", "_")
            .lower()
        )
        self.cache_path = os.path.join(current_dir, f".global_earthquakes_{safe_name}.json")

    def load_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                _LOGGER.error("Error loading cache: %s", e)
        return []

    def save_cache(self, data):
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            _LOGGER.error("Error saving cache: %s", e)

    def clear_cache(self):
        if os.path.exists(self.cache_path):
            try:
                os.remove(self.cache_path)
            except Exception as e:
                _LOGGER.error("Error deleting cache: %s", e)