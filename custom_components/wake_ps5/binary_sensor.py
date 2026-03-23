"""Binary sensor platform for Wake PS5."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WakePS5RuntimeData
from .const import DOMAIN
from .entity import WakePS5Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: WakePS5RuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [PS5PowerBinarySensor(entry, runtime.client, runtime.coordinator)]
    )


class PS5PowerBinarySensor(WakePS5Entity, BinarySensorEntity):
    """Binary sensor that reflects whether the PS5 is reachable."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, entry, client, coordinator) -> None:
        super().__init__(entry, client, coordinator)
        self._attr_name = "Reachable"
        self._attr_unique_id = f"{entry.entry_id}_reachable"

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.is_reachable

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        attributes = super().extra_state_attributes or {}
        if not self.coordinator.last_update_success:
            attributes["power_state"] = "unreachable"
            return attributes

        raw_power_state = self.coordinator.data.raw.get("power_state")
        if raw_power_state:
            attributes["power_state"] = str(raw_power_state)
            return attributes

        if self.coordinator.data.is_on:
            attributes["power_state"] = "on"
        elif self.coordinator.data.is_standby:
            attributes["power_state"] = "standby"
        else:
            attributes["power_state"] = "unknown"
        return attributes
