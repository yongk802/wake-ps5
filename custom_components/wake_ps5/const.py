"""Constants for the Wake PS5 integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "wake_ps5"
PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.BINARY_SENSOR]

CONF_REGIST_KEY = "regist_key"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_NAME = "PlayStation 5"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 2.0

PS5_HOST_TYPE = "PS5"
PS5_DISCOVERY_PORT = 9302
PS5_LOCAL_PORT = 9303

DDP_VERSION = "00030010"
DDP_SEARCH = "SRCH"
DDP_WAKEUP = "WAKEUP"

STATUS_OK = 200
STATUS_STANDBY = 620
