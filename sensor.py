import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST, DEFAULT_HOST

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform from a config entry."""
    # Get the coordinator from hass.data
    coordinator_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = coordinator_data["coordinator"]

    host = entry.data.get(CONF_HOST, DEFAULT_HOST)

    # Create sensor entities using the coordinator
    entities = [
        IntelbrasDoorStatusSensor(coordinator, host),
        IntelbrasEventsCountSensor(coordinator, host),
        IntelbrasLastEventSensor(coordinator, host)
    ]

    async_add_entities(entities, True)


class IntelbrasDoorStatusSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Intelbras door status sensor."""

    def __init__(self, coordinator, host):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Door Status"
        self._attr_unique_id = f"{host}_door_status"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": "Intelbras 3542 MFW",
            "manufacturer": "Intelbras",
            "model": "3542 MFW",
            "configuration_url": host,
        }

    @property
    def state(self):
        """Return the number of events."""
        # We we have an event Type = Entry in the last update, we set it to open
        # Else we set it to closed
        events = self.coordinator.get_latest_events()
        if events:
            for event in events:
                # TODO: This is just a placeholder, we need to get the door status from the device
                if event["Type"] == "Entry":
                    return "Open"
        return "Closed"


class IntelbrasEventsCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the count of events from the coordinator."""

    def __init__(self, coordinator, host):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Events Count"
        self._attr_unique_id = f"{host}_events_count"
        self._attr_icon = "mdi:counter"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": "Intelbras 3542 MFW",
            "manufacturer": "Intelbras",
            "model": "3542 MFW",
            "configuration_url": host,
        }

    @property
    def state(self):
        """Return the number of events."""
        return self.coordinator.get_event_count()

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return {
            "last_updated": self.coordinator.data.get("last_updated") if self.coordinator.data else None,
            "total_events": self.coordinator.get_event_count()
        }


class IntelbrasLastEventSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing details of the most recent event."""

    def __init__(self, coordinator, host):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Last Event"
        self._attr_unique_id = f"{host}_last_event"
        self._attr_icon = "mdi:history"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": "Intelbras 3542 MFW",
            "manufacturer": "Intelbras",
            "model": "3542 MFW",
            "configuration_url": host,
        }

    @property
    def state(self):
        """Return the timestamp of the last event."""
        events = self.coordinator.get_latest_events()
        if events:
            # Return the CreateTime of the most recent event
            last_event = events[-1]
            return last_event.get("CreateTime", "Unknown")
        return "No events"

    @property
    def extra_state_attributes(self):
        """Return the full details of the last event."""
        events = self.coordinator.get_latest_events()
        if events:
            last_event = events[-1]
            # Return all event data as attributes for easy access
            return {
                "event_data": last_event,
                "door": last_event.get("Door"),
                "method": last_event.get("Method"),
                "user_id": last_event.get("UserID"),
                "status": last_event.get("Status"),
                "total_events": len(events)
            }
        return {
            "event_data": None,
            "total_events": 0
        }
