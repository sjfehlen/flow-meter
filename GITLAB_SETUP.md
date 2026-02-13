# Setting Up Your GitLab Repository for HACS

This guide shows you how to publish this integration on GitLab and make it available through HACS.

## Step 1: Create GitLab Repository

1. **Go to GitLab.com** (or your GitLab instance)
2. **Create new project**
   - Click "New project"
   - Choose "Create blank project"
   - Name: `menstrual-cycle-tracker`
   - Visibility: Public (required for HACS)
   - Initialize with README: No (we have our own)

## Step 2: Push Code to GitLab

```bash
# Navigate to the project directory
cd hacs-menstrual-cycle-tracker

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - Menstrual Cycle Tracker v2.0.0"

# Add GitLab remote (replace with your URL)
git remote add origin https://gitlab.com/yourusername/menstrual-cycle-tracker.git

# Push to GitLab
git push -u origin main
```

## Step 3: Create a Release/Tag

HACS requires at least one release/tag.

### Via GitLab UI:
1. Go to your repository on GitLab
2. Navigate to **Repository → Tags**
3. Click **New tag**
4. Tag name: `v2.0.0`
5. Message: `Version 2.0.0 - Initial HACS release`
6. Click **Create tag**

### Via Command Line:
```bash
git tag -a v2.0.0 -m "Version 2.0.0 - Initial HACS release"
git push origin v2.0.0
```

## Step 4: Verify Repository Structure

Your GitLab repository should look like this:

```
menstrual-cycle-tracker/
├── custom_components/
│   └── menstrual_cycle_tracker/
│       ├── __init__.py
│       ├── binary_sensor.py
│       ├── config_flow.py
│       ├── const.py
│       ├── manifest.json
│       ├── sensor.py
│       ├── services.yaml
│       └── strings.json
├── .gitignore
├── .gitlab-ci.yml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── hacs.json
└── info.md
```

## Step 5: Add to HACS

### For Personal Use (Custom Repository):

1. **Open Home Assistant**
2. **Go to HACS → Integrations**
3. **Click three dots (⋮) → Custom repositories**
4. **Add your repository:**
   - URL: `https://gitlab.com/yourusername/menstrual-cycle-tracker`
   - Category: Integration
   - Click **Add**

5. **Find and install:**
   - Search for "Menstrual Cycle Tracker"
   - Click **Download**
   - Restart Home Assistant

### For Public HACS (Submit to HACS):

To get your integration listed in the official HACS store:

1. **Ensure quality standards:**
   - [ ] Working integration with no errors
   - [ ] Proper documentation (README.md)
   - [ ] Valid hacs.json file
   - [ ] At least one release/tag
   - [ ] MIT or compatible license

2. **Fork HACS default repository:**
   - Go to https://github.com/hacs/default
   - Click Fork

3. **Add your repository:**
   - Edit `integration.json` (for GitLab integrations)
   - Add your repository info:
     ```json
     {
       "name": "Menstrual Cycle Tracker",
       "domain": "menstrual_cycle",
       "description": "Privacy-focused menstrual cycle tracking",
       "gitlab": "yourusername/menstrual-cycle-tracker"
     }
     ```

4. **Create Pull Request:**
   - Submit PR to HACS default repository
   - Wait for review and approval

## Step 6: Maintaining Your Repository

### Creating New Releases:

When you make updates:

1. **Update version in manifest.json:**
   ```json
   {
     "version": "2.1.0"
   }
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [2.1.0] - 2026-03-15
   
   ### Added
   - New feature X
   
   ### Fixed
   - Bug Y
   ```

3. **Commit changes:**
   ```bash
   git add .
   git commit -m "Update: Version 2.1.0 - Add feature X"
   git push
   ```

4. **Create new tag:**
   ```bash
   git tag -a v2.1.0 -m "Version 2.1.0"
   git push origin v2.1.0
   ```

### GitLab CI/CD:

The included `.gitlab-ci.yml` will automatically:
- Validate JSON files
- Check Python syntax
- Run linting (optional)

This runs on every merge request and push to main.

## Step 7: Repository Settings

### Enable Issues:
1. Go to **Settings → General → Visibility**
2. Enable **Issues**
3. Save changes

### Enable Merge Requests:
1. Go to **Settings → General → Merge requests**
2. Configure as desired
3. Save changes

### Protected Branches:
1. Go to **Settings → Repository → Protected branches**
2. Protect `main` branch
3. Allow maintainers to push

## Troubleshooting

### HACS can't find my repository:
- Ensure repository is **Public**
- Check that `hacs.json` exists in root
- Verify at least one release/tag exists
- Wait a few minutes for GitLab to index

### Integration doesn't show up after adding:
- Check Home Assistant logs for errors
- Verify `manifest.json` has correct domain
- Ensure `custom_components/menstrual_cycle_tracker/` structure is correct
- Restart Home Assistant

### Updates not appearing:
- Create a new release/tag
- Wait for HACS to check for updates (or force check)
- Clear HACS cache if needed

## Example Repository URLs

Replace these with your actual URLs in:
- `hacs.json` (if using repository URL)
- `manifest.json` (documentation and issue_tracker)
- `README.md` (links)
- `info.md` (links)

```
https://gitlab.com/yourusername/menstrual-cycle-tracker
https://gitlab.com/yourusername/menstrual-cycle-tracker/-/issues
https://gitlab.com/yourusername/menstrual-cycle-tracker/-/discussions
```

## Next Steps

1. ✅ Create GitLab repository
2. ✅ Push code
3. ✅ Create first release (v2.0.0)
4. ✅ Test installation via HACS custom repository
5. ✅ Fix any issues
6. ✅ Consider submitting to official HACS
7. ✅ Engage with community
8. ✅ Maintain and improve!

---

**Your integration is now ready to share with the Home Assistant community!** 🎉

## Resources

- [HACS Documentation](https://hacs.xyz/)
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [GitLab CI/CD Docs](https://docs.gitlab.com/ee/ci/)
- [Home Assistant Community](https://community.home-assistant.io/)
