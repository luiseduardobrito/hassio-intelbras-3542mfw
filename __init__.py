"""The Intelbras 3542 MFW integration."""

import json
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.webhook import async_register as async_register_webhook

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL, DEFAULT_HOST
from .client import IntelbrasClient
from .coordinator import IntelbrasEventsCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA, Platform.BUTTON]

# Set up a logger for your custom component
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Intelbras 3542 MFW from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration from the config entry
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, False)

    # Create the client instance
    client = IntelbrasClient(host, username, password, verify_ssl)

    # Create and setup the events coordinator
    coordinator = IntelbrasEventsCoordinator(hass, entry, client)

    # Perform the initial refresh to set up the coordinator
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data for access by platforms
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "Intelbras 3542 MFW integration successfully set up with events coordinator")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Intelbras 3542 MFW config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_migrate_entry(hass, entry):
    """Migrate config entry to a new version."""
    # Example migration logic
    # if entry.version == 1:
    #     entry.data["new_key"] = "new_value"
    #     entry.version = 2
    #     hass.config_entries.async_update_entry(entry)
    # return True
    return True
