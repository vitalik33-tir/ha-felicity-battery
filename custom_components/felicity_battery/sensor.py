from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


@dataclass
class FelicitySensorDescription(SensorEntityDescription):
    """Extended description for Felicity sensors."""


SENSOR_DESCRIPTIONS: tuple[FelicitySensorDescription, ...] = (
    FelicitySensorDescription(
        key="soc",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    FelicitySensorDescription(
        key="voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="power",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    FelicitySensorDescription(
        key="temp1",
        name="Battery Temp 1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="temp2",
        name="Battery Temp 2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="max_cell_v",
        name="Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-high",
    ),
    FelicitySensorDescription(
        key="min_cell_v",
        name="Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-low",
    ),
    FelicitySensorDescription(
        key="cell_drift",
        name="Cell Voltage Drift",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-bell-curve",
    ),
    FelicitySensorDescription(
        key="max_charge_current",
        name="Max Charge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    FelicitySensorDescription(
        key="max_discharge_current",
        name="Max Discharge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    FelicitySensorDescription(
        key="state",
        name="Battery State",
        icon="mdi:battery-heart",
    ),
    FelicitySensorDescription(
        key="fault",
        name="Battery Fault",
        icon="mdi:alert",
    ),
    FelicitySensorDescription(
        key="warning",
        name="Battery Warning",
        icon="mdi:alert-circle",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Felicity sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities: list[FelicitySensor] = [
        FelicitySensor(coordinator, entry, desc) for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class FelicitySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Felicity sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: FelicitySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info to group entities into one device."""
        data = self.coordinator.data or {}
        serial = data.get("DevSN") or data.get("wifiSN") or self._entry.entry_id
        return {
            "identifiers": {(DOMAIN, serial)},
            "name": self._entry.data.get("name", "Felicity Battery"),
            "manufacturer": "Felicity",
            "model": "FLA48200",
        }

    @property
    def native_value(self) -> Any:
        """Return the native value of the entity."""
        data: dict = self.coordinator.data or {}
        key = self.entity_description.key

        def get_nested(path: tuple[Any, ...]):
            cur: Any = data
            try:
                for p in path:
                    cur = cur[p]
                return cur
            except (KeyError, IndexError, TypeError):
                return None

        if key == "soc":
            raw = get_nested(("Batsoc", 0, 0))
            return round(raw / 100, 1) if raw is not None else None

        if key == "voltage":
            raw = get_nested(("Batt", 0, 0))
            return round(raw / 1000, 2) if raw is not None else None

        if key == "current":
            raw = get_nested(("Batt", 1, 0))
            return round(raw / 10, 1) if raw is not None else None

        if key == "power":
            v_raw = get_nested(("Batt", 0, 0))
            i_raw = get_nested(("Batt", 1, 0))
            if v_raw is None or i_raw is None:
                return None
            v = v_raw / 1000
            i = i_raw / 10
            return round(v * i)

        if key == "temp1":
            raw = get_nested(("BTemp", 0, 0))
            return round(raw / 10, 1) if raw is not None else None

        if key == "temp2":
            raw = get_nested(("BTemp", 0, 1))
            return round(raw / 10, 1) if raw is not None else None

        if key == "max_cell_v":
            raw = get_nested(("BMaxMin", 0, 0))
            return round(raw / 1000, 3) if raw is not None else None

        if key == "min_cell_v":
            raw = get_nested(("BMaxMin", 0, 1))
            return round(raw / 1000, 3) if raw is not None else None

        if key == "cell_drift":
            max_raw = get_nested(("BMaxMin", 0, 0))
            min_raw = get_nested(("BMaxMin", 0, 1))
            if max_raw is None or min_raw is None:
                return None
            return round((max_raw - min_raw) / 1000, 3)

        if key == "max_charge_current":
            raw = get_nested(("LVolCur", 1, 0))
            return round(raw / 10, 1) if raw is not None else None

        if key == "max_discharge_current":
            raw = get_nested(("LVolCur", 1, 1))
            return round(raw / 10, 1) if raw is not None else None

        if key == "state":
            code = data.get("Estate")
            if code is None:
                return None
            if code == 320:
                return "full"
            if code == 960:
                return "standby"
            if code == 9152:
                return "charging"
            if code == 5056:
                return "discharging"
            return f"unknown({code})"

        if key == "fault":
            v = data.get("Bfault")
            if v is None:
                return None
            return int(v)

        if key == "warning":
            v = data.get("Bwarn")
            if v is None:
                return None
            return int(v)

        return None
