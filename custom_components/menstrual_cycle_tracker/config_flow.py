"""Config flow for Menstrual Cycle Tracker."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _validate_date(date_str: str) -> bool:
    """Return True if date_str is a valid DD/MM/YY date."""
    if not date_str:
        return True
    try:
        datetime.strptime(date_str, "%d/%m/%y")
        return True
    except ValueError:
        return False


def _to_iso(date_str: str) -> str:
    """Convert DD/MM/YY to YYYY-MM-DD for internal storage."""
    return datetime.strptime(date_str, "%d/%m/%y").strftime("%Y-%m-%d")


class MenstrualCycleTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Menstrual Cycle Tracker."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._name: str = ""
        self._initial_cycles: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - name the tracker."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._name = user_input["name"]
            return await self.async_step_cycle1()

        schema = vol.Schema(
            {
                vol.Required("name", default="My Cycle"): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_cycle1(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle most recent cycle entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            start = user_input.get("start_date", "").strip()
            end = user_input.get("end_date", "").strip()

            if start and not _validate_date(start):
                errors["start_date"] = "invalid_date"
            elif end and not _validate_date(end):
                errors["end_date"] = "invalid_date"
            else:
                if start:
                    self._initial_cycles.append(
                        {"start_date": _to_iso(start), "end_date": _to_iso(end) if end else ""}
                    )
                return await self.async_step_cycle2()

        schema = vol.Schema(
            {
                vol.Optional("start_date", default=""): str,
                vol.Optional("end_date", default=""): str,
            }
        )
        return self.async_show_form(
            step_id="cycle1",
            data_schema=schema,
            errors=errors,
            description_placeholders={"cycle_num": "1 (most recent)"},
        )

    async def async_step_cycle2(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle second most recent cycle entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            start = user_input.get("start_date", "").strip()
            end = user_input.get("end_date", "").strip()

            if start and not _validate_date(start):
                errors["start_date"] = "invalid_date"
            elif end and not _validate_date(end):
                errors["end_date"] = "invalid_date"
            else:
                if start:
                    self._initial_cycles.append(
                        {"start_date": _to_iso(start), "end_date": _to_iso(end) if end else ""}
                    )
                return await self.async_step_cycle3()

        schema = vol.Schema(
            {
                vol.Optional("start_date", default=""): str,
                vol.Optional("end_date", default=""): str,
            }
        )
        return self.async_show_form(
            step_id="cycle2",
            data_schema=schema,
            errors=errors,
            description_placeholders={"cycle_num": "2"},
        )

    async def async_step_cycle3(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle third most recent cycle entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            start = user_input.get("start_date", "").strip()
            end = user_input.get("end_date", "").strip()

            if start and not _validate_date(start):
                errors["start_date"] = "invalid_date"
            elif end and not _validate_date(end):
                errors["end_date"] = "invalid_date"
            else:
                if start:
                    self._initial_cycles.append(
                        {"start_date": _to_iso(start), "end_date": _to_iso(end) if end else ""}
                    )
                # Sort cycles by start date descending (most recent first)
                self._initial_cycles.sort(
                    key=lambda c: c["start_date"], reverse=True
                )
                return self.async_create_entry(
                    title=self._name,
                    data={
                        "name": self._name,
                        "initial_cycles": self._initial_cycles,
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional("start_date", default=""): str,
                vol.Optional("end_date", default=""): str,
            }
        )
        return self.async_show_form(
            step_id="cycle3",
            data_schema=schema,
            errors=errors,
            description_placeholders={"cycle_num": "3 (oldest)"},
        )
