import logging
import requests
import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

"""Config flow for the Intelbras sensor integration."""


_LOGGER = logging.getLogger(__name__)

DOMAIN = "hassio-intelbras-3542mfw"


class CannotConnect(Exception):
  """Error to indicate a connection failure."""


class InvalidResponse(Exception):
  """Error to indicate an invalid response from the device."""


async def validate_input(hass: core.HomeAssistant, data: dict) -> dict:
  """Validate the user input by making an HTTP request to the device.

  Data required:
    - host: IP or hostname of the device
    - username: Username for authentication
    - password: Password for authentication

  Returns a dict with a title if successful.
  Raises CannotConnect or InvalidResponse if something goes wrong.
  """
  # Build the URL for the sensor endpoint.
  url = f"http://{data[CONF_HOST]}/cgi-bin/accessControl.cgi?action=getDoorStatus&channel=1"

  # Create the digest auth object.
  auth = requests.auth.HTTPDigestAuth(data[CONF_USERNAME], data[CONF_PASSWORD])

  try:
    # Execute the blocking request in an executor.
    response = await hass.async_add_executor_job(
      lambda: requests.get(url, auth=auth, stream=True, timeout=20, verify=False)
    )
    response.raise_for_status()
  except requests.RequestException as err:
    _LOGGER.error("Error connecting to device at %s: %s", data[CONF_HOST], err)
    raise CannotConnect from err

  # Check the content returned by the device.
  content = response.text.strip()
  if not content.startswith("Info.status="):
    _LOGGER.error("Invalid response from device: %s", content)
    raise InvalidResponse

  return {"title": f"Intelbras {data[CONF_HOST]}"}


class IntelbrasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  """Handle a config flow for the Intelbras sensor integration."""

  VERSION = 1
  CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

  async def async_step_user(self, user_input: dict | None = None):
    """Handle the initial step."""
    if user_input is None:
      schema = vol.Schema({
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
      })
      return self.async_show_form(step_id="user", data_schema=schema)

    errors = {}
    try:
      info = await validate_input(self.hass, user_input)
    except CannotConnect:
      errors["base"] = "cannot_connect"
    except InvalidResponse:
      errors["base"] = "invalid_response"
    except Exception:  # pylint: disable=broad-except
      _LOGGER.exception("Unexpected error")
      errors["base"] = "unknown"

    if errors:
      schema = vol.Schema({
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
      })
      return self.async_show_form(
        step_id="user", data_schema=schema, errors=errors
      )

    await self.async_set_unique_id(user_input[CONF_HOST])
    self._abort_if_unique_id_configured()
    return self.async_create_entry(title=info["title"], data=user_input)