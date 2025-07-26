"""The Intelbras 3542 MFW integration."""

import json
import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.components.webhook import async_register as async_register_webhook
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL, DEFAULT_HOST
from .client import IntelbrasClient
from .coordinator import IntelbrasEventsCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA, Platform.BUTTON]

# Set up a logger for your custom component
_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_FIRE_TEST_EVENT = "fire_test_event"
SERVICE_FIRE_TEST_EVENT_SCHEMA = vol.Schema({
    vol.Optional("user_id", default="test_user"): cv.string,
    vol.Optional("door", default=1): cv.positive_int,
    vol.Optional("method", default=1): cv.positive_int,
})


async def async_setup(hass, config):
    """Set up the integration from YAML (not used, but required)."""
    webhook_id = "intelbras_3542_mfw_webhook"
    async_register_webhook(
        hass=hass,
        domain=DOMAIN,
        name="Intelbras 3542 MFW Webhook",
        webhook_id=webhook_id,
        handler=handle_webhook_event,
    )
    return True


async def handle_webhook_event(hass: HomeAssistant, webhook_id: str, request):
    """Handle the incoming webhook event."""
    try:
        # Read the raw request body
        raw_data = await request.text()

        _LOGGER.debug(f"Raw webhook data: {raw_data}")

        # print type of raw_data and lenght for debug
        _LOGGER.debug(f"Type of raw_data: {type(raw_data)}")
        _LOGGER.debug(f"Length of raw_data: {len(raw_data)}")

        # Find the JSON data within the 'info' part
        start = raw_data.find('{')  # Find the start of the JSON string
        end = raw_data.rfind('}') + 1  # Find the end of the JSON string
        json_str = raw_data[start:end]  # Extract the JSON substring

        _LOGGER.debug(f"Extracted JSON string: {json_str}")

        # Parse the JSON string
        payload = json.loads(json_str)

        # Log the payload for debugging
        _LOGGER.info(f"Received webhook payload: {json.dumps(payload)}")

        # Fire a custom event with the payload data
        hass.bus.async_fire("intelbras_3542_mfw_webhook", payload)

    except Exception as e:
        # Log any errors that occur during processing
        _LOGGER.error(f"Error processing webhook event: {e}")


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
    
    # Register services
    await _async_register_services(hass, entry)
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("Intelbras 3542 MFW integration successfully set up with events coordinator")
    
    return True


async def _async_register_services(hass: HomeAssistant, entry: ConfigEntry):
    """Register integration services."""
    import time
    
    async def fire_test_event(call: ServiceCall):
        """Service to fire a test event for debugging purposes."""
        coordinator_data = hass.data[DOMAIN][entry.entry_id]
        coordinator = coordinator_data["coordinator"]
        
        # Create a test event
        test_event = {
            "RecNo": 99999,
            "CreateTime": int(time.time()),
            "Door": call.data.get("door", 1),
            "Method": call.data.get("method", 1),
            "UserID": call.data.get("user_id", "test_user"),
            "Status": 1,
            "test_event": True
        }
        
        # Fire the test event
        await coordinator._async_fire_single_event(test_event)
        
        _LOGGER.info(f"Test event fired: {test_event}")
    
    # Register the service
    hass.services.async_register(
        DOMAIN, 
        SERVICE_FIRE_TEST_EVENT, 
        fire_test_event,
        schema=SERVICE_FIRE_TEST_EVENT_SCHEMA
    )


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
