"""Constants for the VARTA Storage integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTime

DOMAIN = "varta_storage"
LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL_MODBUS = 3
DEFAULT_SCAN_INTERVAL_CGI = 10


@dataclass
class VartaSensorEntityDescription(SensorEntityDescription):
    """Class describing Varta Storage entities."""

    source_key: str | None = None


SENSORS_MODBUS: Final[tuple[VartaSensorEntityDescription, ...]] = (
    VartaSensorEntityDescription(
        key="stateOfCharge",
        name="VARTA State of Charge",
        source_key="soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    VartaSensorEntityDescription(
        key="gridPower",
        name="VARTA Grid Power",
        source_key="grid_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    VartaSensorEntityDescription(
        key="state",
        name="VARTA State Number",
        source_key="state",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="software_version_ems",
        name="VARTA Software Version (EMS)",
        source_key="software_version_ems",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="software_version_ens",
        name="VARTA Software Version (ENS)",
        source_key="software_version_ens",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="software_version_inverter",
        name="VARTA Software Version (INVERTER)",
        source_key="software_version_inverter",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="number_modules",
        name="VARTA Installed Battery Modules",
        source_key="number_modules",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="installed_capacity",
        name="VARTA Installed Capacity",
        source_key="installed_capacity",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    VartaSensorEntityDescription(
        key="stateText",
        name="VARTA State",
        source_key="state_text",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="errorCode",
        name="VARTA Error Code",
        source_key="error_code",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="powerActive",
        name="VARTA Active Power",
        source_key="active_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    VartaSensorEntityDescription(
        key="powerApparent",
        name="VARTA Apparent Power",
        source_key="apparent_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
    ),
    VartaSensorEntityDescription(
        key="powerCharge",
        name="VARTA Charging Power",
        source_key="charge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    VartaSensorEntityDescription(
        key="powerDischarge",
        name="VARTA Discharging Power",
        source_key="discharge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    VartaSensorEntityDescription(
        key="powerChargeTotal",
        name="VARTA Total Power Charged",
        source_key="total_charged_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
)

SENSORS_CGI: Final[tuple[VartaSensorEntityDescription, ...]] = (
    VartaSensorEntityDescription(
        key="cycleCounter",
        name="VARTA Charging Cycle Counter",
        source_key="total_charge_cycles",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="gridPowerToTotal",
        name="VARTA Total Power To Grid",
        source_key="total_grid_dc_ac",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    VartaSensorEntityDescription(
        key="gridPowerFromTotal",
        name="VARTA Total Power From Grid",
        source_key="total_grid_ac_dc",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    VartaSensorEntityDescription(
        key="inverterDischarged",
        name="VARTA Inverter Discharged",
        source_key="total_inverter_dc_ac",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    VartaSensorEntityDescription(
        key="inverterCharged",
        name="VARTA Inverter Charged",
        source_key="total_inverter_ac_dc",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    VartaSensorEntityDescription(
        key="maintnanceFilterDueIn",
        name="VARTA Hours Until Filter Maintenance",
        source_key="hours_until_filter_maintenance",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=UnitOfTime.HOURS,
    ),
    VartaSensorEntityDescription(
        key="fan",
        name="VARTA Fan",
        source_key="status_fan",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="fanSpeed",
        name="VARTA Fan Speed",
        source_key="fan_speed",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="frequencyGrid",
        name="VARTA Grid Frequency",
        source_key="frequency_grid",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
    VartaSensorEntityDescription(
        key="main",
        name="VARTA Main",
        source_key="status_main",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
    ),
)
