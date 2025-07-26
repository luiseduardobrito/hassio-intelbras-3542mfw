from datetime import timedelta
import logging
import time
from typing import List, Dict, Any

import async_timeout

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .event_parser import IntelbrasEventParser

_LOGGER = logging.getLogger(__name__)

class IntelbrasEventsCoordinator(DataUpdateCoordinator):
    """Coordinator for Intelbras events."""

    def __init__(self, hass: HomeAssistant, config_entry, client):
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
        self.config_entry = config_entry
        self.event_parser = IntelbrasEventParser(strict_mode=False)
        self.last_events: List[Dict[str, Any]] = []
        self.device_id = None

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        # Initialize last updated timestamp
        self.last_updated = int(time.time())
        
        # Get or create device for event attribution
        await self._async_get_or_create_device()
        
        _LOGGER.debug("Events coordinator initialized with device_id: %s", self.device_id)

    async def _async_get_or_create_device(self):
        """Get or create the device entry for event attribution."""
        device_registry = dr.async_get(self.hass)
        host = self.config_entry.data.get("host", "unknown")
        
        # Create device identifier
        device_identifier = (DOMAIN, host)
        
        # Try to find existing device
        device_entry = device_registry.async_get_device(
            identifiers={device_identifier}
        )
        
        if device_entry:
            self.device_id = device_entry.id
            _LOGGER.debug("Found existing device: %s", self.device_id)
        else:
            # Create new device entry
            device_entry = device_registry.async_get_or_create(
                config_entry_id=self.config_entry.entry_id,
                identifiers={device_identifier},
                manufacturer="Intelbras",
                model="3542 MFW",
                name="Intelbras 3542 MFW",
                configuration_url=host,
            )
            self.device_id = device_entry.id
            _LOGGER.debug("Created new device: %s", self.device_id)

    async def _async_update_data(self):
        """Fetch data from API endpoint and fire events for new records."""
        try:
            async with async_timeout.timeout(10):
                # Get current timestamp
                current_time = int(time.time())
                
                # Fetch raw events from the API
                raw_events = self.client.get_events(self.last_updated, current_time)
                
                # Parse the events using the event parser
                parsed_events = []
                if raw_events and isinstance(raw_events, str):
                    try:
                        parsed_events = self.event_parser.parse(raw_events)
                        _LOGGER.debug("Parsed %d events from raw data", len(parsed_events))
                    except Exception as e:
                        _LOGGER.warning("Failed to parse events: %s", e)
                        parsed_events = []
                elif isinstance(raw_events, list):
                    parsed_events = raw_events
                
                # Fire events for new records
                await self._async_fire_new_events(parsed_events)
                
                # Update state
                self.last_events = parsed_events
                self.last_updated = current_time
                
                return {
                    "events": parsed_events,
                    "last_updated": current_time,
                    "total_events": len(parsed_events)
                }
                
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def _async_fire_new_events(self, current_events: List[Dict[str, Any]]):
        """Fire Home Assistant events for new records that weren't in the last update."""
        if not current_events:
            return
            
        # Create a set of existing event signatures for comparison
        existing_signatures = set()
        for event in self.last_events:
            signature = self._create_event_signature(event)
            existing_signatures.add(signature)
        
        # Check each current event and fire if it's new
        new_events_count = 0
        for event in current_events:
            signature = self._create_event_signature(event)
            if signature not in existing_signatures:
                await self._async_fire_single_event(event)
                new_events_count += 1
        
        if new_events_count > 0:
            _LOGGER.info("Fired %d new events to Home Assistant", new_events_count)

    def _create_event_signature(self, event: Dict[str, Any]) -> str:
        """Create a unique signature for an event to detect duplicates."""
        # Use key fields to create a unique signature
        # Adjust these fields based on your event structure
        signature_fields = [
            str(event.get("RecNo", "")),
            str(event.get("CreateTime", "")),
            str(event.get("Door", "")),
            str(event.get("Method", "")),
            str(event.get("UserID", ""))
        ]
        return "|".join(signature_fields)

    async def _async_fire_single_event(self, event_data: Dict[str, Any]):
        """Fire a single Home Assistant event for the given event data."""
        # Prepare event data according to Home Assistant conventions
        event_payload = {
            "device_id": self.device_id,
            "type": "intelbras_event",
            **event_data  # Include all event data
        }
        
        # Log the event for debugging
        _LOGGER.debug("Firing intelbras_3542mfw_event: %s", event_payload)
        
        # Fire the event on the Home Assistant event bus
        self.hass.bus.async_fire(
            f"{DOMAIN}_event",  # Event type: intelbras_3542mfw_event
            event_payload
        )

    def get_latest_events(self) -> List[Dict[str, Any]]:
        """Get the latest events from the coordinator data."""
        if self.data and isinstance(self.data, dict):
            return self.data.get("events", [])
        return []

    def get_event_count(self) -> int:
        """Get the total number of events from the last update."""
        if self.data and isinstance(self.data, dict):
            return self.data.get("total_events", 0)
        return 0
