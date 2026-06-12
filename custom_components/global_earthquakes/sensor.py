import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    instance_name = entry.data["instance_name"]

    # Add permanent static sensors including the zero-bloat history feed to work with the new dashboard JS card
    async_add_entities(
        [
            GlobalEarthquakeSensor(coordinator, instance_name),
            EarthquakeLastUpdateSensor(coordinator, instance_name),
            GlobalEarthquakeHistorySensor(coordinator, instance_name),
        ]
    )

    active_entities = {}

    @callback
    def async_update_entities():
        new_entities = []
        current_ids = set()

        if coordinator.data:
            num_markers = entry.options.get(
                "map_markers", entry.data.get("map_markers", 20)
            )
            top_events = coordinator.data[:num_markers]

            for event in top_events:
                eq_id = event["id"]
                current_ids.add(eq_id)

                if eq_id not in active_entities:
                    new_sensor = GlobalEarthquakeEventSensor(
                        coordinator, instance_name, eq_id
                    )
                    active_entities[eq_id] = new_sensor
                    new_entities.append(new_sensor)

        if new_entities:
            async_add_entities(new_entities)

        # CLEANUP: Completely unregisters expired nodes to ensure no grayed-out "Unavailable" entities remain
        obsolete_ids = set(active_entities.keys()) - current_ids
        for eq_id in obsolete_ids:
            entity = active_entities.pop(eq_id)
            entity_id = entity.entity_id

            # Remove from tracking state machine
            hass.async_create_task(entity.async_remove(force_remove=True))

            # Unregister explicitly from registry storage
            if entity_id:
                ent_reg = er.async_get(hass)
                if ent_reg.async_get(entity_id):
                    ent_reg.async_remove(entity_id)

    coordinator.async_add_listener(async_update_entities)
    async_update_entities()


class GlobalBaseEntity(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator)
        self._instance_name = instance_name
        self._device_id = f"global_eq_{instance_name.lower().replace(' ', '_')}"
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"Earthquake Tracker ({self._instance_name})",
            manufacturer="USGS",
            model="Global Seismic Activity Engine",
        )


class GlobalEarthquakeSensor(GlobalBaseEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator, instance_name)
        self._attr_unique_id = f"{self._device_id}_main_magnitude"
        self._attr_icon = "mdi:earthquake"
        self._attr_native_unit_of_measurement = "M"
        self._attr_name = "Latest Magnitude"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return 0.0
        return self.coordinator.data[0].get("magnitude", 0.0)

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}

        latest = self.coordinator.data[0]
        return {
            "location": latest.get("location"),
            "event_type": latest.get("event_type"),
            "tsunami_warning": latest.get("tsunami_warning"),
            "alert_level": latest.get("alert_level"),
            "significance": latest.get("significance"),
            "time": latest.get("time"),
            "depth_km": latest.get("depth_km"),
            "latitude": latest.get("latitude"),
            "longitude": latest.get("longitude"),
            "event_url": latest.get("url"),
            "monitored_events_count": len(self.coordinator.data),
            "history": self.coordinator.data,
        }


class EarthquakeLastUpdateSensor(GlobalBaseEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator, instance_name)
        self._attr_unique_id = f"{self._device_id}_last_sync"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:cloud-sync"
        self._attr_name = "Last Update"

    @property
    def native_value(self):
        return getattr(self.coordinator, "last_update_success_timestamp", None)


class GlobalEarthquakeHistorySensor(GlobalBaseEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator, instance_name)
        self._attr_unique_id = f"{self._device_id}_history_feed"
        self._attr_icon = "mdi:history"
        self._attr_name = "History Feed"
        self._attr_native_unit_of_measurement = "events"

    @property
    def native_value(self):
        return len(getattr(self.coordinator, "history_data", []))

    @property
    def extra_state_attributes(self):
        return {"events": getattr(self.coordinator, "history_data", [])}


class GlobalEarthquakeEventSensor(GlobalBaseEntity):
    def __init__(self, coordinator, instance_name, eq_id):
        super().__init__(coordinator, instance_name)
        self.eq_id = eq_id
        self._attr_unique_id = f"{self._device_id}_{eq_id}"
        self._attr_icon = "mdi:map-marker-alert"

    @property
    def _event_data(self):
        if self.coordinator.data:
            for event in self.coordinator.data:
                if event["id"] == self.eq_id:
                    return event
        return None

    @property
    def name(self):
        data = self._event_data
        if not data:
            return "Despawning Event..."
        return f"{data.get('magnitude')}M - {data.get('location')}"

    @property
    def native_value(self):
        data = self._event_data
        return data.get("magnitude") if data else None

    @property
    def entity_picture(self):
        data = self._event_data
        if not data:
            return None

        event_type = data.get("event_type", "").lower()
        tsunami_warning = data.get("tsunami_warning", False)
        base_url = "/global_earthquakes_assets"

        if tsunami_warning:
            return f"{base_url}/tsunami.png"
        elif "volcano" in event_type or "eruption" in event_type:
            return f"{base_url}/volcano.png"
        elif "earthquake" in event_type or "ice quake" in event_type:
            return f"{base_url}/earthquake.png"
        else:
            return f"{base_url}/default.png"

    @property
    def extra_state_attributes(self):
        data = self._event_data
        if not data:
            return {}

        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "location": data.get("location"),
            "time": data.get("time"),
            "depth_km": data.get("depth_km"),
            "event_type": data.get("event_type"),
        }
