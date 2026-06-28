# Agent Handoff

This file is for future coding agents working on this repo.

## Current State

- Repo: `D:\Antigravity\mw2-campaign-configurator`
- GitHub: `https://github.com/moesuito/mw2-campaign-configurator`
- Main branch: `main`
- Current release target: `v0.3.0`
- App framework: PyQt6
- Packaging: PyInstaller one-file portable executable

## User Preferences

- Keep the app in English.
- Keep original game option names/descriptions where they come from the files.
- UI should be dark mode.
- UI should stay inspired by BF4 Settings Editor, but not copy third-party branding.
- Prefer a practical, easy UI over exposing every raw config field by default.
- `Normal` mode should be global across all categories.
- `Normal` mode should use polished labels and hide technical source paths.
- `Advanced` mode should expose extra config fields from the readable files.
- Do not edit MP/BR/DMZ/CP files.
- Keep the executable portable for now.

## Important Implementation Details

- Files are loaded on startup, profile change, explicit reload, save, or restore.
- The UI re-renders cached `ConfigEntry` objects from RAM for category changes, search, mode changes, and AA/upscaler changes.
- The app opens on a simple home screen. `current_section == ""` means no category is selected.
- `QTreeWidget` is used for the central settings view. Mouse-wheel scrolling should work natively.
- `SliderEditor` is used for practical ranged values and preserves numeric formatting on save.
- `discover_windows_displays()` uses Win32 display APIs to populate monitor, resolution, and refresh-rate dropdowns.
- The bottom-bar lock toggle uses the current read-only state of the loaded files:
  - `Unlock Files` when any loaded file is read-only.
  - `Lock Files` when every loaded file is writable.
- Lock/unlock does not show modal confirmation dialogs.
- `Save Settings` does not force chmod. It shows an error if any loaded file is read-only, saves only when all loaded files are writable, and uses a two-second toast for success.
- Empty or invalid game/profile states are shown in the home panel with direct guidance.
- `Save Settings` is disabled while files are read-only.
- Unsaved changes are tracked against the last loaded/saved baseline and prompt before reload/profile/folder changes.
- `Reset Selected` restores one selected option to the last loaded/saved value.
- `Open Backups` opens the portable backup folder.
- `NORMAL_MODE_KEYS` controls what appears in Normal mode.
- `NORMAL_LABELS` controls nicer Normal-mode labels.
- `entry_subcategory()` controls tree grouping.
- `should_use_slider()` controls whether a range becomes a slider.
- `UPSCALER_VISIBLE_KEYS` controls which subsettings appear for DLSS/XeSS/FSR/SMAA.
- `unified_aa_choices()` presents SMAA, DLSS, DLAA, XeSS, FSR 2.0, CAS, and AMD FSR 1.0 in one selector.
- `is_rtx_gpu_name()` currently checks for both `NVIDIA` and `RTX` in `GPUName:0.0`; only DLSS and DLAA are RTX-gated.

## v0.3.0 Implementation Notes

The v0.3.0 update focuses on first-run UX, safer save affordances, and user confidence around backups/changes. Keep the app portable, English-only, and scoped to campaign-effective files.

Implementation guardrails for this release:

- Keep changes mostly inside `src/mw2_campaign_configurator.py`; split files only if the refactor is clearly small and reduces risk.
- Do not rewrite the parser, metadata model, upscaler filtering, or display-mode discovery as part of this UX release.
- Preserve the current behavior where config files are loaded into `ConfigDocument` / `ConfigEntry` objects and UI navigation re-renders from RAM.
- Keep all user-facing text in English.
- Do not add network calls or telemetry.
- Do not add an installer.
- Update `README.md`, `docs/ARCHITECTURE.md`, `docs/BUILD_AND_RELEASE.md`, and this file if behavior changes.

### Task: Improve Empty States and Onboarding

When the app cannot find `Documents\Call of Duty MWII`, `players`, a numeric profile folder, or the required `.cst` files, the central home panel should explain what is missing and what the user can do next.

Relevant current code:

