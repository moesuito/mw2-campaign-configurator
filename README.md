# MW2 Campaign Configurator

A portable Windows settings editor for the Call of Duty: Modern Warfare II 2022 campaign configuration files.

The campaign settings screen can fail to save changes in some current game builds. This tool edits the readable campaign-effective configuration files directly, creates backups, and can lock the edited files as read-only so the game does not immediately overwrite them.

> This is an unofficial community tool. It is not affiliated with, endorsed by, or sponsored by Activision, Infinity Ward, or Call of Duty.

## Features

- Native Windows GUI inspired by classic Battlefield settings editors.
- Left sidebar with the original game categories: Accessibility, Audio, Display, Gameplay, Graphics, Interface, Mouse and Gamepad, System, and Touch.
- Automatically detects the default `Documents\Call of Duty MWII` folder.
- Supports multiple Steam/profile folders under `players`.
- Shows all editable options found in the campaign-effective text config files.
- Uses control types based on the game's own metadata:
  - checkboxes for true/false options
  - dropdowns for `one of [...]` options
  - numeric inputs for ranged values
  - text inputs for free-form values
- Includes quick presets: Low FPS, Balanced, High, Ultra, and Competitive.
- Shows only the relevant upscaler settings for the selected anti-aliasing technique.
- Hides DLSS and DLAA on non-RTX GPUs based on the detected `GPUName` value.
- Creates timestamped backups before saving.
- Saves and reapplies read-only attributes to the edited files.
- Portable `.exe`, no installer required.

## Edited Files

The app edits only these readable files:

- `players\options.3.cod22.cst`
- `players\<profile-id>\settings.3.local.cod22.cst`

It does not edit multiplayer, battle royale, DMZ, co-op, binary `.csb`, or hashed `.cfg` files.

## Download

Download the latest portable executable from the GitHub Releases page:

- `MW2CampaignConfigurator.exe`

Put it anywhere you like and run it. Backups are created next to the executable under `backups\`.

## Usage

1. Close the game.
2. Run `MW2CampaignConfigurator.exe`.
3. Confirm the detected `Call of Duty MWII` folder, or choose it manually.
4. Select the profile if more than one is detected.
5. Choose a category from the sidebar.
6. Edit values manually or load a preset.
7. Click `Save Settings`.
8. Start the campaign.

Use `Unlock Files` if you want the game to be able to write to the edited config files again.

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

## Safety Notes

- The app creates backups before writing any config files.
- The app temporarily removes read-only before saving, then reapplies read-only.
- Keep the game closed while saving settings.
- If something looks wrong, use `Restore Backup` in the app or copy files back manually from the `backups\` folder.

## License

MIT License. See [LICENSE](LICENSE).
