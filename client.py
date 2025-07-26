import logging
import aiohttp
from aiohttp import ClientTimeout, ClientSession
from typing import Optional, Dict
import time
import hashlib
import re
from urllib.parse import urlparse

from .event_parser import IntelbrasEventParser

_LOGGER = logging.getLogger(__name__)


class DigestAuth:
    """HTTP Digest Authentication handler for aiohttp."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.last_challenge = None

    def parse_challenge(self, auth_header: str) -> Dict[str, str]:
        """Parse the WWW-Authenticate header for digest challenge."""
        challenge = {}
        # Remove 'Digest ' prefix
        auth_header = auth_header.replace('Digest ', '', 1)
        
        # Parse key=value pairs
        items = re.findall(r'(\w+)=(?:"([^"]+)"|([^,\s]+))', auth_header)
        for item in items:
            key = item[0]
            value = item[1] if item[1] else item[2]
            challenge[key] = value
            
        return challenge

    def create_digest_response(self, method: str, uri: str, challenge: Dict[str, str]) -> str:
        """Create the digest response for authentication."""
        realm = challenge.get('realm', '')
        nonce = challenge.get('nonce', '')
        qop = challenge.get('qop', '')
        opaque = challenge.get('opaque', '')
        algorithm = challenge.get('algorithm', 'MD5')
        
        # Client nonce for qop
        cnonce = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
        nc = "00000001"  # Nonce count
        
        # Calculate HA1
        if algorithm.upper() == 'MD5':
            ha1 = hashlib.md5(f"{self.username}:{realm}:{self.password}".encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
            
        # Calculate HA2
        ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
        
        # Calculate response
        if qop:
            if 'auth' in qop:
                response = hashlib.md5(f"{ha1}:{nonce}:{nc}:{cnonce}:auth:{ha2}".encode()).hexdigest()
            else:
                raise ValueError(f"Unsupported qop: {qop}")
        else:
            response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
        
        # Build authorization header
        auth_parts = [
            f'username="{self.username}"',
            f'realm="{realm}"',
            f'nonce="{nonce}"',
            f'uri="{uri}"',
            f'response="{response}"',
        ]
        
        if opaque:
            auth_parts.append(f'opaque="{opaque}"')
            
        if qop:
            auth_parts.append(f'qop=auth')
            auth_parts.append(f'nc={nc}')
            auth_parts.append(f'cnonce="{cnonce}"')
            
        if algorithm:
            auth_parts.append(f'algorithm={algorithm}')
            
        return "Digest " + ", ".join(auth_parts)


class IntelbrasClient:
    """Async HTTP client for communicating with Intelbras 3542 MFW devices."""

    def __init__(self, host: str, username: str, password: str, verify_ssl: bool = False):
        """Initialize the Intelbras client."""
        self.host = host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.digest_auth = DigestAuth(username, password)

    async def _make_request(self, endpoint: str, timeout: int = 20) -> str:
        """Make an async HTTP request to the device with digest authentication."""
        url = f"{self.host}/{endpoint}"
        _LOGGER.debug("Making async request to %s", url)
        
        # Create SSL context
        ssl_context = None if self.verify_ssl else False
        
        # Set up timeout
        client_timeout = ClientTimeout(total=timeout)
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with ClientSession(
            timeout=client_timeout,
            connector=connector
        ) as session:
            try:
                # First attempt without auth to get the digest challenge
                async with session.get(url) as response:
                    if response.status == 401:
                        # Get the WWW-Authenticate header
                        auth_header = response.headers.get('WWW-Authenticate')
                        if not auth_header or 'Digest' not in auth_header:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=401,
                                message="Server requires Digest authentication but no digest challenge found"
                            )
                        
                        # Parse the challenge
                        challenge = self.digest_auth.parse_challenge(auth_header)
                        _LOGGER.debug("Received digest challenge: %s", challenge)
                        
                        # Create the digest response
                        parsed_url = urlparse(url)
                        uri = parsed_url.path
                        if parsed_url.query:
                            uri += f"?{parsed_url.query}"
                            
                        auth_response = self.digest_auth.create_digest_response("GET", uri, challenge)
                        
                        # Make the authenticated request
                        headers = {"Authorization": auth_response}
                        async with session.get(url, headers=headers) as auth_resp:
                            auth_resp.raise_for_status()
                            text = await auth_resp.text()
                            _LOGGER.debug("Authenticated response from %s: %s", url, text[:200])
                            return text
                    else:
                        # Unexpected - got response without authentication
                        response.raise_for_status()
                        text = await response.text()
                        _LOGGER.debug("Response from %s: %s", url, text[:200])
                        return text
                        
            except aiohttp.ClientError as e:
                _LOGGER.error("HTTP request failed for %s: %s", url, e)
                raise
            except Exception as e:
                _LOGGER.error("Unexpected error making request to %s: %s", url, e)
                raise

    async def open_door(self, channel: int = 1) -> str:
        """Open the door via the access control API."""
        endpoint = f"cgi-bin/accessControl.cgi?action=openDoor&channel={channel}"
        response_text = await self._make_request(endpoint)
        _LOGGER.info("Door open response: %s", response_text)
        return response_text

    async def get_door_status(self, channel: int = 1) -> str:
        """Get the door status via the access control API."""
        endpoint = f"cgi-bin/accessControl.cgi?action=getDoorStatus&channel={channel}"
        response_text = await self._make_request(endpoint)
        text = response_text.strip()
        
        # Parse the response format (usually "status=open" or "status=closed")
        if '=' in text:
            status = text.split('=', 1)[1].strip().lower()
        else:
            status = text
            
        _LOGGER.debug("Door status response: %s", status)
        return status
    
    async def get_events(self, start_time: int, end_time: int) -> str:
        """Get events from the device."""
        endpoint = f"cgi-bin/recordFinder.cgi?action=find&name=AccessControlCardRec&StartTime={start_time}&EndTime={end_time}"
        response_text = await self._make_request(endpoint)
        _LOGGER.debug("Events response (first 500 chars): %s", response_text[:500])
        return response_text

    async def get_device_info(self) -> Optional[dict]:
        """Get device information."""
        try:
            endpoint = "cgi-bin/magicBox.cgi?action=getDeviceInfo"
            response_text = await self._make_request(endpoint)
            # Parse device info response here if needed
            return {"raw_info": response_text}
        except Exception as e:
            _LOGGER.warning("Could not fetch device info: %s", e)
            return None

    async def test_connection(self) -> bool:
        """Test if we can connect to the device."""
        try:
            await self.get_device_info()
            return True
        except Exception as e:
            _LOGGER.error("Connection test failed: %s", e)
            return False 
        