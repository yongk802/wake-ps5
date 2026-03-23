"""Minimal PS5 Remote Play discovery and wake protocol helpers."""

from __future__ import annotations

import logging
import socket
from collections.abc import Callable
import subprocess

from homeassistant.core import HomeAssistant

from .const import (
    DDP_SEARCH,
    DDP_VERSION,
    DDP_WAKEUP,
    DEFAULT_TIMEOUT,
    PS5_DISCOVERY_PORT,
    PS5_HOST_TYPE,
    PS5_LOCAL_PORT,
    STATUS_OK,
    STATUS_STANDBY,
)
from .models import PS5Status

_LOGGER = logging.getLogger(__name__)


class PS5ProtocolError(Exception):
    """Base protocol error."""


class PS5ConnectionError(PS5ProtocolError):
    """Raised when the PS5 cannot be reached."""


def _build_message(
    message_type: str, extra_fields: dict[str, str] | None = None
) -> bytes:
    lines = [f"{message_type} * HTTP/1.1"]
    if extra_fields:
        for key, value in extra_fields.items():
            lines.append(f"{key}:{value}")
    lines.append(f"device-discovery-protocol-version:{DDP_VERSION}")
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def _open_socket(timeout: float) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.bind(("0.0.0.0", PS5_LOCAL_PORT))
    except OSError:
        sock.bind(("0.0.0.0", 0))
    return sock


def _parse_response(response: bytes, host_ip: str) -> PS5Status | None:
    payload = response.decode("utf-8", errors="ignore")
    fields: dict[str, str | int] = {"host-ip": host_ip}

    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("HTTP/1.1 "):
            parts = line.split(" ", 2)
            if len(parts) >= 3 and parts[1].isdigit():
                fields["status-code"] = int(parts[1])
                fields["status"] = parts[2]
            continue

        key, separator, value = line.partition(":")
        if separator:
            fields[key] = value

    if not fields.get("status-code"):
        return None

    status_code = int(fields["status-code"])
    return PS5Status(
        available=True,
        is_reachable=True,
        is_on=status_code == STATUS_OK,
        is_standby=status_code == STATUS_STANDBY,
        host_name=_as_text(fields.get("host-name")),
        host_type=_as_text(fields.get("host-type")),
        host_id=_as_text(fields.get("host-id")),
        host_ip=_as_text(fields.get("host-ip")),
        system_version=_as_text(fields.get("system-version")),
        running_app_name=_as_text(fields.get("running-app-name")),
        raw=dict(fields),
    )


def _as_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _normalize_credential(regist_key: str) -> str:
    """Normalize a pyremoteplay RegistKey into a PS5 wake credential.

    The RegistKey stored by pyremoteplay is a double-encoded hex string.
    This reverses that encoding to produce the integer credential the PS5
    expects in the user-credential field of the WAKEUP DDP message.
    """
    value = regist_key.strip()
    if not value:
        raise ValueError("Registration key cannot be empty")

    compact = value.replace(" ", "").replace(":", "")
    if any(char not in "0123456789abcdefABCDEF" for char in compact):
        raise ValueError("Registration key must be hex or a numeric credential")

    try:
        first_pass = bytes.fromhex(compact)
    except ValueError as err:
        raise ValueError("Registration key is not valid hex") from err

    try:
        ascii_hex = first_pass.decode("ascii")
        second_pass = bytes.fromhex(ascii_hex)
        return str(int.from_bytes(second_pass, "big"))
    except (UnicodeDecodeError, ValueError) as err:
        raise ValueError("Registration key is not valid pyremoteplay format") from err


def fetch_status(host: str, timeout: float = DEFAULT_TIMEOUT) -> PS5Status | None:
    """Fetch the current PS5 Remote Play status."""

    return _run_socket_request(
        host,
        lambda target, sock: _fetch_status_from_socket(target, sock),
        timeout,
    )


def wake_console(host: str, regist_key: str, timeout: float = DEFAULT_TIMEOUT) -> None:
    """Send a wake packet to the PS5."""

    credential = _normalize_credential(regist_key)
    _LOGGER.debug("wake_console: host=%s credential=%s", host, credential)
    message = _build_message(
        DDP_WAKEUP,
        {
            "user-credential": credential,
            "client-type": "vr",
            "auth-type": "R",
            "model": "w",
            "app-type": "r",
        },
    )
    _LOGGER.debug("wake_console: message=%s", message.decode("utf-8"))
    _run_socket_request(
        host,
        lambda target, sock: sock.sendto(message, (target, PS5_DISCOVERY_PORT)),
        timeout,
    )
    _LOGGER.debug("wake_console: packet sent to %s:%s", host, PS5_DISCOVERY_PORT)


def _fetch_status_from_socket(target: str, sock: socket.socket) -> PS5Status | None:
    message = _build_message(DDP_SEARCH)
    sock.sendto(message, (target, PS5_DISCOVERY_PORT))
    while True:
        response, address = sock.recvfrom(1024)
        if address[0] != target:
            continue
        return _parse_response(response, address[0])


def _run_socket_request(
    host: str,
    callback: Callable[[str, socket.socket], PS5Status | int | None],
    timeout: float,
) -> PS5Status | None:
    try:
        target = socket.gethostbyname(host)
        with _open_socket(timeout) as sock:
            result = callback(target, sock)
    except (socket.gaierror, TimeoutError, OSError) as err:
        raise PS5ConnectionError(f"Could not reach PS5 host {host}") from err

    if isinstance(result, PS5Status) or result is None:
        return result
    return None


class PS5RemoteClient:
    """Home Assistant friendly wrapper around the PS5 wake protocol."""

    def __init__(self, hass: HomeAssistant, host: str, regist_key: str) -> None:
        self._hass = hass
        self.host = host
        self.regist_key = regist_key

        # Validate once during setup so later calls fail less often.
        _normalize_credential(regist_key)

    async def async_get_status(self) -> PS5Status | None:
        return await self._hass.async_add_executor_job(fetch_status, self.host)

    async def async_wake(self) -> None:
        await self._hass.async_add_executor_job(
            wake_console, self.host, self.regist_key
        )

    async def async_wake_with_retries(
        self, retries: int = 3, delay: float = 1.0
    ) -> None:
        """Send multiple wake packets, retrying if the PS5 does not respond."""

        def _retry_wake() -> None:
            for i in range(retries):
                wake_console(self.host, self.regist_key)
                if i < retries - 1:
                    import time

                    time.sleep(delay)

        await self._hass.async_add_executor_job(_retry_wake)

    async def async_probe(self) -> PS5Status | None:
        return await self.async_get_status()

    async def async_is_reachable(self) -> bool:
        return await self._hass.async_add_executor_job(is_reachable, self.host)

    @property
    def host_type(self) -> str:
        return PS5_HOST_TYPE


def is_reachable(host: str, timeout: float = DEFAULT_TIMEOUT) -> bool:
    """Return whether the host answers ICMP ping."""

    try:
        completed = subprocess.run(
            ["ping", "-c", "1", "-W", str(max(1, int(timeout))), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False

    return completed.returncode == 0
