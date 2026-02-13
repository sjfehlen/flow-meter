"""Menstrual Cycle Tracker integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_DAYS_OVERDUE,
    ATTR_IS_PMS_WINDOW,
    DEFAULT_CYCLE_LENGTH,
    DEFAULT_PERIOD_LENGTH,
    DOMAIN,
    PHASE_FOLLICULAR,
    PHASE_LUTEAL,
    PHASE_MENSTRUAL,
    PHASE_OVULATION,
    PHASE_UNKNOWN,
    SERVICE_DELETE_CYCLE,
    SERVICE_DELETE_SYMPTOM,
    SERVICE_EDIT_CYCLE,
    SERVICE_LOG_PERIOD_END,
    SERVICE_LOG_PERIOD_START,
    SERVICE_LOG_SYMPTOM,
    SIGNAL_UPDATE,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR]

SERVICE_LOG_PERIOD_SCHEMA = vol.Schema(
    {
        vol.Optional("tracker"): cv.string,
        vol.Optional("date"): cv.string,
    }
)

SERVICE_LOG_SYMPTOM_SCHEMA = vol.Schema(
    {
        vol.Optional("tracker"): cv.string,
        vol.Required("symptom"): cv.string,
        vol.Optional("severity"): vol.In(["mild", "moderate", "severe"]),
        vol.Optional("date"): cv.string,
    }
)

SERVICE_EDIT_CYCLE_SCHEMA = vol.Schema(
    {
        vol.Optional("tracker"): cv.string,
        vol.Required("original_start_date"): cv.string,
        vol.Optional("new_start_date"): cv.string,
        vol.Optional("new_end_date"): cv.string,
    }
)

SERVICE_DELETE_CYCLE_SCHEMA = vol.Schema(
    {
        vol.Optional("tracker"): cv.string,
        vol.Required("start_date"): cv.string,
    }
)

SERVICE_DELETE_SYMPTOM_SCHEMA = vol.Schema(
    {
        vol.Optional("tracker"): cv.string,
        vol.Required("date"): cv.string,
        vol.Required("symptom"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Menstrual Cycle Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    cycle_data = CycleData(hass, entry)
    await cycle_data.async_load()
    hass.data[DOMAIN][entry.entry_id] = cycle_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services once globally; subsequent entries reuse the same handlers.
    if not hass.services.has_service(DOMAIN, SERVICE_LOG_PERIOD_START):
        _register_services(hass)

    return True


def _resolve_tracker(hass: HomeAssistant, call: ServiceCall) -> tuple[CycleData | None, str | None]:
    """Return (CycleData, entry_id) for the targeted tracker, or (None, None) on error.

    The 'tracker' field accepts either an entry_id (from the config_entry selector)
    or a tracker name string (for use in automations/scripts).
    """
    loaded: dict[str, CycleData] = hass.data[DOMAIN]
    requested = call.data.get("tracker", "").strip()

    if requested:
        # 1. Direct entry_id match (config_entry selector returns entry_id)
        if requested in loaded:
            return loaded[requested], requested
        # 2. Name match (case-insensitive, for automations using plain text)
        for eid, cd in loaded.items():
            config_entry = hass.config_entries.async_get_entry(eid)
            if config_entry and config_entry.data.get("name", "").lower() == requested.lower():
                return cd, eid
        available = ", ".join(
            hass.config_entries.async_get_entry(e).data.get("name", e)
            for e in loaded
            if hass.config_entries.async_get_entry(e)
        )
        _LOGGER.error(
            "Tracker '%s' not found. Available trackers: %s", requested, available or "none"
        )
        return None, None

    if len(loaded) == 1:
        eid = next(iter(loaded))
        return loaded[eid], eid

    available = ", ".join(
        hass.config_entries.async_get_entry(e).data.get("name", e)
        for e in loaded
        if hass.config_entries.async_get_entry(e)
    )
    _LOGGER.error(
        "Multiple trackers configured (%s). Select a tracker in the service call.", available
    )
    return None, None


def _register_services(hass: HomeAssistant) -> None:
    """Register domain services (called once when the first entry loads)."""

    async def handle_log_period_start(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        date_str = call.data.get("date", date.today().strftime("%m/%d/%y"))
        try:
            period_date = datetime.strptime(date_str, "%m/%d/%y").date()
        except ValueError:
            _LOGGER.error("Invalid date format: %s. Use MM/DD/YY (e.g. 02/12/26).", date_str)
            return
        await cd.log_period_start(period_date)
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{eid}")

    async def handle_log_period_end(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        date_str = call.data.get("date", date.today().strftime("%m/%d/%y"))
        try:
            period_date = datetime.strptime(date_str, "%m/%d/%y").date()
        except ValueError:
            _LOGGER.error("Invalid date format: %s. Use MM/DD/YY (e.g. 02/12/26).", date_str)
            return
        await cd.log_period_end(period_date)
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{eid}")

    async def handle_log_symptom(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        date_str = call.data.get("date", date.today().strftime("%m/%d/%y"))
        try:
            symptom_date = datetime.strptime(date_str, "%m/%d/%y").date()
        except ValueError:
            _LOGGER.error("Invalid date format: %s. Use MM/DD/YY (e.g. 02/12/26).", date_str)
            return
        await cd.log_symptom(
            symptom_date,
            call.data["symptom"],
            call.data.get("severity", ""),
        )
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{eid}")

    async def handle_edit_cycle(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        try:
            original = datetime.strptime(call.data["original_start_date"], "%m/%d/%y").date()
        except ValueError:
            _LOGGER.error(
                "Invalid original_start_date: %s. Use MM/DD/YY.", call.data["original_start_date"]
            )
            return
        new_start = None
        new_end = None
        if "new_start_date" in call.data:
            try:
                new_start = datetime.strptime(call.data["new_start_date"], "%m/%d/%y").date()
            except ValueError:
                _LOGGER.error("Invalid new_start_date: %s. Use MM/DD/YY.", call.data["new_start_date"])
                return
        if "new_end_date" in call.data:
            try:
                new_end = datetime.strptime(call.data["new_end_date"], "%m/%d/%y").date()
            except ValueError:
                _LOGGER.error("Invalid new_end_date: %s. Use MM/DD/YY.", call.data["new_end_date"])
                return
        if not await cd.edit_cycle(original, new_start, new_end):
            _LOGGER.warning("No cycle found with start date %s.", original.isoformat())
            return
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{eid}")

    async def handle_delete_cycle(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        try:
            start = datetime.strptime(call.data["start_date"], "%m/%d/%y").date()
        except ValueError:
            _LOGGER.error("Invalid start_date: %s. Use MM/DD/YY.", call.data["start_date"])
            return
        if not await cd.delete_cycle(start):
            _LOGGER.warning("No cycle found with start date %s.", start.isoformat())
            return
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{eid}")

    async def handle_delete_symptom(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        try:
            symptom_date = datetime.strptime(call.data["date"], "%m/%d/%y").date()
        except ValueError:
            _LOGGER.error("Invalid date: %s. Use MM/DD/YY.", call.data["date"])
            return
        if not await cd.delete_symptom(symptom_date, call.data["symptom"]):
            _LOGGER.warning(
                "No symptom '%s' found on %s.", call.data["symptom"], symptom_date.isoformat()
            )
            return
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{eid}")

    hass.services.async_register(
        DOMAIN, SERVICE_LOG_PERIOD_START, handle_log_period_start, schema=SERVICE_LOG_PERIOD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_LOG_PERIOD_END, handle_log_period_end, schema=SERVICE_LOG_PERIOD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_LOG_SYMPTOM, handle_log_symptom, schema=SERVICE_LOG_SYMPTOM_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_EDIT_CYCLE, handle_edit_cycle, schema=SERVICE_EDIT_CYCLE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_CYCLE, handle_delete_cycle, schema=SERVICE_DELETE_CYCLE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_SYMPTOM, handle_delete_symptom, schema=SERVICE_DELETE_SYMPTOM_SCHEMA
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Only remove services when the last tracker is unloaded.
        if not hass.data[DOMAIN]:
            for service in [
                SERVICE_LOG_PERIOD_START, SERVICE_LOG_PERIOD_END, SERVICE_LOG_SYMPTOM,
                SERVICE_EDIT_CYCLE, SERVICE_DELETE_CYCLE, SERVICE_DELETE_SYMPTOM,
            ]:
                hass.services.async_remove(DOMAIN, service)
    return unload_ok


class CycleData:
    """Class to manage cycle data storage and calculations."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize cycle data."""
        self.hass = hass
        self.entry = entry
        self._store = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.cycles.{entry.entry_id}",
        )
        self.cycles: list[dict[str, str]] = []
        self.symptoms: list[dict[str, str]] = []

    async def async_load(self) -> None:
        """Load data from storage."""
        stored = await self._store.async_load()
        if stored:
            self.cycles = stored.get("cycles", [])
            self.symptoms = stored.get("symptoms", [])
        else:
            # Load initial cycles from config entry data
            initial_cycles = self.entry.data.get("initial_cycles", [])
            self.cycles = initial_cycles
            await self._async_save()

    async def _async_save(self) -> None:
        """Save data to storage."""
        await self._store.async_save(
            {"cycles": self.cycles, "symptoms": self.symptoms}
        )

    async def log_period_start(self, period_date: date) -> None:
        """Log the start of a period."""
        date_str = period_date.isoformat()
        # Check if we already have an open cycle (start without end)
        for cycle in reversed(self.cycles):
            if cycle.get("start_date") == date_str:
                return  # Already logged
            if not cycle.get("end_date"):
                cycle["start_date"] = date_str
                await self._async_save()
                return
        # Add new cycle
        self.cycles.append({"start_date": date_str, "end_date": ""})
        await self._async_save()

    async def log_period_end(self, period_date: date) -> None:
        """Log the end of a period."""
        date_str = period_date.isoformat()
        for cycle in reversed(self.cycles):
            if not cycle.get("end_date"):
                cycle["end_date"] = date_str
                await self._async_save()
                return
        _LOGGER.warning("No open period found to close. Log period start first.")

    async def log_symptom(self, symptom_date: date, symptom: str, severity: str) -> None:
        """Log a symptom."""
        self.symptoms.append(
            {
                "date": symptom_date.isoformat(),
                "symptom": symptom,
                "severity": severity,
            }
        )
        await self._async_save()

    async def edit_cycle(
        self, original_start: date, new_start: date | None, new_end: date | None
    ) -> bool:
        """Edit an existing cycle identified by its original start date.

        Returns True if the cycle was found and updated.
        """
        target = original_start.isoformat()
        for cycle in self.cycles:
            if cycle.get("start_date") == target:
                if new_start is not None:
                    cycle["start_date"] = new_start.isoformat()
                if new_end is not None:
                    cycle["end_date"] = new_end.isoformat()
                await self._async_save()
                return True
        return False

    async def delete_cycle(self, start: date) -> bool:
        """Delete a cycle identified by its start date.

        Returns True if the cycle was found and removed.
        """
        target = start.isoformat()
        for i, cycle in enumerate(self.cycles):
            if cycle.get("start_date") == target:
                self.cycles.pop(i)
                await self._async_save()
                return True
        return False

    async def delete_symptom(self, symptom_date: date, symptom: str) -> bool:
        """Delete a symptom matching the date and name.

        Removes the first matching entry. Returns True if found.
        """
        target_date = symptom_date.isoformat()
        for i, s in enumerate(self.symptoms):
            if s.get("date") == target_date and s.get("symptom") == symptom:
                self.symptoms.pop(i)
                await self._async_save()
                return True
        return False

    @property
    def completed_cycles(self) -> list[dict[str, str]]:
        """Return only cycles with both start and end dates."""
        return [c for c in self.cycles if c.get("start_date") and c.get("end_date")]

    @property
    def last_period_start(self) -> date | None:
        """Return the most recent period start date."""
        if not self.cycles:
            return None
        last = self.cycles[-1]
        start = last.get("start_date")
        if start:
            return datetime.strptime(start, "%Y-%m-%d").date()
        return None

    @property
    def last_period_end(self) -> date | None:
        """Return the most recent period end date."""
        for cycle in reversed(self.cycles):
            end = cycle.get("end_date")
            if end:
                return datetime.strptime(end, "%Y-%m-%d").date()
        return None

    @property
    def average_cycle_length(self) -> int:
        """Calculate average cycle length from last 3 cycle intervals.

        Uses all cycles with a start date (not just completed ones) because
        cycle length is the interval between consecutive start dates and does
        not require an end date.
        """
        starts = []
        for c in self.cycles:
            s = c.get("start_date")
            if s:
                try:
                    starts.append(datetime.strptime(s, "%Y-%m-%d").date())
                except ValueError:
                    continue
        starts.sort()
        if len(starts) < 2:
            return DEFAULT_CYCLE_LENGTH
        intervals = [
            (starts[i + 1] - starts[i]).days for i in range(len(starts) - 1)
        ]
        recent = intervals[-3:]
        return round(sum(recent) / len(recent))

    @property
    def average_period_length(self) -> int:
        """Calculate average period length from last 3 completed cycles."""
        completed = self.completed_cycles
        if not completed:
            return DEFAULT_PERIOD_LENGTH
        lengths = []
        for c in completed:
            try:
                start = datetime.strptime(c["start_date"], "%Y-%m-%d").date()
                end = datetime.strptime(c["end_date"], "%Y-%m-%d").date()
                lengths.append((end - start).days + 1)
            except (ValueError, KeyError):
                continue
        if not lengths:
            return DEFAULT_PERIOD_LENGTH
        recent = lengths[-3:]
        return round(sum(recent) / len(recent))

    @property
    def current_cycle_day(self) -> int | None:
        """Return current day within the predicted cycle (1-indexed, wraps with cycle length)."""
        start = self.last_period_start
        if not start:
            return None
        cycle_len = self.average_cycle_length
        days_since = (date.today() - start).days
        return (days_since % cycle_len) + 1

    @property
    def next_period_date(self) -> date | None:
        """Return the current predicted period start date.

        Uses the same algorithm as days_overdue so both always refer to the
        same cycle. The returned date may be in the past when the period is
        overdue; use days_overdue to know how many days late it is.
        """
        start = self.last_period_start
        if not start:
            return None
        cycle_len = self.average_cycle_length
        predicted = start + timedelta(days=cycle_len)
        today = date.today()
        # Advance until the NEXT prediction would still be in the future,
        # leaving predicted at the current cycle's expected start date.
        while predicted + timedelta(days=cycle_len) <= today:
            predicted += timedelta(days=cycle_len)
        return predicted

    @property
    def days_until_next_period(self) -> int | None:
        """Days until (positive) or since (negative) the predicted period start."""
        next_period = self.next_period_date
        if not next_period:
            return None
        return (next_period - date.today()).days

    @property
    def is_period_active(self) -> bool:
        """Return True if a period is currently active (started but not yet ended)."""
        if not self.cycles:
            return False
        last = self.cycles[-1]
        return bool(last.get("start_date")) and not last.get("end_date")

    @property
    def current_phase(self) -> str:
        """Return the current cycle phase."""
        cycle_day = self.current_cycle_day
        if cycle_day is None:
            return PHASE_UNKNOWN
        period_len = self.average_period_length
        cycle_len = self.average_cycle_length
        ovulation_day = cycle_len - 14

        if cycle_day <= period_len:
            return PHASE_MENSTRUAL
        if cycle_day < ovulation_day - 1:
            return PHASE_FOLLICULAR
        if cycle_day <= ovulation_day + 2:
            return PHASE_OVULATION
        return PHASE_LUTEAL

    @property
    def is_fertile_window(self) -> bool:
        """Return True if currently in fertile window."""
        return self.current_phase == PHASE_OVULATION

    @property
    def is_pms_window(self) -> bool:
        """Return True if in PMS window (last 5 days before period)."""
        days_until = self.days_until_next_period
        if days_until is None:
            return False
        return 0 <= days_until <= 5

    @property
    def days_overdue(self) -> int:
        """Days past the predicted period start.

        Returns -1 if the period is active or the predicted date is still in
        the future. Returns 0 if today is the expected start day, positive N
        if the period is N days late.
        """
        if self.is_period_active:
            return -1
        next_period = self.next_period_date
        if not next_period:
            return -1
        delta = (date.today() - next_period).days
        return delta if delta >= 0 else -1

    @property
    def days_period_end_overdue(self) -> int:
        """Days since expected period end based on average period length.

        Returns -1 if no period is active.
        Returns 0 if today is the expected last day.
        Returns positive N if period is N days past expected length.
        Returns negative N if N days remain before expected end.
        """
        if not self.is_period_active:
            return -1
        start = self.last_period_start
        if not start:
            return -1
        days_active = (date.today() - start).days + 1
        return days_active - self.average_period_length

    @property
    def days_left_of_period(self) -> int | None:
        """Days remaining until expected period end.

        Returns a positive integer while the period is active and before
        the expected end date. Returns None once the period has reached or
        passed its expected length, or when no period is active.
        """
        overdue = self.days_period_end_overdue
        if overdue >= 0:
            return None
        return -overdue

    @property
    def symptoms_today(self) -> list[dict[str, str]]:
        """Return symptoms logged today."""
        today = date.today().isoformat()
        return [s for s in self.symptoms if s.get("date") == today]
