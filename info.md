# Menstrual Cycle Tracker

A privacy-focused Home Assistant integration for tracking menstrual cycles with adaptive prediction algorithms.

**Your data stays on YOUR device** - No cloud, no external servers, complete privacy.

## Features

- Adaptive predictions using your last 3 cycles (not generic 28-day estimates)
- 100% local storage in Home Assistant
- Easy logging via services
- Phase tracking: Menstrual, Follicular, Ovulation, Luteal
- Fertile window detection
- Real-time entity updates
- Period Active binary sensor for automations

## Entities Created

- `binary_sensor.[name]_period_active`
- `sensor.[name]_current_phase`
- `sensor.[name]_cycle_day`
- `sensor.[name]_next_period`
- `sensor.[name]_period_length`
- `sensor.[name]_cycle_length`
- `sensor.[name]_fertile_window`

## Quick Automation Example

```yaml
automation:
  - alias: "Period Alert"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.cycle_tracker_next_period', 'days_until_next_period') == 2 }}
    action:
      - service: notify.mobile_app
        data:
          title: "Period Alert"
          message: "Your period is predicted to start in 2 days"
```

## Issues

Report issues at: https://github.com/sjfehlen/flow-meter/issues
