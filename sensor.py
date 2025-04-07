import logging
from datetime import timedelta

import requests
from requests.auth import HTTPDigestAuth
import urllib3

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, DEFAULT_HOST

_LOGGER = logging.getLogger(__name__)

# Disable warnings for insecure SSL requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define how often to poll the device
SCAN_INTERVAL = timedelta(seconds=60)


def fetch_door_status(host, username, password):
    """Fetch door status from the Intelbras device using HTTP Digest Authentication."""
    url = f"{host}/cgi-bin/accessControl.cgi?action=getDoorStatus&channel=1"
    try:
        session = requests.Session()
        session.verify = False  # Disable SSL certificate verification globally for this session
        response = session.get(
            url,
            auth=HTTPDigestAuth(username, password),
            stream=True,
            timeout=20,
        )
        response.raise_for_status()
        text = response.text.strip()
        if '=' in text:
            return text.split('=', 1)[1].strip().lower()
        return text
    except Exception as err:
        _LOGGER.error("Error fetching door status from %s: %s", host, err)
        raise


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Intelbras Door Status",
        update_method=lambda: hass.async_add_executor_job(
            fetch_door_status, host, username, password
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
