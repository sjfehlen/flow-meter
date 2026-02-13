"""Constants for the Menstrual Cycle Tracker integration."""

DOMAIN = "menstrual_cycle_tracker"

# Services
SERVICE_LOG_PERIOD_START = "log_period_start"
SERVICE_LOG_PERIOD_END = "log_period_end"
SERVICE_LOG_SYMPTOM = "log_symptom"
SERVICE_EDIT_CYCLE = "edit_cycle"
SERVICE_DELETE_CYCLE = "delete_cycle"
SERVICE_DELETE_SYMPTOM = "delete_symptom"

# Phase names
PHASE_MENSTRUAL = "Menstrual"
PHASE_FOLLICULAR = "Follicular"
PHASE_OVULATION = "Ovulation"
PHASE_LUTEAL = "Luteal"
PHASE_UNKNOWN = "Unknown"

# Attribute keys
ATTR_DAYS_ACTIVE = "days_active"
ATTR_LAST_PERIOD_START = "last_period_start"
ATTR_LAST_PERIOD_END = "last_period_end"
ATTR_DAYS_UNTIL_NEXT = "days_until_next_period"
ATTR_DAYS_OVERDUE = "days_overdue"
ATTR_DAYS_PERIOD_END_OVERDUE = "days_period_end_overdue"
ATTR_DAYS_LEFT_OF_PERIOD = "days_left_of_period"
ATTR_IS_PMS_WINDOW = "is_pms_window"
ATTR_CYCLE_DAY = "cycle_day"

# Dispatcher signals
SIGNAL_UPDATE = f"{DOMAIN}_update"

# Default values
DEFAULT_CYCLE_LENGTH = 28
DEFAULT_PERIOD_LENGTH = 5

# Storage
STORAGE_VERSION = 1
