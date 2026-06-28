# MW2 Campaign Configurator

A portable Windows settings editor for the Call of Duty: Modern Warfare II 2022 campaign configuration files.

The campaign settings screen can fail to save changes in some current game builds. This tool edits the readable campaign-effective configuration files directly, creates backups, and can lock the edited files as read-only so the game does not immediately overwrite them.

> This is an unofficial community tool. It is not affiliated with, endorsed by, or sponsored by Activision, Infinity Ward, or Call of Duty.

## Features

- Native PyQt6 Windows GUI inspired by classic Battlefield settings editors.
- Full dark mode interface.
- Home screen on startup with no settings category selected by default, including clearer guidance when the game folder or campaign profile is missing.
- Left sidebar with the original game categories: Accessibility, Audio, Display, Gameplay, Graphics, Interface, Mouse and Gamepad, System, and Touch.
- Normal and Advanced modes:
  - `Normal` focuses on the main in-game menu style options.
  - `Normal` uses cleaner in-game style labels and hides technical source paths.
  - `Advanced` also shows extra readable config fields exposed by the files.
- Tree-style subcategories inside each section, including grouped anti-aliasing/upscaler controls.
- Automatically detects the default `Documents\Call of Duty MWII` folder.
- Supports multiple Steam/profile folders under `players`.
- Shows all editable options found in the campaign-effective text config files.
- Detects Windows displays and exposes monitor-specific resolution and refresh-rate choices.
- Uses control types based on the game's own metadata:
  - checkboxes for true/false options
  - dropdowns for `one of [...]` options
  - sliders with numeric inputs for practical percentage/range settings
  - numeric inputs for ranged values
  - text inputs for free-form values
- Includes quick presets: Low FPS, Balanced, High, Ultra, and Competitive.
- Shows only the relevant upscaler settings for the selected anti-aliasing technique.
- Uses one unified upscaler selector for SMAA, DLSS, DLAA, XeSS, FSR 2.0, CAS, and AMD FSR 1.0.
- Hides only DLSS and DLAA on non-RTX GPUs based on the detected `GPUName` value. FSR and XeSS remain available across GPU vendors.
- Creates timestamped backups before saving.
- Includes `Open Backups` to open the backup folder directly in Explorer.
- Saves only when the loaded files are writable, leaving lock control to the user.
- Includes a bottom-bar file lock toggle:
  - `Unlock Files` appears when the loaded files are read-only.
  - `Lock Files` appears when the loaded files are writable.
- Disables saving while files are locked, then shows a short success notification instead of a modal dialog.
- Tracks unsaved changes and warns before reload, folder changes, or profile changes would discard edits.
- Includes `Reset Selected` to restore one setting to the last loaded or saved value.
- Portable `.exe`, no installer required.

## Edited Files

The app edits only these readable files:

- `players\options.3.cod22.cst`
- `players\<profile-id>\settings.3.local.cod22.cst`

It does not edit multiplayer, battle royale, DMZ, co-op, binary `.csb`, or hashed `.cfg` files.

## Download

Download the latest portable executable from the GitHub Releases page:

- `MW2CampaignConfigurator.exe`

Put it anywhere you like and run it. Backups are created under a `backups\` folder next to the executable (for a portable build) or at the repo root (for a source run).

## Usage

1. Close the game.
2. Run `MW2CampaignConfigurator.exe`.
3. Confirm the detected `Call of Duty MWII` folder, or choose it manually.
4. Select the profile if more than one is detected.
5. Click `Unlock Files` if the loaded files are read-only.
6. Choose a category from the sidebar.
7. Use `Normal` mode for the common settings, or `Advanced` to expose every supported readable field.
8. Edit values manually or load a preset.
9. Use `Reset Selected` if you want to revert one highlighted option before saving.
10. Click `Save Settings`.
11. Click `Lock Files` if you want to protect the edited files from game-side overwrites.
12. Start the campaign.

Use the bottom-bar lock toggle if you want to temporarily unlock the loaded files or lock them again after manual edits.

## Presets

- `Low FPS`: lowers expensive graphics settings and prioritizes performance.
- `Balanced`: keeps a practical mix of clarity, image quality, and frame rate.
- `High`: restores high-quality graphics while keeping sane limits.
- `Ultra`: maximizes visual settings available in the readable config.
- `Competitive`: prioritizes clarity, low latency, high FOV, and high FPS.

Presets only modify known keys that exist in the loaded files and pass the game's metadata validation.

## Build From Source

Requirements:

- Windows
- Python 3.11 or newer
- Git

Build:

```powershell
git clone https://github.com/moesuito/mw2-campaign-configurator.git
cd mw2-campaign-configurator
.\scripts\build.ps1
```

The portable executable will be created at:

```text
dist\MW2CampaignConfigurator.exe
```

Run from source:

```powershell
py src\mw2_campaign_configurator.py
```

Run tests:

```powershell
py -m pytest .\tests
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Build and release](docs/BUILD_AND_RELEASE.md)
- [Agent handoff](docs/HANDOFF.md)

## Safety Notes

- The app creates backups before writing any config files.
- `Save Settings` requires the loaded files to be writable. Use `Unlock Files` before saving.
- Unsaved-change prompts appear before actions that would discard in-memory edits.
- Keep the game closed while saving settings.
- If something looks wrong, use `Restore Backup`, click `Open Backups`, or copy files back manually from the `backups\` folder.

## License

MIT License. See [LICENSE](LICENSE).
