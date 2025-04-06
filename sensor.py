"""Platform for sensor integration."""
from __future__ import annotations

import requests

from homeassistant.components.sensor import (
  SensorDeviceClass,
  SensorEntity,
  SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


def setup_platform(
  hass: HomeAssistant,
  config: ConfigType,
  add_entities: AddEntitiesCallback,
  discovery_info: DiscoveryInfoType | None = None
) -> None:
  """Set up the sensor platform."""
  add_entities([ExampleSensor()])


class ExampleSensor(SensorEntity):
  """Representation of a Sensor that fetches data from a HTTP endpoint with digest auth."""

  _attr_name = "Example Door Status"
  _attr_native_unit_of_measurement = None  # If the returned value is a string, omit a unit.
  _attr_device_class = None
  _attr_state_class = SensorStateClass.MEASUREMENT

  def update(self) -> None:
    """Fetch new state data for the sensor."""
    # Device configuration
    device_ip = '192.168.3.87'
    username = 'admin'
    password = 'acesso1234'
    
    url = f"http://{device_ip}/cgi-bin/accessControl.cgi?action=getDoorStatus&channel=1"
    digest_auth = requests.auth.HTTPDigestAuth(username, password)
    
    try:
      response = requests.get(url, auth=digest_auth, stream=True, timeout=20, verify=False)
      response.raise_for_status()
    except requests.RequestException:
      self._attr_native_value = None
      return
    
    # Expected response: "Info.status=Close" (or similar)
    content = response.text.strip()
    if content.startswith("Info.status="):
      self._attr_native_value = content.split("=", 1)[1]
    else:
      self._attr_native_value = None
