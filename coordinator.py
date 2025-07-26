from datetime import timedelta
import logging
import time

import async_timeout

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class IntelbrasEventsCoordinator(DataUpdateCoordinator):
    """Coordinator for Intelbras events."""

    def __init__(self, hass, config_entry, client):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Intelbras events",
            config_entry=config_entry,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True
        )
        self.client = client

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        # Listen for events from now on
        self.last_updated = int(time.time())

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                events = self.client.get_events(self.last_updated, int(time.time()))
                self.last_updated = int(time.time())
                return events
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
