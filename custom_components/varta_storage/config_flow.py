"""Config flow for VARTA Storage integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from vartastorage import vartastorage

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=502): int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        vol.Optional(CONF_USERNAME, default="user1"): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
    }
)


class VartaStorageHub:
    """Provide methods for GUI configuration."""

    def __init__(
        self,
        host: str,
        port: int,
        scan_interval: cv.time_period,
        username: str = None,
        password: str = None,
    ) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.serial = ""
        self.scan_interval = scan_interval
        self.username = username
        self.password = password

    def test_connection(self) -> bool:
        """Tests a connection to the VartaStorage device."""
        varta = vartastorage.VartaStorage(
            self.host, self.port, self.username, self.password
        )
        try:
            modbus_data = varta.get_raw_data_modbus()
            self.serial = modbus_data.serial
            return bool(varta.modbus_client.connect())
        except ValueError:
            return False


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    hub = VartaStorageHub(
        data["host"],
        data["port"],
        data["scan_interval"],
        data["username"],
        data["password"],
    )

    # Used PyPI package is not built with async, passing to the sync executor.
    if not await hass.async_add_executor_job(hub.test_connection):
        raise CannotConnect

    # Return info stored in the config entry.
    return {
        "title": f"{data['host']} (S/N: {hub.serial} )",
        "serial": hub.serial,
        "scan_interval": hub.scan_interval,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VARTA Storage."""

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        # except Exception:  # pylint: disable=broad-except
        #    LOGGER.warning("Unexpected exception")
        #    errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(info["serial"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for VARTA Storage."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # update config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )

            return self.async_create_entry(
                title=self.config_entry.title, data=user_input
            )

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_USER_DATA_SCHEMA,
        )
