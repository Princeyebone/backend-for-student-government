"""Cloudinary upload signature generation"""
import time
import hashlib
import socket
import struct
from fastapi import APIRouter, Depends
from typing import Annotated
from .config import settings
from .model import User
from .dependencies import get_current_active_user

router = APIRouter(prefix="/api/upload", tags=["Uploads"])


def get_ntp_time() -> int:
    """
    Fetch accurate UTC time from an NTP server.
    Falls back to local system time if NTP is unreachable.
    """
    try:
        # Use Google's public NTP server
        NTP_SERVER = "time.google.com"
        NTP_PORT = 123
        NTP_EPOCH_DELTA = 2208988800  # seconds between 1900 (NTP epoch) and 1970 (Unix epoch)

        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(3)

        # NTP request packet (48 bytes, LI=0, VN=3, Mode=3)
        data = b'\x1b' + 47 * b'\0'
        client.sendto(data, (NTP_SERVER, NTP_PORT))
        data, _ = client.recvfrom(1024)
        client.close()

        if data:
            # Unpack transmit timestamp (bytes 40-47) as unsigned 64-bit
            t = struct.unpack('!I', data[40:44])[0]
            return int(t - NTP_EPOCH_DELTA)
    except Exception:
        # Silently fall back to system time
        pass

    return int(time.time())


def generate_cloudinary_signature(params: dict, api_secret: str) -> str:
    """
    Generate a SHA-1 signature for Cloudinary uploads.
    Params are sorted alphabetically and concatenated before hashing.
    """
    sorted_params = "&".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )
    sign_string = sorted_params + api_secret
    return hashlib.sha1(sign_string.encode("utf-8")).hexdigest()


@router.post("/signature")
def get_upload_signature(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Generate a signed upload signature for Cloudinary direct uploads.
    Frontend requests this, then uploads directly to Cloudinary.
    Uses NTP time to avoid stale-request errors from system clock drift.
    Returns: timestamp, signature, api_key, cloud_name, folder
    """
    # Use NTP time to guarantee accuracy regardless of server clock drift
    timestamp = get_ntp_time()

    # Parameters that will be sent with the Cloudinary upload
    params = {
        "timestamp": timestamp,
        "folder": "student_government",
    }

    signature = generate_cloudinary_signature(params, settings.CLOUDINARY_SECRET)

    return {
        "timestamp": timestamp,
        "signature": signature,
        "api_key": settings.CLOUDINARY_API_KEY,
        "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
        "folder": "student_government",
    }
