"""Coordinator for Wake PS5."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import PS5Status
from .protocol import PS5ConnectionError, PS5RemoteClient

_LOGGER = logging.getLogger(__name__)


class PS5StatusCoordinator(DataUpdateCoordinator[PS5Status]):
    """Coordinate PS5 status updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PS5RemoteClient,
        entry_id: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> PS5Status:
        try:
            status = await self.client.async_get_status()
        except PS5ConnectionError as err:
            if await self.client.async_is_reachable():
                return PS5Status(
                    available=True,
                    is_reachable=True,
                    is_on=False,
                    is_standby=False,
                    host_ip=self.client.host,
                    raw={"power_state": "reachable_unknown", "error": str(err)},
                )
            return PS5Status(
                available=False,
                is_reachable=False,
                is_on=False,
                is_standby=False,
                host_ip=self.client.host,
                raw={"power_state": "unreachable", "error": str(err)},
            )

        if status is None:
            if await self.client.async_is_reachable():
                return PS5Status(
                    available=True,
                    is_reachable=True,
                    is_on=False,
                    is_standby=False,
                    host_ip=self.client.host,
                    raw={"power_state": "reachable_unknown"},
                )
            return PS5Status(
                available=False,
                is_reachable=False,
                is_on=False,
                is_standby=False,
                host_ip=self.client.host,
                raw={"power_state": "unreachable"},
            )
        return status
