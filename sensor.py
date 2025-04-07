import logging
from requests.auth import HTTPDigestAuth
import requests

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the door button entity from a config entry."""
    async_add_entities([IntelbrasDoorButton(hass, entry.data)])


class IntelbrasDoorButton(ButtonEntity):
    """Representation of a door button to open the door via the device API."""

    def __init__(self, hass, config_data):
        """Initialize the door button."""
        self.hass = hass
        self._config = config_data
        host = config_data.get(CONF_HOST)
        self._username = config_data.get(CONF_USERNAME)
        self._password = config_data.get(CONF_PASSWORD)
        self._verify_ssl = config_data.get(CONF_VERIFY_SSL, False)
        self._channel = 1  # For devices with a single door, channel is always 1.

        self._attr_name = "Open Door"
        self._attr_unique_id = f"{host}_door_button"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            name="Intelbras 3542 MFW Door Controller",
            manufacturer="Intelbras",
        )

    async def async_press(self) -> None:
        """Handle the button press to open the door."""
        # Use the host as provided (which should include the scheme)
        host = self._config.get(CONF_HOST)
        url = f"{host}/cgi-bin/accessControl.cgi?action=openDoor&channel={self._channel}"
        _LOGGER.debug("Sending door open command to %s", url)
        try:
            # Run the synchronous HTTP request in an executor to avoid blocking.
            await self.hass.async_add_executor_job(
                self._send_request, url, self._username, self._password, self._verify_ssl
            )
        except Exception as exc:
            _LOGGER.error("Error opening door: %s", exc)

    def _send_request(self, url: str, username: str, password: str, verify_ssl: bool):
        """Send the HTTP request to open the door."""
        digest_auth = HTTPDigestAuth(username, password)
        response = requests.get(url, auth=digest_auth, stream=True, timeout=20, verify=verify_ssl)
        response.raise_for_status()
        _LOGGER.info("Door open response: %s", response.text)
