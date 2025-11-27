from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "felicity_battery"

DEFAULT_PORT = 53970
DEFAULT_SCAN_INTERVAL = 30  # seconds

PLATFORMS: list[Platform] = [Platform.SENSOR]
