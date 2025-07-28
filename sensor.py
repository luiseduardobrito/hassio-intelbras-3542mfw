import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST, DEFAULT_HOST

_LOGGER = logging.getLogger(__name__)

ENTRY_METHOD_LABELS = {
    4: "remote",
    5: "button",
}


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
        IntelbrasLastEventSensor(coordinator, host),
        IntelbrasDoorEntryMethodSensor(coordinator, host)
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
        """Return the door status."""
        # This state is a little tricky, we need to get the door status from the coordinator
        # first we check if the door status is in the coordinator data is open
        # if it is, we return open
        # if it is not, we check if we have an event Type = Entry in the last update
        # if we have an event Type = Entry in the last update, we return open
        # else we return closed
        door_status = self.coordinator.get_door_status()

        # Fast return if the door status is open
        if door_status == "open":
            return "open"

        # If the door status is not open, we check if we have an event Type = Entry in the last update
        # as the door status can be changed too fast for the coordinator to detect it,
        # so we get events in defined intervals, if a door was opened and closed in the last interval we set it manually as open.
        events = self.coordinator.get_latest_events()

        if events:
            for event in events:
                if event["Type"] == "Entry" and event["ErrorCode"] == 0:
                    return "open"

        # If no status and no events in last update, we return closed
        return "closed"


class IntelbrasDoorEntryMethodSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Intelbras door entry method sensor."""

    def __init__(self, coordinator, host):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Door Entry Method"
        self._attr_unique_id = f"{host}_door_entry_method"
        self._attr_icon = "mdi:lock-open-alert"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": "Intelbras 3542 MFW",
            "manufacturer": "Intelbras",
            "model": "3542 MFW",
            "configuration_url": host,
        }

    @property
    def state(self):
        """Return the door entry method."""
        events = self.coordinator.get_latest_events()
        if events:
            for event in events:
                # We only show the entry method if the event is an entry and the error code is 0
                if event["Type"] == "Entry" and event["ErrorCode"] == 0:
                    return ENTRY_METHOD_LABELS.get(event["Method"], "unknown")
        return "unknown"


class IntelbrasLastEventSensor(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Sensor showing details of the most recent event."""

    def __init__(self, coordinator, host):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Last Event"
        self._attr_unique_id = f"{host}_last_event"
        self._attr_icon = "mdi:history"
        self._last_known_state = None  # Store the last known state
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": "Intelbras 3542 MFW",
            "manufacturer": "Intelbras",
            "model": "3542 MFW",
            "configuration_url": host,
        }

    async def async_added_to_hass(self) -> None:
        """Restore last state after restart."""
        await super().async_added_to_hass()

        # Restore the previous timestamp state if available
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state != "unknown":
            self._last_known_state = last_state.state
            _LOGGER.debug(
                f"Restored last known state: {self._last_known_state}")

    @property
    def state(self):
        """Return the timestamp of the last event."""
        events = self.coordinator.get_latest_events()
        if events:
            # Return the CreateTime of the most recent event
            last_event = events[-1]
            new_state = last_event.get("CreateTime", "Unknown")
            # Update our stored state
            self._last_known_state = new_state
            return new_state

        # Return the last known state if no new events are available
        return self._last_known_state
