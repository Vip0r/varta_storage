"""The VARTA Storage integration."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import timedelta

import async_timeout
from vartastorage import vartastorage

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VARTA Storage from a config entry."""

    required_fields = ["scan_interval_modbus", "scan_interval_cgi", "host", "host_cgi", "port", "username", "password"]
    missing_fields = [field for field in required_fields if field not in entry.data]
    if missing_fields:
        message = (
            f"The new version of VARTA Storage integration requires reconfiguration due to newly introduced configuration options"
            "Please [reconfigure the integration](/config/integrations/dashboard) in Home Assistant."
        )
        LOGGER.error(message)
        # Display notification in Home Assistant GUI
        hass.async_create_task(
            hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "VARTA Storage Integration Requires Reconfiguration",
                    "message": message,
                    "notification_id": "varta_storage_reconfigure",
                },
                blocking=False,
            )
        )
        raise ConfigEntryNotReady(
            f"Missing required fields: {', '.join(missing_fields)}. Please reconfigure the integration."
        )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    scan_interval_modbus = timedelta(seconds=entry.data["scan_interval_modbus"])
    scan_interval_cgi = timedelta(seconds=entry.data["scan_interval_cgi"])

    def flatten_dataclass(obj: Any) -> Dict[str, Any]:
        flat_dict = {}
        if hasattr(obj, "__dataclass_fields__"):
            for field in fields(obj):
                value = getattr(obj, field.name)
                if hasattr(value, "__dataclass_fields__"):
                    flat_dict.update(
                        {f"{k}": v for k, v in flatten_dataclass(value).items()}
                    )
                else:
                    flat_dict[field.name] = value
        else:
            flat_dict = {str(obj): obj}
        return flat_dict

    async def async_update_modbus():
        def sync_update():
            try:
                v = vartastorage.VartaStorage(
                    entry.data["host"],
                    entry.data["port"],
                    False,
                    entry.data["username"],
                    entry.data["password"],
                )
                print("getting modbus data")
                r = v.get_all_data_modbus()

            except Exception:
                try:
                    v = vartastorage.VartaStorage(
                        entry.data["host"],
                        entry.data["port"],
                        False,
                        entry.data["username"],
                        entry.data["password"],
                    )
                    print("getting modbus data after first exception")
                    r = v.get_all_data_modbus()
                except Exception as e:
                    LOGGER.info("Can not retrieve Modbus Data from the VARTA Device. %s", e)
                    raise UpdateFailed("Can not retrieve Modbus Data from the VARTA Device.") from Exception
            return flatten_dataclass(r)
        try:
            async with async_timeout.timeout(10):
                return await hass.async_add_executor_job(sync_update)
        except ValueError as api_error:
            raise UpdateFailed("Error communicating with Modbus API") from api_error

    async def async_update_cgi():
        def sync_update():

            try:
                if entry.data["host_cgi"] == "":
                    host = entry.data["host"]
                else:
                    host = entry.data["host_cgi"]

                v = vartastorage.VartaStorage(
                    host,
                    entry.data["port"],
                    True,
                    entry.data["username"],
                    entry.data["password"],
                )

                print("getting cgi data")
                EmsData = v.get_ems_cgi()
                EnergyData = v.get_energy_cgi()
                InfoData = v.get_info_cgi()
                ServiceData = v.get_service_cgi()

                @dataclass
                class VarataStorageData:
                    EmsData: v.get_ems_cgi()
                    EnergyData: v.get_energy_cgi()
                    InfoData: v.get_info_cgi()
                    ServiceData: v.get_service_cgi()

                # Some post processing to the data
                if isinstance(EnergyData.total_charge_cycles, list) and len(EnergyData.total_charge_cycles) == 1:
                    EnergyData.total_charge_cycles = EnergyData.total_charge_cycles[0]

                r = VarataStorageData(EmsData=EmsData, EnergyData=EnergyData, InfoData=InfoData, ServiceData=ServiceData)


            except Exception:
                try:
                    if entry.data["host_cgi"] == "":
                        host = entry.data["host"]
                    else:
                        host = entry.data["host_cgi"]

                    v = vartastorage.VartaStorage(
                        host,
                        entry.data["port"],
                        True,
                        entry.data["username"],
                        entry.data["password"],
                    )

                    print("getting cgi data after first exception")

                    @dataclass
                    class VarataStorageData:
                        EmsData: v.get_ems_cgi()
                        EnergyData: v.get_energy_cgi()
                        InfoData: v.get_info_cgi()
                        ServiceData: v.get_service_cgi()

                    # Some post processing to the data
                    if isinstance(EnergyData.total_charge_cycles, list) and len(EnergyData.total_charge_cycles) == 1:
                        EnergyData.total_charge_cycles = EnergyData.total_charge_cycles[0]

                    r = VarataStorageData(EmsData=EmsData, EnergyData=EnergyData, InfoData=InfoData, ServiceData=ServiceData)

                except Exception as e:
                    LOGGER.info("Can not retrieve CGI Data from the VARTA Device. %s", e)
                    raise UpdateFailed("Can not retrieve CGI Data from the VARTA Device.") from Exception
            return flatten_dataclass(r)
        try:
            async with async_timeout.timeout(10):
                return await hass.async_add_executor_job(sync_update)
        except ValueError as api_error:
            raise UpdateFailed("Error communicating with CGI API") from api_error

    coordinators = {}

    # Always create Modbus coordinator
    modbus_coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name="modbus_sensor",
        update_method=async_update_modbus,
        update_interval=scan_interval_modbus,
        always_update=False,
    )
    await modbus_coordinator.async_config_entry_first_refresh()
    coordinators["modbus"] = modbus_coordinator

    # Optionally create CGI coordinator
    if entry.data.get("cgi"):
        cgi_coordinator = DataUpdateCoordinator(
            hass,
            LOGGER,
            name="cgi_sensor",
            update_method=async_update_cgi,
            update_interval=scan_interval_cgi,
            always_update=False,
        )
        await cgi_coordinator.async_config_entry_first_refresh()
        coordinators["cgi"] = cgi_coordinator

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinators

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
