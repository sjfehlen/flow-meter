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

# Cycle field prefixes for the 3 historical cycles
_CYCLE_FIELDS = [
    ("cycle1_start", "cycle1_end"),
    ("cycle2_start", "cycle2_end"),
    ("cycle3_start", "cycle3_end"),
]


class MenstrualCycleTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Menstrual Cycle Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the single-screen setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input["name"]

            # Validate and collect cycles
            initial_cycles: list[dict[str, str]] = []
            for start_key, end_key in _CYCLE_FIELDS:
                start = user_input.get(start_key, "")
                end = user_input.get(end_key, "")

                if end and not start:
                    errors[end_key] = "end_without_start"
                    continue

                if start and end:
                    start_dt = datetime.strptime(start, "%Y-%m-%d").date()
                    end_dt = datetime.strptime(end, "%Y-%m-%d").date()
                    if end_dt < start_dt:
                        errors[end_key] = "end_before_start"
                        continue

                if start:
                    initial_cycles.append({
                        "start_date": start,
                        "end_date": end or "",
                    })

            if not errors:
                # Sort ascending (oldest first) so cycles[-1] is the most
                # recent, matching the append behaviour of log_period_start.
                initial_cycles.sort(key=lambda c: c["start_date"])
                return self.async_create_entry(
                    title=name,
                    data={
                        "name": name,
                        "initial_cycles": initial_cycles,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required("name", default="My Cycle"): selector.TextSelector(),
                # Most recent cycle
                vol.Optional("cycle1_start"): selector.DateSelector(),
                vol.Optional("cycle1_end"): selector.DateSelector(),
                # Second most recent cycle
                vol.Optional("cycle2_start"): selector.DateSelector(),
                vol.Optional("cycle2_end"): selector.DateSelector(),
                # Third most recent cycle (oldest)
                vol.Optional("cycle3_start"): selector.DateSelector(),
                vol.Optional("cycle3_end"): selector.DateSelector(),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
