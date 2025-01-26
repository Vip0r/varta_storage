"""The VARTA Storage integration."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import timedelta

import async_timeout
from vartastorage import vartastorage

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VARTA Storage from a config entry."""

    # Reload entry when its updated.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    async def async_update_data():
        """Fetch data and preo-process the data from API endpoint."""

        def sync_update():
            """Utilizing synchronous task as the used PyPI Package is not built with async."""
            try:
                # Collect all data from the device at once
                v = vartastorage.VartaStorage(
                    entry.data["host"],
                    entry.data["port"],
                    entry.data["cgi"],
                    entry.data["username"],
                    entry.data["password"],
                )

                if entry.data["cgi"]:
                    r = v.get_all_data()
                else:
                    r = v.get_all_data_modbus()
            except Exception:
                try:
                    # This is a bit ugly but at least my device is very unresponsible and we just go to try it a second time before raising an exception
                    v = vartastorage.VartaStorage(
                        entry.data["host"],
                        entry.data["port"],
                        entry.data["cgi"],
                        entry.data["username"],
                        entry.data["password"],
                    )

                    if entry.data["cgi"]:
                        r = v.get_all_data()
                    else:
                        r = v.get_all_data_modbus()
                except Exception as e:
                    LOGGER.Info("Can not retrieve Data from the VARTA Device. %s", e)
                    raise UpdateFailed(
                        "Can not retrieve Data from the VARTA Device."
                    ) from Exception

            # Flatten dataclass

            def flatten_dataclass(obj: Any) -> Dict[str, Any]:
                flat_dict = {}

                if hasattr(obj, "__dataclass_fields__"):  # Check if it's a dataclass
                    for field in fields(obj):
                        value = getattr(obj, field.name)
                        if hasattr(value, "__dataclass_fields__"):  # Nested dataclass
                            # Recursively flatten nested dataclass
                            flat_dict.update(
                                {f"{k}": v for k, v in flatten_dataclass(value).items()}
                            )
                        else:
                            flat_dict[field.name] = value
                else:
                    flat_dict = {str(obj): obj}  # If it's not a dataclass, return as is

                return flat_dict

            return flatten_dataclass(r)

        try:
            async with async_timeout.timeout(10):
                # Call synchronous task to update the sensor values
                return await hass.async_add_executor_job(sync_update)
        except ValueError as api_error:
            raise UpdateFailed("Error communicating with API") from api_error

    scan_interval = timedelta(seconds=entry.data["scan_interval"])

    coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        # Name of the data. For logging purposes.
        name="sensor",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=scan_interval,
        always_update=False,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward the setup to the sensor platform.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_reload_entry(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass, entry):
    """Handle options update."""
    LOGGER.info("Config options update in GUI")
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await hass.config_entries.async_reload(entry.entry_id)
