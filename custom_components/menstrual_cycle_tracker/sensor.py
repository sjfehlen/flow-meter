"""Sensors for the Menstrual Cycle Tracker integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_DAYS_OVERDUE,
    ATTR_DAYS_UNTIL_NEXT,
    ATTR_IS_PMS_WINDOW,
    DOMAIN,
    SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    cycle_data = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get("name", "Cycle Tracker")

    async_add_entities(
        [
            CurrentPhaseSensor(cycle_data, entry, name),
            CycleDaySensor(cycle_data, entry, name),
            NextPeriodSensor(cycle_data, entry, name),
            PeriodLengthSensor(cycle_data, entry, name),
            CycleLengthSensor(cycle_data, entry, name),
            FertileWindowSensor(cycle_data, entry, name),
            TodaysSymptomsSensor(cycle_data, entry, name),
        ]
    )


class CycleTrackerSensorBase(SensorEntity):
    """Base class for cycle tracker sensors."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        """Initialize the sensor."""
        self._cycle_data = cycle_data
        self._entry = entry
        self._tracker_name = tracker_name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=tracker_name,
            manufacturer="Custom",
            model="Menstrual Cycle Tracker",
            sw_version="2.0.0",
        )

    async def async_added_to_hass(self) -> None:
        """Register dispatcher."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_UPDATE}_{self._entry.entry_id}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        """Handle update signal."""
        self.async_write_ha_state()


class CurrentPhaseSensor(CycleTrackerSensorBase):
    """Sensor for current cycle phase."""

    _attr_icon = "mdi:calendar-heart"

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        super().__init__(cycle_data, entry, tracker_name)
        self._attr_unique_id = f"{entry.entry_id}_current_phase"
        self._attr_name = "Current Phase"

    @property
    def native_value(self) -> str:
        return self._cycle_data.current_phase


class CycleDaySensor(CycleTrackerSensorBase):
    """Sensor for current cycle day."""

    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "day"

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        super().__init__(cycle_data, entry, tracker_name)
        self._attr_unique_id = f"{entry.entry_id}_cycle_day"
        self._attr_name = "Cycle Day"

    @property
    def native_value(self) -> int | None:
        return self._cycle_data.current_cycle_day


class NextPeriodSensor(CycleTrackerSensorBase):
    """Sensor for predicted next period date."""

    _attr_icon = "mdi:calendar-clock"

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        super().__init__(cycle_data, entry, tracker_name)
        self._attr_unique_id = f"{entry.entry_id}_next_period"
        self._attr_name = "Next Period"

    @property
    def native_value(self) -> str | None:
        next_period = self._cycle_data.next_period_date
        if next_period is None:
            return None
        return next_period.strftime("%m/%d/%y")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_DAYS_UNTIL_NEXT: self._cycle_data.days_until_next_period,
            ATTR_DAYS_OVERDUE: self._cycle_data.days_overdue,
        }


class PeriodLengthSensor(CycleTrackerSensorBase):
    """Sensor for average period length."""

    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "days"

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        super().__init__(cycle_data, entry, tracker_name)
        self._attr_unique_id = f"{entry.entry_id}_period_length"
        self._attr_name = "Period Length"

    @property
    def native_value(self) -> int:
        return self._cycle_data.average_period_length


class CycleLengthSensor(CycleTrackerSensorBase):
    """Sensor for average cycle length."""

    _attr_icon = "mdi:calendar-range"
    _attr_native_unit_of_measurement = "days"

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        super().__init__(cycle_data, entry, tracker_name)
        self._attr_unique_id = f"{entry.entry_id}_cycle_length"
        self._attr_name = "Cycle Length"

    @property
    def native_value(self) -> int:
        return self._cycle_data.average_cycle_length


class FertileWindowSensor(CycleTrackerSensorBase):
    """Sensor for fertile window status."""

    _attr_icon = "mdi:flower"

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        super().__init__(cycle_data, entry, tracker_name)
        self._attr_unique_id = f"{entry.entry_id}_fertile_window"
        self._attr_name = "Fertile Window"

    @property
    def native_value(self) -> str:
        return "Yes" if self._cycle_data.is_fertile_window else "No"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {ATTR_IS_PMS_WINDOW: self._cycle_data.is_pms_window}


class TodaysSymptomsSensor(CycleTrackerSensorBase):
    """Sensor showing symptoms logged today."""

    _attr_icon = "mdi:clipboard-pulse"
    _attr_native_unit_of_measurement = "symptoms"

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        super().__init__(cycle_data, entry, tracker_name)
        self._attr_unique_id = f"{entry.entry_id}_todays_symptoms"
        self._attr_name = "Today's Symptoms"

    @property
    def native_value(self) -> int:
        return len(self._cycle_data.symptoms_today)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"symptoms": self._cycle_data.symptoms_today}
