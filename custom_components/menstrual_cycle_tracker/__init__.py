"""Menstrual Cycle Tracker integration for Home Assistant."""
from __future__ import annotations

import logging
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_IS_PMS_WINDOW,
    DEFAULT_CYCLE_LENGTH,
    DEFAULT_PERIOD_LENGTH,
    DOMAIN,
    PHASE_FOLLICULAR,
    PHASE_LUTEAL,
    PHASE_MENSTRUAL,
    PHASE_OVULATION,
    PHASE_UNKNOWN,
    SERVICE_LOG_PERIOD_END,
    SERVICE_LOG_PERIOD_START,
    SERVICE_LOG_SYMPTOM,
    SIGNAL_UPDATE,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

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


def _install_blueprints(hass: HomeAssistant) -> None:
    """Copy bundled blueprints to /config/blueprints/automation/ if not present."""
    src_dir = Path(__file__).parent / "blueprints"
    dst_dir = Path(hass.config.config_dir) / "blueprints" / "automation" / DOMAIN
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src_file in src_dir.glob("*.yaml"):
        dst_file = dst_dir / src_file.name
        if not dst_file.exists():
            shutil.copy2(src_file, dst_file)
            _LOGGER.info("Installed blueprint: %s", dst_file)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Menstrual Cycle Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await hass.async_add_executor_job(_install_blueprints, hass)

    cycle_data = CycleData(hass, entry)
    await cycle_data.async_load()
    hass.data[DOMAIN][entry.entry_id] = cycle_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services once globally; subsequent entries reuse the same handlers.
    if not hass.services.has_service(DOMAIN, SERVICE_LOG_PERIOD_START):
        _register_services(hass)

    return True


def _resolve_tracker(hass: HomeAssistant, call: ServiceCall) -> tuple[CycleData | None, str | None]:
    """Return (CycleData, entry_id) for the targeted tracker, or (None, None) on error."""
    trackers: dict[str, tuple[str, CycleData]] = {}
    for eid, cd in hass.data[DOMAIN].items():
        config_entry = hass.config_entries.async_get_entry(eid)
        if config_entry:
            name = config_entry.data.get("name", eid).lower()
            trackers[name] = (eid, cd)

    requested = call.data.get("tracker", "").strip().lower()

    if requested:
        if requested not in trackers:
            available = ", ".join(trackers.keys()) or "none"
            _LOGGER.error(
                "Tracker '%s' not found. Available trackers: %s", requested, available
            )
            return None, None
        eid, cd = trackers[requested]
        return cd, eid

    if len(trackers) == 1:
        eid, cd = next(iter(trackers.values()))
        return cd, eid

    available = ", ".join(trackers.keys())
    _LOGGER.error(
        "Multiple trackers configured (%s). Specify 'tracker' in the service call.", available
    )
    return None, None


def _register_services(hass: HomeAssistant) -> None:
    """Register domain services (called once when the first entry loads)."""

    async def handle_log_period_start(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        date_str = call.data.get("date", date.today().strftime("%d/%m/%y"))
        try:
            period_date = datetime.strptime(date_str, "%d/%m/%y").date()
        except ValueError:
            _LOGGER.error("Invalid date format: %s. Use DD/MM/YY (e.g. 12/02/26).", date_str)
            return
        await cd.log_period_start(period_date)
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{eid}")

    async def handle_log_period_end(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        date_str = call.data.get("date", date.today().strftime("%d/%m/%y"))
        try:
            period_date = datetime.strptime(date_str, "%d/%m/%y").date()
        except ValueError:
            _LOGGER.error("Invalid date format: %s. Use DD/MM/YY (e.g. 12/02/26).", date_str)
            return
        await cd.log_period_end(period_date)
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{eid}")

    async def handle_log_symptom(call: ServiceCall) -> None:
        cd, eid = _resolve_tracker(hass, call)
        if cd is None:
            return
        date_str = call.data.get("date", date.today().strftime("%d/%m/%y"))
        try:
            symptom_date = datetime.strptime(date_str, "%d/%m/%y").date()
        except ValueError:
            _LOGGER.error("Invalid date format: %s. Use DD/MM/YY (e.g. 12/02/26).", date_str)
            return
        await cd.log_symptom(
            symptom_date,
            call.data["symptom"],
            call.data.get("severity", ""),
        )

    hass.services.async_register(
        DOMAIN, SERVICE_LOG_PERIOD_START, handle_log_period_start, schema=SERVICE_LOG_PERIOD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_LOG_PERIOD_END, handle_log_period_end, schema=SERVICE_LOG_PERIOD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_LOG_SYMPTOM, handle_log_symptom, schema=SERVICE_LOG_SYMPTOM_SCHEMA
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Only remove services when the last tracker is unloaded.
        if not hass.data[DOMAIN]:
            for service in [SERVICE_LOG_PERIOD_START, SERVICE_LOG_PERIOD_END, SERVICE_LOG_SYMPTOM]:
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
        """Calculate average cycle length from last 3 completed cycles."""
        completed = self.completed_cycles
        if len(completed) < 2:
            return DEFAULT_CYCLE_LENGTH
        # Need at least 2 cycles to compute a cycle length (gap between starts)
        starts = []
        for c in completed:
            try:
                starts.append(datetime.strptime(c["start_date"], "%Y-%m-%d").date())
            except (ValueError, KeyError):
                continue
        starts.sort()
        if len(starts) < 2:
            return DEFAULT_CYCLE_LENGTH
        # Use last 3 intervals
        intervals = [
            (starts[i + 1] - starts[i]).days for i in range(len(starts) - 1)
        ]
        recent = intervals[-3:]
        return round(sum(recent) / len(recent))

    @property
    def average_period_length(self) -> int:
        """Calculate average period length from completed cycles."""
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
        return round(sum(lengths) / len(lengths))

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
        """Predict the next future period start date."""
        start = self.last_period_start
        if not start:
            return None
        cycle_len = self.average_cycle_length
        predicted = start + timedelta(days=cycle_len)
        today = date.today()
        while predicted <= today:
            predicted += timedelta(days=cycle_len)
        return predicted

    @property
    def days_until_next_period(self) -> int | None:
        """Return days until predicted next period."""
        next_period = self.next_period_date
        if not next_period:
            return None
        return (next_period - date.today()).days

    @property
    def is_period_active(self) -> bool:
        """Return True if a period is currently active."""
        start = self.last_period_start
        if not start:
            return False
        # If last cycle has no end, period is active
        if self.cycles and not self.cycles[-1].get("end_date"):
            return True
        # Or if end date is today or in the future for the last cycle
        end = self.last_period_end
        if end and start <= date.today() <= end:
            return True
        return False

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
    def symptoms_today(self) -> list[dict[str, str]]:
        """Return symptoms logged today."""
        today = date.today().isoformat()
        return [s for s in self.symptoms if s.get("date") == today]
