"""Button platform for Wake PS5."""

from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WakePS5RuntimeData
from .const import DOMAIN
from .entity import WakePS5Entity

WAKE_RETRIES = 3
WAKE_RETRY_DELAY = 1.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: WakePS5RuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WakePS5Button(entry, runtime.client, runtime.coordinator)])


class WakePS5Button(WakePS5Entity, ButtonEntity):
    """Button entity that wakes the PS5."""

    def __init__(self, entry, client, coordinator) -> None:
        super().__init__(entry, client, coordinator)
        self._attr_name = "Wake"
        self._attr_unique_id = f"{entry.entry_id}_wake"

    @property
    def available(self) -> bool:
        return True

    async def async_press(self) -> None:
        await self._client.async_wake_with_retries(
            retries=WAKE_RETRIES, delay=WAKE_RETRY_DELAY
        )
        self.hass.async_create_task(self._async_delayed_refresh())

    async def _async_delayed_refresh(self) -> None:
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()
