"""Config flow for Wake PS5."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import TextSelector

from .const import (
    CONF_REGIST_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PS5_HOST_TYPE,
)
from .protocol import PS5ConnectionError, PS5RemoteClient


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(),
        vol.Required(CONF_REGIST_KEY): TextSelector(),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): TextSelector(),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            cv.positive_int,
            vol.Range(min=5, max=3600),
        ),
    }
)


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    client = PS5RemoteClient(hass, data[CONF_HOST], data[CONF_REGIST_KEY])
    try:
        status = await client.async_probe()
    except PS5ConnectionError as err:
        raise CannotConnect from err

    if status is None:
        raise CannotConnect

    if status.host_type and status.host_type.upper() != PS5_HOST_TYPE:
        raise InvalidHost

    return {
        "title": data.get(CONF_NAME) or status.host_name or DEFAULT_NAME,
        "unique_id": status.host_id or data[CONF_HOST].strip().lower(),
    }


class WakePS5ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wake PS5."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "invalid_host"
            except ValueError:
                errors["base"] = "invalid_regist_key"
            else:
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidHost(Exception):
    """Error to indicate the host is not a PS5."""
