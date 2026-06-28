# Agent Instructions

This repository contains **MW2 Campaign Configurator**, a portable PyQt6 Windows app for editing the readable Call of Duty: Modern Warfare II 2022 campaign-effective configuration files.

Use this file as the first project handoff document. For deeper implementation details and planned work, read [`docs/HANDOFF.md`](docs/HANDOFF.md).

## Repository

- Local path: `D:\Antigravity\mw2-campaign-configurator`
- GitHub: `https://github.com/moesuito/mw2-campaign-configurator`
- Main branch: `main`
- App entrypoint: `src/mw2_campaign_configurator.py`
- Build script: `scripts/build.ps1`
- Portable executable output: `dist\MW2CampaignConfigurator.exe`

## Product Scope

- Keep the app focused on campaign-effective files only.
- Edit only:
  - `players\options.3.cod22.cst`
  - `players\<profile-id>\settings.3.local.cod22.cst`
- Do not edit multiplayer, battle royale, DMZ, co-op, `.csb`, hashed `.cfg`, or unrelated game files.
- Keep all app UI text and docs in English.
- Keep the app portable. Do not add an installer unless explicitly requested.

## Current UX Baseline

- PyQt6 dark-mode UI.
- Startup opens on a neutral home screen with no settings category selected.
- Sidebar categories are populated from loaded config entries.
- `Normal` mode hides technical source paths and uses cleaner labels.
- `Advanced` mode exposes extra readable fields from the config files.
- Config documents are loaded into memory and re-rendered from cache for navigation/search/mode changes.
- `Save Settings` requires writable files. It shows an error if any loaded file is read-only.
- `Lock Files` / `Unlock Files` changes file attributes directly without confirmation popups.
- Successful save shows a short toast notification.
- Empty or invalid game/profile states are explained in the home panel instead of relying only on the bottom status bar.
- The footer tracks unsaved changes and warns before destructive reload/profile/folder changes.
- `Reset Selected` restores one option to the last loaded or saved value.
- `Open Backups` opens the portable backup directory in Explorer.

## Development Rules

- Prefer small, scoped changes that match the current single-file app structure.
- Preserve raw config formatting and comments whenever possible.
- Preserve choice-index behavior through the existing helper functions.
- Do not replace game-provided option names/descriptions in Advanced mode.
- Add or update tests when parser behavior, choice mapping, visibility filtering, or save validation changes.
- Do not commit generated `build/`, `dist/`, virtualenv, or backup files unless explicitly requested.

## Validation

Run these before publishing changes:

```powershell
.\.venv\Scripts\python -m py_compile .\src\mw2_campaign_configurator.py .\scripts\create_icon.py
.\.venv\Scripts\python -m pytest .\tests
```

Useful offscreen smoke test:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python -c "import sys; sys.path.insert(0, 'src'); from PyQt6.QtWidgets import QApplication; from mw2_campaign_configurator import QtConfiguratorWindow; app=QApplication([]); w=QtConfiguratorWindow(); print('current_section=', repr(w.current_section)); print('home_hidden=', w.home_panel.isHidden()); print('sidebar_current=', w.sidebar.currentRow()); w.close(); app.quit()"
```

Build portable executable:

```powershell
.\scripts\build.ps1
```

## Release Flow

1. Confirm `git status -sb` contains only intended changes.
2. Run validation and build.
3. Commit to `main` with a concise release-oriented message when preparing a release.
4. Push `main`.
5. Create a GitHub release and attach `dist\MW2CampaignConfigurator.exe`.
6. Include release notes and the validation commands used.

Example:

```powershell
gh release create vX.Y.Z .\dist\MW2CampaignConfigurator.exe --title "vX.Y.Z" --notes "Release notes here."
```

## v0.3.0 Baseline

The v0.3.0 UX/reliability work is implemented. The detailed task plan remains in [`docs/HANDOFF.md`](docs/HANDOFF.md) as historical context and review guidance.

Implemented scope:

- Better first-run and missing-profile home-screen guidance.
- Save button state that reflects read-only lock state.
- Unsaved-change tracking and discard warnings.
- Backup folder access and release checksum documentation.
- Reset action for individual settings.

Future agents should preserve this behavior unless a new task explicitly changes it.

## Open UX Tasks

The next visual polish pass is documented in [`docs/HANDOFF.md`](docs/HANDOFF.md), under `Open Tasks After v0.3.0`.

Do not treat these as regressions in the current release:

- (All v0.3.0 polish tasks completed)
