# Build and Release

## Local Build

From the repository root:

```powershell
.\scripts\build.ps1
```

The script:

1. Creates `.venv` if needed.
2. Installs `requirements-dev.txt`.
3. Regenerates `assets\app.ico` and `assets\favicon.ico`.
4. Runs PyInstaller with `--onefile`, `--windowed`, and the app icon.

Output:

```text
dist\MW2CampaignConfigurator.exe
```

## Tests

```powershell
.\.venv\Scripts\python -m pytest .\tests
```

Smoke test without opening a visible window:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python -c "import sys; sys.path.insert(0, 'src'); from PyQt6.QtWidgets import QApplication; from mw2_campaign_configurator import QtConfiguratorWindow; app=QApplication([]); w=QtConfiguratorWindow(); print(w.status_label.text()); w.close(); app.quit()"
```

The offscreen smoke test may print a Qt font warning in this local environment. That warning is not currently blocking.

## Release Checklist

1. Ensure `git status -sb` is clean or contains only intended changes.
2. Run tests.
3. Run `.\scripts\build.ps1`.
4. Generate the SHA256 checksum for the release executable:
   ```powershell
   Get-FileHash .\dist\MW2CampaignConfigurator.exe -Algorithm SHA256
   ```
5. Commit and push.
6. Create a GitHub release, pasting the SHA256 hash in the release description:
   ```powershell
   gh release create vX.Y.Z .\dist\MW2CampaignConfigurator.exe --title "vX.Y.Z" --notes "Release notes here with SHA256."
   ```

## Version Notes

- `v0.1.0`: initial Tkinter release.
- `v0.1.1`: upscaler filtering and white panel fix.
- `v0.2.0`: PyQt6 dark-mode UI, native mouse-wheel scrolling, tree subcategories, Normal/Advanced modes, sliders.
- `v0.2.1`: unified FSR/CAS/XeSS/DLSS upscaler selector, cleaner Normal-mode labels, and hidden Source column in Normal mode.
- `v0.2.2`: Windows display mode dropdowns, simplified header, and read-only aware file lock toggle.
- `v0.2.3`: startup home screen, direct lock/unlock actions, and save success toast with locked-file error handling.
- `v0.3.0`: clearer first-run and missing-profile onboarding states on the home screen, save button state reflecting lock status, unsaved changes tracking with prompts, "Reset Selected" action for individual settings, and "Open Backups" explorer link.
