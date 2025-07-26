import logging
import requests
from requests.auth import HTTPDigestAuth
from typing import Optional
import urllib3
import time

from event_parser import IntelbrasEventParser

# Disable warnings for insecure SSL requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)


class IntelbrasClient:
    """HTTP client for communicating with Intelbras 3542 MFW devices."""

    def __init__(self, host: str, username: str, password: str, verify_ssl: bool = False):
        """Initialize the Intelbras client."""
        self.host = host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._auth = HTTPDigestAuth(username, password)

    def _make_request(self, endpoint: str, timeout: int = 20) -> requests.Response:
        """Make an HTTP request to the device."""
        url = f"{self.host}/{endpoint}"
        _LOGGER.debug("Making request to %s", url)
        
        session = requests.Session()
        session.verify = self.verify_ssl
        
        response = session.get(
            url, 
            auth=self._auth, 
            stream=True, 
            timeout=timeout
        )
        response.raise_for_status()
        return response

    def open_door(self, channel: int = 1) -> str:
        """Open the door via the access control API."""
        endpoint = f"cgi-bin/accessControl.cgi?action=openDoor&channel={channel}"
        response = self._make_request(endpoint)
        _LOGGER.info("Door open response: %s", response.text)
        return response.text

    def get_door_status(self, channel: int = 1) -> str:
        """Get the door status via the access control API."""
        endpoint = f"cgi-bin/accessControl.cgi?action=getDoorStatus&channel={channel}"
        response = self._make_request(endpoint)
        text = response.text.strip()
        
        # Parse the response format (usually "status=open" or "status=closed")
        if '=' in text:
            status = text.split('=', 1)[1].strip().lower()
        else:
            status = text
            
        _LOGGER.debug("Door status response: %s", status)
        return status
    
    def get_events(self, start_time: int, end_time: int) -> list[dict]: 
        """Get events from the device."""
        endpoint = f"cgi-bin/recordFinder.cgi?action=find&name=AccessControlCardRec&StartTime={start_time}&EndTime={end_time}"
        response = self._make_request(endpoint)
        text = response.text.strip()

        parser = IntelbrasEventParser()
        return parser.parse(text)

    def get_device_info(self) -> Optional[dict]:
        """Get device information (placeholder for future implementation)."""
        # This can be extended to fetch device info, status, etc.
        pass 