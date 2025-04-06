import logging
from urllib.parse import urlparse

from homeassistant.components.camera import Camera
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, DEFAULT_HOST

_LOGGER = logging.getLogger(__name__)

def get_rtsp_url(host, username, password):
    """Generate the RTSP URL for the camera feed.
    
    Assumes the host is provided as an HTTP URL (e.g. "http://192.168.1.123").
    Extracts the network location and builds a RTSP URL.
    """
    parsed = urlparse(host)
    # If host is given as http://192.168.1.123 then netloc is "192.168.1.123"
    netloc = parsed.netloc if parsed.netloc else parsed.path
    # Modify the port and stream path if needed for your device.
    return f"rtsp://{username}:{password}@{netloc}:554/"

async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the camera platform from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)

    async_add_entities([IntelbrasCamera(host, username, password)])

class IntelbrasCamera(Camera):
    """Representation of an Intelbras RTSP Camera."""

    def __init__(self, host, username, password):
        """Initialize the camera."""
        super().__init__()
        self._host = host
        self._username = username
        self._password = password
        self._attr_name = "Intelbras Camera"
        self._attr_unique_id = f"{host}_camera"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": "Intelbras 3542 MFW Camera",
            "manufacturer": "Intelbras",
        }
        self._rtsp_url = get_rtsp_url(host, username, password)

    @property
    def stream_source(self):
        """Return the RTSP stream URL."""
        return self._rtsp_url

    async def async_camera_image(self):
        """Return a still image from the camera.
        
        In this example, we return None so that Home Assistant's built-in ffmpeg integration
        can use the stream_source for live viewing.
        """
        return None
