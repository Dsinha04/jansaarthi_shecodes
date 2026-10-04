"""RFID + fingerprint access.

mock mode (default): RFID uid comes from the request; fingerprint scan returns the id sent in the
request, or 1 if none. Lets the whole UI be tested on a laptop.
real mode: implement read_rfid()/scan_fingerprint() for your reader. Common setups:
  * USB RFID reader acting as a keyboard: the frontend captures it, so nothing is needed here.
  * Serial fingerprint sensor (R307/AS608): use pyserial or the `adafruit-circuitpython-fingerprint`
    library inside scan_fingerprint(); return the matched template id.
"""
from typing import Optional
from ..config import settings
from ..errors import AppError


def mode() -> str:
    return settings.hardware_mode


def scan_fingerprint(requested_id: Optional[int] = None) -> int:
    if mode() == "mock":
        return requested_id if requested_id is not None else 1
    raise AppError(501, "fingerprint_not_implemented",
                   "Fingerprint sensor driver is not set up. See app/services/hardware.py.")
