import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL, DEFAULT_HOST
from .client import IntelbrasClient

_LOGGER = logging.getLogger(__name__)

# Define how often to poll the device
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, False)

    # Create the client instance
    client = IntelbrasClient(host, username, password, verify_ssl)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Intelbras Door Status",
        update_method=lambda: hass.async_add_executor_job(
            client.get_door_status, 1
        ),
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data before adding entities.
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([IntelbrasDoorStatusSensor(coordinator, host)], True)


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
            "configuration_url": host,
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        # The coordinator.data contains the door status string returned by the API.
        return self.coordinator.data
