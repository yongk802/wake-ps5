"""Wake PS5 integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import (
    CONF_REGIST_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import PS5StatusCoordinator
from .protocol import PS5RemoteClient


@dataclass(slots=True)
class WakePS5RuntimeData:
    """Runtime data stored for each config entry."""

    client: PS5RemoteClient
    coordinator: PS5StatusCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wake PS5 from a config entry."""

    client = PS5RemoteClient(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_REGIST_KEY],
    )
    coordinator = PS5StatusCoordinator(
        hass,
        client,
        entry.entry_id,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = WakePS5RuntimeData(
        client=client,
        coordinator=coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
