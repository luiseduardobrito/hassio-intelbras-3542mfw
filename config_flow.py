import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from .const import (
    DOMAIN, 
    DEFAULT_HOST, 
    CONF_HOST, 
    CONF_USERNAME, 
    CONF_PASSWORD, 
    CONF_VERIFY_SSL,
    CONF_EVENT_SCAN_INTERVAL,
    DEFAULT_EVENT_SCAN_INTERVAL
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Loading config_flow for %s", __name__)


@config_entries.HANDLERS.register(DOMAIN)
class IntelbrasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Intelbras 3542 MF-W."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # Validate the device connection using the provided host, username, password, and SSL verification.
                await self.hass.async_add_executor_job(
                    fetch_data,
                    user_input[CONF_HOST],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_VERIFY_SSL],
                )
            except Exception as err:
                _LOGGER.error("Error connecting to device at %s: %s",
                              user_input[CONF_HOST], err)
                errors["base"] = "cannot_connect"
            if not errors:
                return self.async_create_entry(title="intelbras_3542_mfw", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=self._get_data_schema(), errors=errors
        )

    def _get_data_schema(self):
        """Return the data schema for the user step."""
        return vol.Schema({
            vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_VERIFY_SSL, default=False): bool,
            vol.Optional(CONF_EVENT_SCAN_INTERVAL, default=DEFAULT_EVENT_SCAN_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
        })


def fetch_data(host, username, password, verify_ssl):
    """
    A simple synchronous function to fetch data from the API using digest authentication.
    It uses HTTP digest authentication by passing the username and password.
    """
    import requests
    from requests.auth import HTTPDigestAuth

    params = {}
    response = requests.get(
        host,
        auth=HTTPDigestAuth(username, password),
        params=params,
        timeout=10,
        verify=verify_ssl
    )
    response.raise_for_status()  # Raises an exception for HTTP errors
    return response.text
