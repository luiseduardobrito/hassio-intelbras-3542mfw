"""Platform for Intelbras sensor integration."""
from __future__ import annotations

import logging
import requests

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
  hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
  """Set up the Intelbras sensor from a config entry."""
  async_add_entities([IntelbrasSensor(hass, entry)])


class IntelbrasSensor(SensorEntity):
  """Representation of a sensor that fetches data from the device using configuration entry info."""

  _attr_name = "Intelbras Door Status"
  _attr_native_unit_of_measurement = None  # No unit since the device returns a string.
  _attr_device_class = None
  _attr_state_class = SensorStateClass.MEASUREMENT

  def __init__(self, hass: HomeAssistant, entry) -> None:
    """Initialize the Intelbras sensor."""
    self.hass = hass
    self._host: str = entry.data[CONF_HOST]
    self._username: str = entry.data[CONF_USERNAME]
    self._password: str = entry.data[CONF_PASSWORD]
    self._attr_native_value = None

  async def async_update(self) -> None:
    """Fetch new state data for the sensor."""
    url = f"http://{self._host}/cgi-bin/accessControl.cgi?action=getDoorStatus&channel=1"
    digest_auth = requests.auth.HTTPDigestAuth(self._username, self._password)

    def get_status() -> str | None:
      try:
        response = requests.get(
          url, auth=digest_auth, stream=True, timeout=20, verify=False
        )
        response.raise_for_status()
        return response.text.strip()
      except requests.RequestException as exc:
        _LOGGER.error("Error fetching data from %s: %s", self._host, exc)
        return None

    content = await self.hass.async_add_executor_job(get_status)

    if content and content.startswith("Info.status="):
      self._attr_native_value = content.split("=", 1)[1]
    else:
      self._attr_native_value = None
