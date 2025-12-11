from __future__ import annotations
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Порог разброса напряжений между ячейками, В
CELL_DRIFT_HIGH_THRESHOLD_V = 0.03


@dataclass
class FelicityBinarySensorDescription(BinarySensorEntityDescription):
    """Extended description for Felicity binary sensors."""


BINARY_SENSOR_DESCRIPTIONS: tuple[FelicityBinarySensorDescription, ...] = (
    FelicityBinarySensorDescription(
        key="fault_active",
        name="Battery Fault Active",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicityBinarySensorDescription(
        key="warning_active",
        name="Battery Warning Active",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicityBinarySensorDescription(
        key="charging",
        name="Battery Charging",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    FelicityBinarySensorDescription(
        key="discharging",
        name="Battery Discharging",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    FelicityBinarySensorDescription(
        key="standby",
        name="Battery Standby",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicityBinarySensorDescription(
        key="cell_drift_high",
        name="Cell Voltage Drift High",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Felicity binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = [FelicityBinarySensor(coordinator, entry, desc) for desc in BINARY_SENSOR_DESCRIPTIONS]
    async_add_entities(entities)


class FelicityBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Felicity binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: FelicityBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for grouping."""
        data = self.coordinator.data or {}
        serial = data.get("DevSN") or data.get("wifiSN") or self._entry.entry_id
        basic = data.get("_basic") or {}
        sw_version = basic.get("version")

        return {
            "identifiers": {(DOMAIN, serial)},
            "name": self._entry.data.get("name", "Felicity Battery"),
            "manufacturer": "Felicity",
            "model": "FLA48200",
            "sw_version": sw_version,
            "serial_number": serial,
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if condition is active."""
        data: dict = self.coordinator.data or {}
        key = self.entity_description.key

        def get_nested(path: tuple[Any, ...]):
            cur = data
            try:
                for p in path:
                    cur = cur[p]
                return cur
            except Exception:
                return None

        try:
            if key == "fault_active":
                v = data.get("Bfault")
                return v is not None and int(v) != 0

            if key == "warning_active":
                v = data.get("Bwarn")
                return v is not None and int(v) != 0

            estate = data.get("Estate")
            if key == "charging":
                if estate == 9152:
                    return True
                i_raw = get_nested(("Batt", 1, 0))
                return (i_raw / 10.0) > 0.05 if i_raw is not None else None

            if key == "discharging":
                if estate == 5056:
                    return True
                i_raw = get_nested(("Batt", 1, 0))
                return (i_raw / 10.0) < -0.05 if i_raw is not None else None

            if key == "standby":
                if estate in (960, 320):
                    return True
                i_raw = get_nested(("Batt", 1, 0))
                return abs(i_raw / 10.0) <= 0.05 if i_raw is not None else None

            if key == "cell_drift_high":
                max_raw = get_nested(("BMaxMin", 0, 0))
                min_raw = get_nested(("BMaxMin", 0, 1))
                if max_raw is None or min_raw is None:
                    return None
                drift_v = (max_raw - min_raw) / 1000.0
                return drift_v > CELL_DRIFT_HIGH_THRESHOLD_V

        except Exception as e:
            _LOGGER.warning("Error in binary sensor %s: %s", key, e)
            return None

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Extra diagnostic info."""
        data: dict = self.coordinator.data or {}
        key = self.entity_description.key

        if key == "cell_drift_high":
            bmaxmin = data.get("BMaxMin")
            if (
                isinstance(bmaxmin, list)
                and bmaxmin
                and isinstance(bmaxmin[0], list)
                and len(bmaxmin[0]) >= 2
            ):
                max_raw = bmaxmin[0][0]
                min_raw = bmaxmin[0][1]
                drift_v = (max_raw - min_raw) / 1000.0
                return {
                    "drift_v": round(drift_v, 3),
                    "threshold_v": CELL_DRIFT_HIGH_THRESHOLD_V,
                }

        return None
