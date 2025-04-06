"""The Intelbras 3542 MFW integration."""

from .const import DOMAIN

async def async_setup(hass, config):
    """Set up the integration from YAML (not used, but required)."""
    return True

async def async_setup_entry(hass, entry):
    """Set up Intelbras 3542 MFW from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Forward the setup to both sensor and camera platforms
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "camera")
    )
    return True

async def async_unload_entry(hass, entry):
    """Unload Intelbras 3542 MFW config entry."""
    unload_sensor = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    unload_camera = await hass.config_entries.async_forward_entry_unload(entry, "camera")
    if unload_sensor and unload_camera:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_sensor and unload_camera
