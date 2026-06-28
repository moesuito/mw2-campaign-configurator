# Agent Handoff

This file is for future coding agents working on this repo.

## Current State

- Repo: `D:\Antigravity\mw2-campaign-configurator`
- GitHub: `https://github.com/moesuito/mw2-campaign-configurator`
- Main branch: `main`
- Current planned release: `v0.2.0`
- App framework: PyQt6
- Packaging: PyInstaller one-file portable executable

## User Preferences

- Keep the app in English.
- Keep original game option names/descriptions where they come from the files.
- UI should be dark mode.
- UI should stay inspired by BF4 Settings Editor, but not copy third-party branding.
- Prefer a practical, easy UI over exposing every raw config field by default.
- `Normal` mode should be global across all categories.
- `Advanced` mode should expose extra config fields from the readable files.
- Do not edit MP/BR/DMZ/CP files.
- Keep the executable portable for now.

## Important Implementation Details

- Files are read only on initial load, profile change, explicit reload, save, or restore.
- The UI re-renders cached `ConfigEntry` objects from RAM for category changes, search, mode changes, and AA/upscaler changes.
- `QTreeWidget` is used for the central settings view. Mouse-wheel scrolling should work natively.
- `SliderEditor` is used for practical ranged values and preserves numeric formatting on save.
- `NORMAL_MODE_KEYS` controls what appears in Normal mode.
- `entry_subcategory()` controls tree grouping.
- `should_use_slider()` controls whether a range becomes a slider.
- `UPSCALER_VISIBLE_KEYS` controls which subsettings appear for DLSS/XeSS/FSR/SMAA.
- `is_rtx_gpu_name()` currently checks for both `NVIDIA` and `RTX` in `GPUName:0.0`.

## Common Tasks

### Add a Normal-mode option

1. Confirm the key exists in a real config file.
2. Add the key to `NORMAL_MODE_KEYS`.
3. If needed, add or adjust grouping in `entry_subcategory()`.
4. Add a parser/classification test when behavior changes.

### Add slider support

1. Confirm the key has reliable `x to y` metadata.
2. Add it to `should_use_slider()` if the generic range logic does not pick it up.
3. Verify formatting is preserved through `format_number()`.

### Add upscaler logic

1. Add config keys to `UPSCALER_CONFIG_KEYS`.
2. Add visible keys under the matching technique in `UPSCALER_VISIBLE_KEYS`.
3. Add tests in `tests/test_config_parser.py`.

## Validation Commands

```powershell
.\.venv\Scripts\python -m pytest .\tests
.\.venv\Scripts\python -m py_compile .\src\mw2_campaign_configurator.py .\scripts\create_icon.py
```

PyQt offscreen smoke test:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python -c "import sys; sys.path.insert(0, 'src'); from PyQt6.QtWidgets import QApplication; from mw2_campaign_configurator import QtConfiguratorWindow; app=QApplication([]); w=QtConfiguratorWindow(); print(w.status_label.text()); w.close(); app.quit()"
```

## Release Notes Draft for v0.2.0

- Migrated from Tkinter to PyQt6.
- Added full dark-mode UI.
- Replaced the settings grid with a tree view and subcategories.
- Fixed mouse-wheel scrolling through native Qt widgets.
- Added global Normal/Advanced modes.
- Added sliders with numeric inputs for practical ranged settings.
- Kept cached config data in RAM during UI navigation.