- `default_game_dir()` returns the initial `Documents\Call of Duty MWII` path.
- `discover_profiles(game_dir)` returns numeric profile folders containing `settings.3.local.cod22.cst`.
- `validate_game_dir(game_dir, profile)` raises if required files are missing.
- `QtConfiguratorWindow.reload_profiles()` handles no-profile cases.
- `QtConfiguratorWindow.load_documents()` handles missing-file exceptions after profile selection.
- `QtConfiguratorWindow.show_home_screen()` currently shows the neutral startup home.

Suggested implementation:

1. Change the home panel labels from static local variables to instance attributes, for example:
   - `self.home_title`
   - `self.home_copy`
2. Add a helper such as `set_home_message(title: str, copy: str) -> None`.
3. Keep `show_home_screen()` responsible only for showing/hiding panels and clearing option UI state.
4. In `reload_profiles()`:
   - If `players` does not exist, set a specific home message explaining that no MWII players folder was found.
   - If `players` exists but no valid numeric profile is found, set a specific home message explaining that the campaign may need to be launched once.
   - Keep `self.documents = []`, clear the profile combo, call `update_lock_button()`, and keep the sidebar empty.
5. In `load_documents()`:
   - For `FileNotFoundError` from `validate_game_dir()`, prefer a clear home-panel message plus concise status text.
   - Avoid a modal for normal missing required `.cst` files.
   - Keep modal errors for unexpected exceptions.
6. Avoid auto-selecting `Graphics`; startup and missing-state flows should keep `current_section == ""`.

Expected behavior:

1. If no valid profile is found, show a clear home-panel message such as `No campaign profile found`.
2. Include short guidance: launch the campaign once, close the game, then click `Reload` or use `Browse`.
3. Keep the bottom status text concise, but do not rely on the bottom bar as the only explanation.
4. Do not show noisy modal dialogs for normal first-run missing-folder/missing-profile cases.
5. Continue showing a modal only for unexpected or destructive-risk errors.

Acceptance checks:

- Fresh machine without `Documents\Call of Duty MWII` shows a useful center-panel message.
- Existing game folder without valid profile shows a useful center-panel message.
- Valid folder still opens on the neutral home screen with no category selected.
- Selecting a valid folder after an empty state repopulates profiles and returns to the neutral home screen.
- Missing `options.3.cod22.cst` or profile `settings.3.local.cod22.cst` is explained in the home panel without crashing.

### Task: Save and Lock State Affordances

Make save availability visually match the file lock state.

Relevant current code:

- The `Save Settings` button is currently local to `_build_ui()`.
- `self.lock_toggle_button` is already an instance attribute.
- `files_have_readonly()` returns whether any loaded document is read-only.
- `update_lock_button()` updates lock/unlock text and color.
- `save_all()` still contains a defensive locked-file error.
- `toggle_file_lock()` changes file attributes and then reloads documents.

Suggested implementation:

1. Store the save button as `self.save_button` instead of a local `save_settings` variable.
2. Add `update_save_button()` or fold save-state updates into a broader `update_action_buttons()`.
3. Call the update helper after:
   - `load_documents()`
   - no-profile path in `reload_profiles()`
   - `toggle_file_lock()`
   - successful save
   - restore backup
4. Recommended state:
   - no documents loaded: disabled
   - any loaded document read-only: disabled or visibly blocked
   - all loaded documents writable: enabled
5. Keep the explicit `save_all()` read-only check even if the button is disabled. It protects against shortcut/focus/edge cases.
6. If using a disabled button, make sure the user still understands the fix:
   - lock button should show `Unlock Files`
   - bottom status should include `Options: RO` / `Settings: RO`
   - optional tooltip on `self.save_button`: `Unlock files before saving.`

Expected behavior:

1. Disable or clearly de-emphasize `Save Settings` when any loaded file is read-only.
2. Re-enable `Save Settings` immediately after `Unlock Files`.
3. Keep the current explicit error if a save is attempted while files are locked through any edge case.
4. Keep `Lock Files` / `Unlock Files` as direct actions without confirmation popups.

Acceptance checks:

- Locked files make save unavailable or visually blocked.
- Unlocking files makes save available without restarting.
- Locking files again blocks save again.
- No-profile state disables both save and lock controls.
- Defensive save error still appears if `save_all()` is called while files are read-only.

### Task: Unsaved Changes Tracking

Track whether visible or preset-applied settings differ from the last loaded/saved state.

