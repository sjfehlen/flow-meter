"""Binary sensors for the Menstrual Cycle Tracker integration."""
from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_DAYS_ACTIVE,
    ATTR_DAYS_LEFT_OF_PERIOD,
    ATTR_DAYS_PERIOD_END_OVERDUE,
    ATTR_LAST_PERIOD_END,
    ATTR_LAST_PERIOD_START,
    DOMAIN,
    SIGNAL_UPDATE,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    cycle_data = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get("name", "Cycle Tracker")
    async_add_entities([PeriodActiveSensor(cycle_data, entry, name)])


class PeriodActiveSensor(BinarySensorEntity):
    """Binary sensor indicating if a period is currently active."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:water"

    def __init__(self, cycle_data: Any, entry: ConfigEntry, tracker_name: str) -> None:
        """Initialize the binary sensor."""
        self._cycle_data = cycle_data
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_period_active"
        self._attr_name = "Period Active"
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

    @property
    def is_on(self) -> bool:
        return self._cycle_data.is_period_active

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        start = self._cycle_data.last_period_start
        end = self._cycle_data.last_period_end
        days_active = None
        if start and self._cycle_data.is_period_active:
            days_active = (date.today() - start).days + 1
        return {
            ATTR_DAYS_ACTIVE: days_active,
            ATTR_LAST_PERIOD_START: start.isoformat() if start else None,
            ATTR_LAST_PERIOD_END: end.isoformat() if end else None,
            ATTR_DAYS_PERIOD_END_OVERDUE: self._cycle_data.days_period_end_overdue,
            ATTR_DAYS_LEFT_OF_PERIOD: self._cycle_data.days_left_of_period,
        }
