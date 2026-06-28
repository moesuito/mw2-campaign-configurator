# Build and Release

## Local Build

From the repository root:

```powershell
.\scripts\build.ps1
```

The script:

1. Creates `.venv` if needed.
2. Installs `requirements-dev.txt`.
3. Regenerates `assets\app.ico`.
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
4. Commit and push.
5. Create a GitHub release:

```powershell
gh release create vX.Y.Z .\dist\MW2CampaignConfigurator.exe --title "vX.Y.Z" --notes "Release notes here."
```

## Version Notes

- `v0.1.0`: initial Tkinter release.
- `v0.1.1`: upscaler filtering and white panel fix.
- `v0.2.0`: PyQt6 dark-mode UI, native mouse-wheel scrolling, tree subcategories, Normal/Advanced modes, sliders.