Relevant current code:

- `ConfigEntry.value` is mutated in memory.
- `capture_visible_controls(validate=False)` pulls visible widgets into `ConfigEntry.value`.
- `apply_preset_to_ui()` mutates entries and re-renders.
- `load_documents()` reloads config values from disk.
- `doc.set_value(entry, entry.value)` writes current values during save.

Suggested implementation:

1. Add a baseline snapshot after successful load and after successful save.
   A simple structure is enough:
   - `self.loaded_values: dict[tuple[str, int], str]`
   - key should match the existing `self.controls` key shape: `(doc.label, entry.line_index)`
2. Add `snapshot_loaded_values()`:
   - iterate all documents and entries
   - store current `entry.value`
3. Add `changed_entries()`:
   - call `capture_visible_controls(validate=False)` first when appropriate
   - compare current `entry.value` against `self.loaded_values`
   - return a list of changed `(doc, entry)` pairs or keys
4. Add `has_unsaved_changes()` as `bool(changed_entries())`.
5. Add `update_dirty_indicator()`:
   - append or integrate `Unsaved changes` / `N changes` into the bottom status area
   - avoid destroying useful loaded-file status; consider adding a separate `self.dirty_label` near `self.status_label`
6. Call dirty update after user edits. Options:
   - connect widget signals in `create_value_widget()` to a lightweight `on_value_edited()` method
   - or update after category changes/search/mode changes via `capture_visible_controls()`
   - preferred: connect obvious signals for responsive UX, but keep the implementation simple.
7. `apply_preset_to_ui()` should mark dirty after applying a preset.
8. After successful save, update the baseline snapshot to the saved values and clear dirty state.
9. Before destructive navigation:
   - `reload_profiles()`
   - profile combo changes
   - `choose_game_dir()`
   prompt with `QMessageBox.question()` if there are unsaved changes.
10. Avoid warning on simple sidebar/category/mode/search changes, because those do not discard in-memory values.

Implementation caution:

- Avoid recursively calling `capture_visible_controls()` from signal handlers in ways that cause re-render loops.
- Upscaler changes already re-render the tree. Ensure dirty tracking captures the selected AA/upscaler state before re-render.
- Slider widgets emit many values while dragging; if dirty updates are expensive, debounce or keep the dirty check lightweight.

Expected behavior:

1. Show an `Unsaved changes` indicator in the bottom bar when edits are pending.
2. Clear the indicator after successful save or reload.
3. Show the number of changed settings if practical.
4. Warn before `Reload Settings`, profile changes, or folder changes if unsaved changes would be discarded.

Acceptance checks:

- Editing a checkbox/dropdown/slider/text field marks the app dirty.
- Loading a preset marks the app dirty.
- Saving clears dirty state.
- Reloading with changes prompts before discarding.
- Switching sidebar sections does not lose changes and should not prompt.
- Changing Normal/Advanced mode does not lose changes and should not prompt.
- Search/filter changes do not lose changes and should not prompt.

### Task: Backup Access and Release Integrity

Improve trust and recovery without adding an installer.

Relevant current code:

- `backup_documents(documents, repo_dir)` writes backups to `repo_dir / "backups" / timestamp`.
- `app_data_dir()` returns the executable folder in frozen builds and the repo root in source runs.
- `restore_latest_backup()` reads from `self.repo_dir / "backups"`.
- Build output is `dist\MW2CampaignConfigurator.exe`.

Suggested implementation:

1. Add `open_backup_folder()` method:
   - target path: `self.repo_dir / "backups"`
   - create it if it does not exist
   - open with `subprocess.Popen(["explorer", str(path)])` or `os.startfile(path)` on Windows
   - keep this Windows-only app simple; no cross-platform abstraction needed.
