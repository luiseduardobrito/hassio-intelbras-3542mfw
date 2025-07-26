import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL
from .client import IntelbrasClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the door button entity from a config entry."""
    async_add_entities([IntelbrasDoorButton(entry.data)])


class IntelbrasDoorButton(ButtonEntity):
    """Representation of a door button to open the door via the device API."""

    def __init__(self, config_data):
        """Initialize the door button."""
        self._config = config_data
        host = config_data.get(CONF_HOST)
        username = config_data.get(CONF_USERNAME)
        password = config_data.get(CONF_PASSWORD)
        verify_ssl = config_data.get(CONF_VERIFY_SSL, False)
        self._channel = 1  # For devices with a single door, channel is always 1.

        # Initialize the client
        self._client = IntelbrasClient(host, username, password, verify_ssl)

        self._attr_name = "Open Door"
        self._attr_unique_id = f"{host}_door_button"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            name="Intelbras 3542 MFW Door Controller",
            manufacturer="Intelbras",
            configuration_url=host,
        )

    async def async_press(self) -> None:
        """Handle the button press to open the door."""
        _LOGGER.debug("Opening door via button press")
        try:
            # Run the HTTP request in an executor
            await self.hass.async_add_executor_job(
                self._client.open_door, self._channel
            )
        except Exception as exc:
            _LOGGER.error("Error opening door: %s", exc)
