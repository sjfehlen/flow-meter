# Menstrual Cycle Tracker for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

A privacy-focused Home Assistant integration for tracking menstrual cycles with adaptive prediction algorithms.

> **Your data stays on YOUR device** - No cloud, no external servers, complete privacy.

---

## ✨ Key Features

- 📊 **Adaptive Predictions** - Uses rolling averages of your last 3 cycles (not generic 28-day predictions)
- 🔒 **100% Privacy** - All data stored locally in Home Assistant
- 📱 **Easy Logging** - Simple services to track periods and symptoms
- 🎯 **Phase Tracking** - Menstrual, Follicular, Ovulation, Luteal phases
- 🏠 **Full Automation** - Integrate with lights, climate, notifications
- ⚡ **Real-time Updates** - Entities update instantly when you log data
- 🔔 **Binary Sensor** - Period Active status for automations

---

## 📊 How Many Cycles Do You Need?

| Cycles | Accuracy | Status |
|--------|----------|--------|
| **0** | N/A | Can start logging |
| **1** | ±5 days | Basic tracking |
| **2** | ±3 days | Simple predictions |
| **3** | ±1-2 days | **Recommended** ⭐ |
| **6+** | <1 day | Optimal |

**Bottom line:** Start with what you have! Works with 0 cycles, excellent with 3, optimal with 6+.

---

## 🚀 Installation

### HACS (Recommended)

1. **Add this repository to HACS:**
   - Open HACS in Home Assistant
   - Click on "Integrations"
   - Click the three dots in the top right
   - Select "Custom repositories"
   - Add this repository URL
   - Select "Integration" as the category
   - Click "Add"

2. **Install the integration:**
   - Search for "Menstrual Cycle Tracker"
   - Click "Download"
   - Restart Home Assistant

3. **Add the integration:**
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "Menstrual Cycle Tracker"
   - Follow the setup wizard

### Manual Installation

1. Copy the `custom_components/menstrual_cycle_tracker` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration → "Menstrual Cycle Tracker"

---

## ⚙️ Setup Wizard

### Step 1: Name Your Tracker
Give it a friendly name (e.g., "My Cycle" or "Cycle Tracker")

### Step 2: Add Initial Data (Optional)

For best results, enter your last **3 cycles** during setup:

```
Cycle 1 (Most Recent):
  Start: 2026-02-02
  End: 2026-02-06

Cycle 2:
  Start: 2026-01-05
  End: 2026-01-10

Cycle 3:
  Start: 2025-12-09
  End: 2025-12-14
```

**Why 3 cycles?**
- Medical standard (3 months tracking)
- Rolling average algorithm kicks in
- ±1-2 day accuracy from day one
- You can skip this and add data later!

**Date format:** YYYY-MM-DD

---

## 📊 Entities Created

The integration creates a device with these entities:

### Binary Sensor
- **`binary_sensor.cycle_tracker_period_active`**
  - State: On/Off (is period happening now?)
  - Perfect for automations

### Sensors
- **`sensor.cycle_tracker_current_phase`**
  - States: Menstrual, Follicular, Ovulation, Luteal
  
- **`sensor.cycle_tracker_cycle_day`**
  - Value: Current day in cycle (1, 2, 3...)
  
- **`sensor.cycle_tracker_next_period`**
  - Value: Predicted next period date
  - Attribute: days_until_next_period
  
- **`sensor.cycle_tracker_period_length`**
  - Value: Average period length in days
  
- **`sensor.cycle_tracker_cycle_length`**
  - Value: Average cycle length in days
  
- **`sensor.cycle_tracker_fertile_window`**
  - States: Yes/No
  - Attribute: is_pms_window

---

## 🎮 Services

### Log Period Start
```yaml
service: menstrual_cycle.log_period_start
data:
  date: "2026-02-02"  # Optional, defaults to today
```

### Log Period End
```yaml
service: menstrual_cycle.log_period_end
data:
  date: "2026-02-06"  # Optional, defaults to today
```

### Log Symptom
```yaml
service: menstrual_cycle.log_symptom
data:
  symptom: "cramps"
  severity: "moderate"  # Optional: mild, moderate, severe
  date: "2026-02-02"    # Optional, defaults to today
```

---

## 🤖 Quick Automation Examples

### One-Tap Logging Buttons

```yaml
# configuration.yaml
input_button:
  period_started:
    name: Period Started
    icon: mdi:calendar-heart
  period_ended:
    name: Period Ended
    icon: mdi:check-circle

# automations.yaml
automation:
  - alias: "Log Period Start"
    trigger:
      - platform: state
        entity_id: input_button.period_started
    action:
      - service: menstrual_cycle.log_period_start
      - service: notify.mobile_app
        data:
          message: "Period logged! 💪"

  - alias: "Log Period End"
    trigger:
      - platform: state
        entity_id: input_button.period_ended
    action:
      - service: menstrual_cycle.log_period_end
```

