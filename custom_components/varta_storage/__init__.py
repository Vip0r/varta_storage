"""The VARTA Storage integration."""

from __future__ import annotations

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
    varta = vartastorage.VartaStorage(
        entry.data["host"],
        entry.data["port"],
        entry.data["username"],
        entry.data["password"],
    )
    if varta.modbus_client.connect() is False:
        LOGGER.warning("Could not connect to modbus server")
        raise ConfigEntryNotReady

    # Reload entry when its updated.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    async def async_update_data():
        """Fetch data and pre-process the data from API endpoint."""

        def sync_update():
            """Utilizing synchronous task as the used PyPI Package is not built with async."""
            varta = vartastorage.VartaStorage(entry.data["host"], entry.data["port"])
            # Collect all data from the device at once
            varta_data = varta.get_all_data()

            # Pre-Select the data we plan to use for our sensor entities
            data = varta_data.modbus_data

            def addCgiData(data, endpoint, attribute):
                """Adding additional data if the cgi endpoint is available."""
                if hasattr(endpoint, attribute):
                    setattr(data, attribute, getattr(endpoint, attribute))

            addCgiData(data, varta_data.service_data, "status_fan")
            addCgiData(data, varta_data.service_data, "status_main")
            addCgiData(data, varta_data.service_data, "hours_until_filter_maintenance")
            addCgiData(data, varta_data.energy_data, "total_grid_ac_dc")
            addCgiData(data, varta_data.energy_data, "total_grid_dc_ac")
            addCgiData(data, varta_data.energy_data, "total_inverter_ac_dc")
            addCgiData(data, varta_data.energy_data, "total_inverter_dc_ac")
            addCgiData(data, varta_data.energy_data, "total_charge_cycles")

            return data

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
