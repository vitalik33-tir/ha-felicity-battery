from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTemperature,
    PERCENTAGE,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FelicityDataUpdateCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: FelicityDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    def add_sensor(name, key, scale=1.0, unit=None, device_class=None, icon=None):
        entities.append(
            FelicitySensor(
                coordinator,
                name,
                key,
                scale=scale,
                unit=unit,
                device_class=device_class,
                icon=icon,
            )
        )

    # _basic
    add_sensor("Device SN", "DevSN", icon="mdi:identifier")
    add_sensor("WiFi SN", "wifiSN", icon="mdi:wifi")

    # _settings
    add_sensor("Battery Pack Count", "ttl_pack", icon="mdi:counter", unit="шт")
    add_sensor("Cell Over Voltage", "cell_over_voltage", scale=0.001, unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE)
    add_sensor("Cell Under Voltage", "cell_under_voltage", scale=0.001, unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE)
    add_sensor("Cell Voltage @20%", "cell_v_20", scale=0.001, unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE)
    add_sensor("Cell Voltage @80%", "cell_v_80", scale=0.001, unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE)
    add_sensor("Charge Current Limit (setting)", "charge_limit_setting", scale=0.1, unit=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT)
    add_sensor("Discharge Current Limit (setting)", "discharge_limit_setting", scale=0.1, unit=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT)

    # _real
    add_sensor("SOC (%)", "soc", scale=0.01, unit=PERCENTAGE)
    add_sensor("Battery Voltage", "voltage", scale=0.01, unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE)
    add_sensor("Battery Current", "current", scale=0.1, unit=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT)
    add_sensor("Max Cell Voltage", "cell_v_max", scale=0.001, unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE)
    add_sensor("Min Cell Voltage", "cell_v_min", scale=0.001, unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE)
    add_sensor("Max Temp", "temp_max", scale=0.1, unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE)
    add_sensor("Min Temp", "temp_min", scale=0.1, unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE)

    # Список ячеек
    cell_list = coordinator.data.get("BatcelList", [[]])[0]
    for i, val in enumerate(cell_list):
        key = f"cell_{i+1:02}"
        add_sensor(f"Cell {i+1:02}", key, scale=0.001, unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE)

    async_add_entities(entities)


class FelicitySensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: FelicityDataUpdateCoordinator,
        name: str,
        key: str,
        scale: float = 1.0,
        unit: str | None = None,
        device_class: SensorDeviceClass | None = None,
        icon: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._scale = scale
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = f"{coordinator.base_unique_id}_{key}"

    @property
    def native_value(self):
        # Определяем, из какого раздела брать ключ
        data = self.coordinator.data
        val = None

        if self._key in data.get("_settings", {}):
            val = data["_settings"].get(self._key)
        elif self._key in data.get("_basic", {}):
            val = data["_basic"].get(self._key)
        elif self._key in data:
            val = data.get(self._key)
        elif self._key.startswith("cell_"):
            index = int(self._key.replace("cell_", ""))
            try:
                val = data.get("BatcelList", [[]])[0][index - 1]
            except Exception:
                val = None

        if val is None:
            return None
        try:
            return round(float(val) * self._scale, 3)
        except Exception:
            return None
