"""Data models for the Wake PS5 integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class PS5Status:
    """A parsed PS5 Remote Play status."""

    available: bool
    is_reachable: bool
    is_on: bool
    is_standby: bool
    host_name: str | None = None
    host_type: str | None = None
    host_id: str | None = None
    host_ip: str | None = None
    system_version: str | None = None
    running_app_name: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
