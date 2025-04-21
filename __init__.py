"""The Intelbras 3542 MFW integration."""

import json
from .const import DOMAIN
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.webhook import async_register as async_register_webhook 


PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA, Platform.BUTTON]

async def async_setup(hass, config):
    """Set up the integration from YAML (not used, but required)."""
    webhook_id = "intelbras_3542_mfw_webhook"
    async_register_webhook(
        hass,
        webhook_id,
        handle_webhook_event,
    )
    return True

async def handle_webhook_event(hass: HomeAssistant, webhook_id: str, request):
    """Handle the incoming webhook event."""
    payload = await request.json()
    # Optionally, log the payload for debugging
    hass.logger.info(f"Received webhook payload: {json.dumps(payload)}")
    # Fire a custom event with the payload data
    hass.bus.async_fire("intelbras_3542_mfw_webhook", payload)

async def async_setup_entry(hass, entry):
    """Set up Intelbras 3542 MFW from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
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
