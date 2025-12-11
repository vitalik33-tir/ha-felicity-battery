from __future__ import annotations
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEVICE_TYPE_BATTERY, DEVICE_TYPE_INVERTER


@dataclass
class FelicitySensorDescription:
    """Describes Felicity sensor metadata and how to extract its value."""

    key: str
    name: str
    icon: str | None = None
    native_unit_of_measurement: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None
    suggested_display_precision: int | None = None


BATTERY_SENSOR_DESCRIPTIONS: tuple[FelicitySensorDescription, ...] = (
    # --- Основные показатели батареи ---
    FelicitySensorDescription(
        key="soc",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    FelicitySensorDescription(
        key="pack_voltage",
        name="Battery Pack Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        suggested_display_precision=2,
    ),
    FelicitySensorDescription(
        key="pack_current",
        name="Battery Pack Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        suggested_display_precision=1,
    ),
    FelicitySensorDescription(
        key="pack_power_charge",
        name="Battery Charge Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    FelicitySensorDescription(
        key="pack_power_discharge",
        name="Battery Discharge Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
    ),

    # --- Статус / флаги BMS ---
    FelicitySensorDescription(
        key="bms_fault",
        name="BMS Fault Code",
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="bms_warning",
        name="BMS Warning Code",
        icon="mdi:alert-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # --- Температуры батареи ---
    FelicitySensorDescription(
        key="temp_1",
        name="Battery Temp 1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="temp_2",
        name="Battery Temp 2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="temp_3",
        name="Battery Temp 3",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="temp_4",
        name="Battery Temp 4",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),

    # --- Максимальные/минимальные значения ---
    FelicitySensorDescription(
        key="cell_max_voltage",
        name="Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-positive",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=3,
    ),
    FelicitySensorDescription(
        key="cell_min_voltage",
        name="Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-negative",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=3,
    ),
    FelicitySensorDescription(
        key="cell_max_index",
        name="Max Cell Index",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_min_index",
        name="Min Cell Index",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # --- Напряжение по ячейкам 1-16 ---
    FelicitySensorDescription(
        key="cell_1_v",
        name="Cell 1 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_2_v",
        name="Cell 2 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_3_v",
        name="Cell 3 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_4_v",
        name="Cell 4 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_5_v",
        name="Cell 5 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_6_v",
        name="Cell 6 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_7_v",
        name="Cell 7 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_8_v",
        name="Cell 8 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_9_v",
        name="Cell 9 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_10_v",
        name="Cell 10 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_11_v",
        name="Cell 11 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_12_v",
        name="Cell 12 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_13_v",
        name="Cell 13 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_14_v",
        name="Cell 14 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_15_v",
        name="Cell 15 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="cell_16_v",
        name="Cell 16 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # --- Лимиты по фактическим данным ---
    FelicitySensorDescription(
        key="max_charge_current",
        name="Max Charge Current (runtime)",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="max_discharge_current",
        name="Max Discharge Current (runtime)",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="runtime_min_voltage",
        name="Min Runtime Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="runtime_max_voltage",
        name="Max Runtime Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

INVERTER_SENSOR_DESCRIPTIONS: tuple[FelicitySensorDescription, ...] = (
    # --- Inverter runtime / status sensors ---
    FelicitySensorDescription(
        key="inverter_work_mode",
        name="Inverter Work Mode",
        icon="mdi:state-machine",
    ),
    FelicitySensorDescription(
        key="inverter_fault_code",
        name="Inverter Fault Code",
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="inverter_warning_code",
        name="Inverter Warning Code",
        icon="mdi:alert-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicitySensorDescription(
        key="inverter_load_percent",
        name="Inverter Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
    ),
    FelicitySensorDescription(
        key="inverter_bus_voltage",
        name="DC Bus Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="inverter_batt_voltage",
        name="Inverter Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    FelicitySensorDescription(
        key="inverter_batt_current",
        name="Inverter Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="inverter_batt_soc",
        name="Inverter Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
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
    device_type: str = data.get("device_type", DEVICE_TYPE_BATTERY)

    if device_type == DEVICE_TYPE_INVERTER:
        descriptions = INVERTER_SENSOR_DESCRIPTIONS
    else:
        descriptions = BATTERY_SENSOR_DESCRIPTIONS

    entities: list[FelicitySensor] = [
        FelicitySensor(coordinator, entry, desc) for desc in descriptions
    ]
    async_add_entities(entities)


class FelicitySensor(CoordinatorEntity, SensorEntity):
    """Representation of a single Felicity sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: FelicitySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_native_unit_of_measurement = (
            description.native_unit_of_measurement
        )
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_entity_category = description.entity_category
        self._suggested_display_precision = description.suggested_display_precision

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info to group entities into one device."""
        data = self.coordinator.data or {}
        serial = data.get("DevSN") or data.get("wifiSN") or self._entry.entry_id
        basic = data.get("_basic") or {}
        sw_version = basic.get("version")
        host = self._entry.data.get(CONF_HOST)
        serial_display = f"{serial} (IP {host})" if host else serial

        return {
            "identifiers": {(DOMAIN, serial)},
            "name": self._entry.data.get("name", "Felicity Battery"),
            "manufacturer": "Felicity",
            "model": "FLA48200",
            "sw_version": sw_version,
            "serial_number": serial_display,
        }

    @property
    def native_value(self) -> Any:
        """Return the value reported by the sensor."""
        data = self.coordinator.data or {}
        key = self.entity_description.key

        def get_nested(path: tuple[Any, ...]) -> Any:
            cur: Any = data
            for p in path:
                if isinstance(cur, dict):
                    cur = cur.get(p)
                elif isinstance(cur, list) and isinstance(p, int):
                    if 0 <= p < len(cur):
                        cur = cur[p]
                    else:
                        return None
                else:
                    return None
            return cur

        # --- Inverter-specific telemetry ---
        if key == "inverter_work_mode":
            # Raw inverter work mode code from payload (Type-specific decoding can be added later)
            return data.get("workM")

        if key == "inverter_fault_code":
            # Raw inverter fault code bitmask/value
            return data.get("fault")

        if key == "inverter_warning_code":
            # Raw inverter warning code bitmask/value
            return data.get("warn")

        if key == "inverter_load_percent":
            raw = data.get("lPerc")
            return raw if isinstance(raw, (int, float)) else None

        if key == "inverter_bus_voltage":
            raw = data.get("busVp")
            if not isinstance(raw, (int, float)):
                return None
            # Typically reported in 0.1 V units, e.g. 3944 -> 394.4 V
            return round(raw / 10.0, 1)

        if key == "inverter_batt_voltage":
            raw = get_nested(("Batt", 0, 0))
            return round(raw / 1000.0, 2) if isinstance(raw, (int, float)) else None

        if key == "inverter_batt_current":
            raw = get_nested(("Batt", 1, 0))
            return round(raw / 10.0, 1) if isinstance(raw, (int, float)) else None

        if key == "inverter_batt_soc":
            raw = get_nested(("Batsoc", 0, 0))
            return round(raw / 100.0, 1) if isinstance(raw, (int, float)) else None

        # --- Runtime telemetry ---
        if key == "soc":
            raw = get_nested(("Batsoc", 0, 0))
            return round(raw / 100.0, 1) if isinstance(raw, (int, float)) else None

        if key == "pack_voltage":
            raw = get_nested(("Batt", 0, 0))
            return round(raw / 1000.0, 2) if isinstance(raw, (int, float)) else None

        if key == "pack_current":
            raw = get_nested(("Batt", 1, 0))
            return round(raw / 10.0, 1) if isinstance(raw, (int, float)) else None

        if key == "pack_power_charge":
            raw = get_nested(("Batt", 2, 0))
            return raw if isinstance(raw, (int, float)) else None

        if key == "pack_power_discharge":
            raw = get_nested(("Batt", 2, 1))
            return raw if isinstance(raw, (int, float)) else None

        if key == "bms_fault":
            return data.get("Bfault")

        if key == "bms_warning":
            return data.get("Bwarn")

        # Temps: BTemp [[t1,t2,t3,t4,...]] in 0.1 °C
        if key.startswith("temp_"):
            try:
                idx = int(key.split("_", 1)[1]) - 1
            except Exception:
                return None
            temps = get_nested(("BTemp", 0))
            if isinstance(temps, list) and 0 <= idx < len(temps):
                raw = temps[idx]
                return round(raw / 10.0, 1) if isinstance(raw, (int, float)) else None
            return None

        # Max/min voltage and indices
        if key == "cell_max_voltage":
            raw = get_nested(("BMaxMin", 0, 0))
            return round(raw / 1000.0, 3) if isinstance(raw, (int, float)) else None

        if key == "cell_min_voltage":
            raw = get_nested(("BMaxMin", 0, 1))
            return round(raw / 1000.0, 3) if isinstance(raw, (int, float)) else None

        if key == "cell_max_index":
            return get_nested(("BMaxMin", 1, 0))

        if key == "cell_min_index":
            return get_nested(("BMaxMin", 1, 1))

        # Cell voltages from BatcelList [[c1,c2,...]]
        if key.startswith("cell_") and key.endswith("_v"):
            try:
                idx = int(key.split("_", 1)[1].split("_")[0]) - 1
            except Exception:
                return None
            cells = get_nested(("BatcelList", 0))
            if isinstance(cells, list) and 0 <= idx < len(cells):
                raw = cells[idx]
                return round(raw / 1000.0, 3) if isinstance(raw, (int, float)) else None
            return None

        # Limits from runtime (LVolCur)
        if key == "max_charge_current":
            raw = get_nested(("LVolCur", 1, 0))
            return round(raw / 10.0, 1) if isinstance(raw, (int, float)) else None

        if key == "max_discharge_current":
            raw = get_nested(("LVolCur", 1, 1))
            return round(raw / 10.0, 1) if isinstance(raw, (int, float)) else None

        if key == "runtime_min_voltage":
            raw = get_nested(("LVolCur", 0, 1))
            return round(raw / 100.0, 2) if isinstance(raw, (int, float)) else None

        if key == "runtime_max_voltage":
            raw = get_nested(("LVolCur", 0, 0))
            return round(raw / 100.0, 2) if isinstance(raw, (int, float)) else None

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes for some sensors."""
        data = self.coordinator.data or {}
        key = self.entity_description.key

        if key in {
            "ttl_pack",
            "cell_v_80",
            "cell_v_20",
            "cell_over_voltage",
            "cell_under_voltage",
            "charge_limit_setting",
            "discharge_limit_setting",
        }:
            settings = data.get("_settings")
            if isinstance(settings, dict):
                return settings
            return None

        return None