### Period Alert (2 Days Before)

```yaml
automation:
  - alias: "Period Alert"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.cycle_tracker_current_phase', 'days_until_next_period') == 2 }}
    action:
      - service: notify.mobile_app
        data:
          title: "🩸 Period Alert"
          message: "Your period is predicted to start in 2 days"
```

### Comfort Lighting During Period

```yaml
automation:
  - alias: "Comfort Lighting"
    trigger:
      - platform: state
        entity_id: binary_sensor.cycle_tracker_period_active
        to: "on"
    condition:
      - condition: sun
        after: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.bedroom
        data:
          brightness_pct: 30
          kelvin: 2700
```

### Fertile Window Alert

```yaml
automation:
  - alias: "Fertile Window"
    trigger:
      - platform: state
        entity_id: sensor.cycle_tracker_fertile_window
        to: "Yes"
    action:
      - service: notify.mobile_app
        data:
          title: "🥚 Fertility Update"
          message: "You've entered your fertile window!"
```

---

## 📱 Dashboard Example

```yaml
type: entities
title: 🌸 Cycle Tracker
entities:
  - entity: binary_sensor.cycle_tracker_period_active
    name: Period Active
  - entity: sensor.cycle_tracker_current_phase
    name: Current Phase
  - entity: sensor.cycle_tracker_cycle_day
    name: Cycle Day
  - entity: sensor.cycle_tracker_next_period
    name: Next Period
  - entity: sensor.cycle_tracker_fertile_window
    name: Fertile Window
```

---

## 🧮 How It Works

### Adaptive Rolling Average Algorithm

Instead of using a generic 28-day cycle:

1. **Looks at your last 3 cycles**
   ```
   Example: 27, 28, 26 days
   ```

2. **Calculates average**
   ```
   (27 + 28 + 26) / 3 = 27 days
   ```

3. **Predicts next period**
   ```
   Last period: Feb 2
   Add 27 days = Mar 1
   ```

4. **Adapts continuously**
   - Each new cycle updates the average
   - Outliers automatically filtered
   - Gets more accurate over time

### Phase Tracking

- **Menstrual** (Days 1-6): Period active
- **Follicular** (Days 7-13): Between period end and ovulation
- **Ovulation** (Days 13-16): Fertile window
- **Luteal** (Days 16-27): After ovulation until next period

---

## 🔒 Privacy & Data

**Your data NEVER leaves your device:**
- ✅ Stored locally in Home Assistant
- ✅ No cloud services
- ✅ No external servers
- ✅ No analytics or tracking
- ✅ You own and control everything

**Data location:**
```
/config/.storage/menstrual_cycle.cycles.[entry_id]
```

**Data format:**
```json
{
  "cycles": [
    {"start_date": "2026-02-02", "end_date": "2026-02-06"}
  ],
  "symptoms": [
    {"date": "2026-02-02", "symptom": "cramps", "severity": "moderate"}
  ]
}
```

---

## ❓ FAQ

**Q: Can I track multiple people?**  
A: Yes! Add the integration multiple times with different names.

**Q: What if I don't remember my last 3 cycles?**  
A: Skip the initial data step and start logging from today. Predictions will improve after 2-3 cycles.

**Q: How accurate are predictions?**  
A: With 3+ cycles: typically ±1-2 days. Gets better with more data.

**Q: Does this work for irregular cycles?**  
A: Yes, but predictions will be less accurate. The algorithm adapts to your pattern.

**Q: Can I edit old data?**  
A: Currently manual via the JSON file. UI editing planned for future release.

**Q: Is this HIPAA compliant?**  
A: All data stays on your device, so there's no data transmission. However, consult a compliance expert for your specific use case.

---

## 🛠️ Troubleshooting

### Sensors show "Unknown"
- Log at least one period start date
- Check date format is YYYY-MM-DD
- Check logs: Settings → System → Logs

### Integration not loading
- Ensure all files are in `custom_components/menstrual_cycle_tracker/`
- Restart Home Assistant completely
- Check for errors in logs

### Entities not updating after logging
- This should update instantly in v2
- Try reloading the integration
- Check dispatcher is working (no errors in logs)

---

## 🗺️ Roadmap

- [ ] Edit historical cycles via service
- [ ] Import from CSV/JSON
- [ ] Statistics card with charts
- [ ] Symptom correlation tracking
- [ ] Multi-language support
- [ ] Google Calendar integration
- [ ] Apple Health export

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- Built for the Home Assistant community
- Algorithm based on medical cycle tracking standards
- Inspired by the need for privacy-focused period tracking

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/sjfehlen/flow-meter/issues)
- **Home Assistant Community:** [Forum Thread](https://community.home-assistant.io/)

---

**Made with ❤️ for privacy-conscious cycle tracking**

Track your cycle. Own your data. Automate your comfort.
