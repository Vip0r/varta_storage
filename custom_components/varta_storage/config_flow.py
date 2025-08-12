"""Config flow for VARTA Storage integration."""

from __future__ import annotations

from typing import Any

from vartastorage import vartastorage
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DEFAULT_SCAN_INTERVAL_CGI,
    DEFAULT_SCAN_INTERVAL_MODBUS,
    DOMAIN,
    LOGGER,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=502): int,
        vol.Optional("scan_interval_modbus", default=DEFAULT_SCAN_INTERVAL_MODBUS): int,
        vol.Required("cgi", default=True): bool,
        vol.Optional("host_cgi", default=""): str,
        vol.Optional(CONF_USERNAME, default="user1"): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
        vol.Optional("scan_interval_cgi", default=DEFAULT_SCAN_INTERVAL_CGI): int,
    }
)


class VartaHub:
    """Provide methods for GUI configuration."""

    def __init__(
        self,
        host: str,
        port: int,
        scan_interval_modbus: int,
        cgi: bool,
        scan_interval_cgi: int,
        host_cgi: str = None,
        username: str = None,
        password: str = None,
    ) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.serial = ""
        self.scan_interval_modbus = scan_interval_modbus
        self.cgi = cgi
        self.host_cgi = host_cgi
        self.username = username
        self.password = password
        self.scan_interval_cgi = scan_interval_cgi

    def test_connection(self) -> bool:
        """Tests a connection to the VartaStorage device."""
        varta = vartastorage.VartaStorage(
            self.host, self.port, self.cgi, self.username, self.password
        )
        try:
            self.serial = varta.modbus_client.get_serial()
            return True
        except ValueError:
            return False


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    hub = VartaHub(
        data["host"],
        data["port"],
        data["scan_interval_modbus"],
        data["cgi"],
        data["host_cgi"],
        data["username"],
        data["password"],
        data["scan_interval_cgi"],
    )

    # Used PyPI package is not built with async, passing to the sync executor.
    if not await hass.async_add_executor_job(hub.test_connection):
        raise CannotConnect

    # Return info stored in the config entry.
    return {
        "title": f"{data['host']} (S/N: {hub.serial} )",
        "serial": hub.serial,
        "scan_interval_modbus": hub.scan_interval_modbus,
        "scan_interval_cgi": hub.scan_interval_cgi,
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
        except Exception as e:  # pylint: disable=broad-except
            LOGGER.warning("Unexpected exception: %s", e)
            errors["base"] = "unknown"
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        # Get current values from config entry
        current = self.config_entry.data.copy()
        current.update(self.config_entry.options)

        if user_input is not None:
            # update config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )

            return self.async_create_entry(
                title=self.config_entry.title, data=user_input
            )

        # Build schema with current values as defaults
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current.get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=current.get(CONF_PORT, 502)): int,
                vol.Optional("scan_interval_modbus", default=current.get("scan_interval_modbus", DEFAULT_SCAN_INTERVAL_MODBUS)): int,
                vol.Required("cgi", default=current.get("cgi", True)): bool,
                vol.Optional("host_cgi", default=""): str,
                vol.Optional(CONF_USERNAME, default=current.get(CONF_USERNAME, "user1")): str,
                vol.Optional(CONF_PASSWORD, default=current.get(CONF_PASSWORD, "")): str,
                vol.Optional("scan_interval_cgi", default=current.get("scan_interval_cgi", DEFAULT_SCAN_INTERVAL_CGI)): int,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
