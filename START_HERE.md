# 🚀 Start Here - Menstrual Cycle Tracker for Home Assistant

Welcome! This package contains everything you need to publish a HACS-compatible Home Assistant integration for menstrual cycle tracking.

## 📦 What's In This Package

```
hacs-menstrual-cycle-tracker/
├── custom_components/           ← The actual integration
│   └── menstrual_cycle_tracker/
│       ├── __init__.py
│       ├── binary_sensor.py
│       ├── config_flow.py
│       ├── const.py
│       ├── manifest.json
│       ├── sensor.py
│       ├── services.yaml
│       └── strings.json
├── .gitignore                   ← Git ignore file
├── .gitlab-ci.yml              ← GitLab CI/CD configuration
├── CHANGELOG.md                 ← Version history
├── CONTRIBUTING.md              ← Contribution guidelines
├── GITLAB_SETUP.md             ← Step-by-step GitLab setup
├── LICENSE                      ← MIT License
├── README.md                    ← Main documentation
├── hacs.json                    ← HACS configuration
└── info.md                      ← HACS display info
```

## 🎯 Quick Start (Choose Your Path)

### Path 1: Just Use It Locally (No GitLab)

**For personal use only:**

1. Copy `custom_components/menstrual_cycle_tracker/` to your Home Assistant:
   ```
   /config/custom_components/menstrual_cycle_tracker/
   ```

2. Restart Home Assistant

3. Add integration:
   - Settings → Devices & Services
   - Add Integration → "Menstrual Cycle Tracker"

**Done!** Skip the rest if you just want to use it.

---

### Path 2: Publish to GitLab + HACS (Share with Others)

**To make it available via HACS:**

1. **Create GitLab account** (if you don't have one)
   - Go to https://gitlab.com
   - Sign up (free)

2. **Create new GitLab project**
   - Name: `menstrual-cycle-tracker`
   - Visibility: **Public** (required for HACS)
   - Don't initialize with README

3. **Upload all these files to GitLab**
   
   **Option A - Command Line:**
   ```bash
   cd hacs-menstrual-cycle-tracker
   git init
   git add .
   git commit -m "Initial commit - v2.0.0"
   git remote add origin https://gitlab.com/YOUR_USERNAME/menstrual-cycle-tracker.git
   git push -u origin main
   ```

   **Option B - GitLab Web UI:**
   - Zip all files
   - Upload via GitLab web interface
   - Repository → Upload file

4. **Create a release tag**
   ```bash
   git tag -a v2.0.0 -m "Version 2.0.0"
   git push origin v2.0.0
   ```
   
   Or via GitLab UI:
   - Repository → Tags → New tag
   - Name: `v2.0.0`

5. **Add to HACS as custom repository**
   - Home Assistant → HACS → Integrations
   - Three dots (⋮) → Custom repositories
   - URL: `https://gitlab.com/YOUR_USERNAME/menstrual-cycle-tracker`
   - Category: Integration

6. **Install via HACS**
   - Search: "Menstrual Cycle Tracker"
   - Download
   - Restart Home Assistant

**Done!** Now anyone can install from your GitLab repo.

---

### Path 3: Submit to Official HACS (Public Distribution)

**To get listed in HACS default store:**

Follow Path 2 first, then:

1. Test thoroughly for several weeks
2. Ensure quality:
   - [ ] No errors in logs
   - [ ] All features working
   - [ ] Documentation complete
   - [ ] Multiple release tags

3. Submit to HACS:
   - Fork https://github.com/hacs/default
   - Add your repo to `integration.json`
   - Create Pull Request
   - Wait for approval

See [HACS Documentation](https://hacs.xyz/docs/publish/integration) for details.

---

## 📖 Documentation Guide

### For Users:
- **README.md** - Complete user guide (installation, features, automations)
- **info.md** - Quick overview shown in HACS

### For Contributors:
- **CONTRIBUTING.md** - How to contribute code
- **GITLAB_SETUP.md** - Detailed GitLab setup instructions

### For Maintenance:
- **CHANGELOG.md** - Track version changes
- **.gitlab-ci.yml** - Automated testing

## 🔧 Before Publishing

### ✅ Pre-flight Checklist

**Required:**
- [ ] Update URLs in files (replace `yourusername` with your GitLab username)
- [ ] Test integration works in Home Assistant
- [ ] All files are included
- [ ] LICENSE file present
- [ ] At least one git tag/release created

**Recommended:**
- [ ] Test with 0, 1, 2, and 3 cycles
- [ ] Verify all automations work
- [ ] Check for typos in documentation
- [ ] Test on fresh Home Assistant install

**URLs to Update:**

Search and replace `yourusername` with your GitLab username in:
- `README.md` (all links)
- `info.md` (issue link)
- `manifest.json` (documentation, issue_tracker)
- `GITLAB_SETUP.md` (example URLs)
- `CONTRIBUTING.md` (all links)

Example:
```
Find: yourusername
Replace: mackenzie-schneider
```

## 🎨 Customization (Optional)

### Change Integration Name:
1. Edit `manifest.json` → `"name"`
2. Edit `hacs.json` → `"name"`
3. Update README.md title

### Change Domain:
⚠️ **Not recommended** - Would require code changes throughout

### Add Features:
See `CONTRIBUTING.md` for development guidelines

## 📊 What Users Will Get

When someone installs this integration:

**Device Created:**
- "Menstrual Cycle Tracker" (or custom name)

**Entities:**
- `binary_sensor.cycle_tracker_period_active`
- `sensor.cycle_tracker_current_phase`
- `sensor.cycle_tracker_cycle_day`
- `sensor.cycle_tracker_next_period`
- `sensor.cycle_tracker_period_length`
- `sensor.cycle_tracker_cycle_length`
- `sensor.cycle_tracker_fertile_window`

**Services:**
- `menstrual_cycle.log_period_start`
- `menstrual_cycle.log_period_end`
- `menstrual_cycle.log_symptom`

## 🔒 Privacy Note

**Important selling point:**
- All data stays on user's device
- No cloud services
- No external servers
- No data transmission
- Complete privacy

Make sure to emphasize this in your repo description!

## 🐛 Troubleshooting

### "Integration not found in HACS"
- Repository must be Public
- Need at least one release tag
- Check `hacs.json` is valid JSON

### "Files not loading"
- Verify directory structure matches exactly
- Check all `.py` files are present
- Restart Home Assistant completely

### "Entities not appearing"
- Check Home Assistant logs
- Verify `manifest.json` domain matches const.py
- Try reloading integration

## 🆘 Getting Help

- **HACS Issues:** https://github.com/hacs/integration/issues
- **Home Assistant Community:** https://community.home-assistant.io/
- **Your Repository Issues:** Will be available after you create your GitLab repo

## 📅 Next Steps

1. **Now:** Choose your path (local use or publish)
2. **Today:** Set up GitLab repo (if publishing)
3. **This week:** Test thoroughly
4. **This month:** Gather feedback, improve
5. **Long term:** Maintain, add features, help users

## 🎉 You're Ready!

Everything is set up and ready to go. Choose your path and follow the steps above.

**Questions?** Check `GITLAB_SETUP.md` for detailed instructions.

---

**Made with ❤️ for privacy-conscious cycle tracking**

Good luck with your integration! 🌸
