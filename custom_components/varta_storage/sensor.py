"""Sensor platform of the VARTA Storage integration."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSORS_MODBUS, SENSORS_CGI, VartaSensorEntityDescription


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Initialize the integration."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if entry.data["cgi"]:
        async_add_entities(
            VartaStorageEntity(coordinator, description=description)
            for description in SENSORS_CGI
        )

    async_add_entities(
        VartaStorageEntity(coordinator, description=description)
        for description in SENSORS_MODBUS
    )


class VartaStorageEntity(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
    should_poll
    async_update
    async_added_to_hass
    available

    """

    entity_description: VartaSensorEntityDescription

    def __init__(self, coordinator, description: VartaSensorEntityDescription):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            configuration_url=f"http://{coordinator.config_entry.data['host']}",
            identifiers={(DOMAIN, str(coordinator.config_entry.unique_id))},
            manufacturer="VARTA",
            name="VARTA Battery",
        )

        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}-{self.entity_description.key}"
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.entity_description.source_key is None:
            raise Exception(
                "Invalid entity configuration: source_key is not set in varta entity description."
            )
        self._attr_native_value = self.coordinator.data.get(
            self.entity_description.source_key
        )

        self.async_write_ha_state()
