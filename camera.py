import logging
from urllib.parse import urlparse, quote_plus

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, DEFAULT_HOST, CONF_VERIFY_SSL

_LOGGER = logging.getLogger(__name__)


def get_rtsp_url(host: str, username: str, password: str, verify_ssl: bool) -> str:
    """
    Generate the RTSP URL for the camera feed.

    Uses 'rtsps' if verify_ssl is True or the host uses HTTPS; otherwise 'rtsp'.
    URL-encodes the username and password to support special characters.
    """
    parsed = urlparse(host)
    netloc = parsed.netloc if parsed.netloc else parsed.path
    username_encoded = quote_plus(username) if username else ""
    password_encoded = quote_plus(password) if password else ""
    protocol = "rtsps" if verify_ssl or parsed.scheme == "https" else "rtsp"
    return f"{protocol}://{username_encoded}:{password_encoded}@{netloc}:554"


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up the Intelbras camera platform from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, False)

    async_add_entities([IntelbrasCamera(host, username, password, verify_ssl)])


class IntelbrasCamera(Camera):
    """Representation of an Intelbras RTSP Camera."""

    def __init__(self, host: str, username: str, password: str, verify_ssl: bool):
        """Initialize the camera."""
        super().__init__()
        self._host = host
        self._username = username
        self._password = password
        self.verify_ssl = verify_ssl

        self._attr_name = "Intelbras Camera"
        self._attr_unique_id = f"{host}_camera"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": "Intelbras 3542 MFW Camera",
            "manufacturer": "Intelbras",
        }

        # Build the RTSP URL with proper credentials and protocol.
        self._rtsp_url = get_rtsp_url(host, username, password, verify_ssl)

        # Advertise streaming support.
        self._attr_supported_features = CameraEntityFeature.STREAM

        # Configure ffmpeg stream options: disable TLS verification if verify_ssl is False.
        # self.stream_options = {}
        # if not verify_ssl:
        #     self.stream_options["-tls_verify"] = "0"

    async def stream_source(self) -> str:
        """Return the RTSP stream URL."""
        return self._rtsp_url

    async def async_camera_image(self, width: int = None, height: int = None):
        """
        Return a still image from the camera.

        Returning None lets Home Assistant's built-in ffmpeg integration use
        the stream_source for live viewing.
        """
        return None
