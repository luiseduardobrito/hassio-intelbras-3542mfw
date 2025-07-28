import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the door button entity from a config entry."""
    # Get the client from hass.data
    coordinator_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = coordinator_data["coordinator"]
    client = coordinator_data["client"]
    
    host = entry.data.get(CONF_HOST)
    
    async_add_entities([IntelbrasDoorButton(coordinator, client, host)])


class IntelbrasDoorButton(ButtonEntity):
    """Representation of a door button to open the door via the device API."""

    def __init__(self, coordinator, client, host):
        """Initialize the door button."""
        self._client = client
        self._host = host
        self._coordinator = coordinator
        self._channel = 1  # For devices with a single door, channel is always 1.

        self._attr_name = "Open Door"
        self._attr_unique_id = f"{host}_door_button"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            name="Intelbras 3542 MFW Door Controller",
            manufacturer="Intelbras",
            model="3542 MFW",
            configuration_url=host,
        )

    async def async_press(self) -> None:
        """Handle the button press to open the door."""
        _LOGGER.debug("Opening door via button press")
        try:
            # Use the async client method directly
            response = await self._client.open_door(self._channel)
            _LOGGER.info("Door opened successfully: %s", response)

            # Refresh the coordinator data
            await self._coordinator.async_refresh()
        except Exception as exc:
            _LOGGER.error("Error opening door: %s", exc)
            raise
