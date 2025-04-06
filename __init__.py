"""The Intelbras 3542 MFW integration."""

from .const import DOMAIN

async def async_setup(_hass, _config):
    """Set up the integration from YAML (not used, but required)."""
    return True

async def async_setup_entry(hass, entry):
    """Set up Intelbras 3542 MFW from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Forward the setup to both sensor and camera platforms using the new API
    result = await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "camera"])
    return result

async def async_unload_entry(hass, entry):
    """Unload Intelbras 3542 MFW config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "camera"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