2. Add an `Open Backup Folder` button near `Restore Backup` in the bottom bar, or add it to the About dialog only if bottom bar space becomes tight.
3. If no backups exist, still open the folder after creating it. That is less annoying than a blocking dialog.
4. Update README safety/download sections with the backup path rule:
   - portable build: `backups\` next to the `.exe`
   - source run: `backups\` at the repo root
5. For release checksums:
   - compute SHA256 after `scripts\build.ps1`
   - PowerShell: `Get-FileHash .\dist\MW2CampaignConfigurator.exe -Algorithm SHA256`
   - include the hash in release notes.
6. Update `docs/BUILD_AND_RELEASE.md` release checklist to include checksum generation.

Expected behavior:

1. Add an `Open Backup Folder` action near `Restore Backup` or inside the About/help flow.
2. If no backups exist, show a small non-blocking message or concise dialog.
3. Add SHA256 checksum information for release executables in release notes.
4. Document where backups are stored in the README.

Acceptance checks:

- `Open Backup Folder` opens the portable `backups` directory.
- Restore behavior remains unchanged.
- Release notes include the executable checksum.
- README documents backup location.
- Build/release docs document checksum command.

### Task: Reset Selected Setting

Allow users to revert one edited option without reloading the whole profile.

Relevant current code:

- Options are rendered as `QTreeWidgetItem` rows in `render_options()`.
- Widgets are installed via `self.tree.setItemWidget(item, 2, self.create_value_widget(doc, entry))`.
- Current baseline does not yet exist; implement this after or alongside unsaved-change tracking.
- `display_label()`, choice helper functions, and `format_number()` preserve user-facing labels and numeric formatting.

Suggested implementation:

1. Reuse `self.loaded_values` from unsaved-change tracking as the reset baseline.
2. Add metadata to each option row:
   - Use `item.setData(0, Qt.ItemDataRole.UserRole, (doc.label, entry.line_index))`
   - Or keep `self.item_entries: dict[int, tuple[ConfigDocument, ConfigEntry]]`; item data is cleaner.
3. Add a small reset control. Practical options:
   - Add a fourth `Reset` column only in Advanced and Normal; or
   - Add a right-click context menu on the tree with `Reset Setting`; or
   - Add one bottom/toolbar button `Reset Selected` enabled when an option row is selected.
4. Recommended first implementation: `Reset Selected` button in the tools row.
   - It avoids resizing every row and is simple to test.
   - It should be disabled when no option row is selected or selected row is a subcategory.
5. Implement `reset_selected_setting()`:
   - locate selected row
   - read `(doc_label, line_index)`
   - find matching `ConfigEntry`
   - set `entry.value = self.loaded_values[key]`
   - call `render_options(capture=False)`
   - update dirty indicator
6. Do not reset all AA/upscaler shadow keys unless the selected setting is the unified AA selector.
   - For `AATechniquePreferred`, reset both visible and hidden AA/upscaler backing keys only if their baselines exist.
   - If that gets risky, document that v0.3.0 reset is per raw row and avoid special-casing unified AA until later.
7. Keep reset to last loaded/saved state, not factory defaults. The app does not know real factory defaults.

Expected behavior:

1. Store original loaded values separately from current in-memory values.
2. Add a simple per-row or context action to reset one setting to the last loaded value.
3. Preserve current formatting and choice-index behavior.
4. Resetting a setting should update unsaved-change tracking.

Acceptance checks:

- Resetting one setting restores only that setting.
- Reset works for bool, choice, range/slider, and text values.
- Save after reset writes the expected value.

### v0.3.0 Release Notes

- Added clearer first-run and missing-profile guidance on the home screen.
- Improved save availability based on file lock state.
- Added unsaved-change tracking and discard warnings.
- Added backup folder access and release checksum documentation.
- Added a reset action for individual settings.

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

## Release Notes Draft for v0.2.1

- Added FSR 2.0, AMD FSR 1.0, and CAS to the unified upscaler selector.
- Kept FSR/CAS/XeSS available across GPU vendors while gating only DLSS/DLAA to RTX GPUs.
- Hid the Source column in Normal mode.
- Added cleaner in-game style labels in Normal mode while keeping Advanced mode more file-faithful.

## Release Notes Draft for v0.2.2

- Added Windows display discovery for monitor, resolution, and refresh-rate dropdowns.
- Removed unused top-bar buttons to simplify the main window.
- Replaced the fixed `Unlock Files` action with a read-only aware `Lock Files` / `Unlock Files` toggle.

## Release Notes Draft for v0.2.3

- Added a startup home screen with no settings category selected by default.
- Removed lock/unlock confirmation popups.
- Changed saving to require unlocked files and show a short success toast instead of a modal dialog.
