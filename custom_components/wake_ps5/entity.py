"""Shared entity helpers for Wake PS5."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PS5_HOST_TYPE
from .coordinator import PS5StatusCoordinator
from .protocol import PS5RemoteClient


class WakePS5Entity(CoordinatorEntity[PS5StatusCoordinator]):
    """Base entity for Wake PS5 entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        client: PS5RemoteClient,
        coordinator: PS5StatusCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._client = client

    @property
    def device_info(self) -> DeviceInfo:
        status = self.coordinator.data if self.coordinator.last_update_success else None
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Sony",
            model=(status.host_type if status and status.host_type else PS5_HOST_TYPE),
            sw_version=(status.system_version if status else None),
        )

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        attributes: dict[str, str] = {"host": self._client.host}
        status = self.coordinator.data if self.coordinator.last_update_success else None
        if status and status.host_ip:
            attributes["host_ip"] = status.host_ip
        if status and status.running_app_name:
            attributes["running_app"] = status.running_app_name
        return attributes
