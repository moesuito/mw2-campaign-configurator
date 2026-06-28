# Architecture

MW2 Campaign Configurator is a small PyQt6 desktop app that edits the readable campaign-effective configuration files used by Call of Duty: Modern Warfare II 2022.

## Runtime Flow

1. Detect the default game folder at `Documents\Call of Duty MWII`.
2. Discover profile folders under `players\<profile-id>`.
3. Load the two text config files into memory:
   - `players\options.3.cod22.cst`
   - `players\<profile-id>\settings.3.local.cod22.cst`
4. Parse option entries from the game's own text metadata.
5. Render cached entries in a PyQt6 tree UI.
6. Mutate values in memory while the user edits.
7. On `Save Settings`, create backups, remove read-only, write files, and reapply read-only.
8. Reload files after save/restore so the UI reflects disk state.

Menu changes, search, Normal/Advanced mode, anti-aliasing changes, and sidebar navigation do not reread files. They re-render cached entries already held in RAM.

## Parser

The parser lives in `src/mw2_campaign_configurator.py`:

- `ConfigDocument` represents one loaded config file.
- `ConfigEntry` represents one editable setting line.
- Lines are preserved as text and only the quoted value is replaced.
- Comments, section headers, metadata, and unknown lines are preserved.

Supported metadata:

- `one of [...]` becomes a dropdown.
- `x to y` becomes either a slider or numeric input.
- `true`/`false` becomes a checkbox.
- Everything else becomes a text field.

Some game options store dropdown values as numeric indexes. `stores_choice_index`, `choice_label_for_value`, and `choice_value_for_label` preserve that behavior so saving does not rewrite index-backed values as labels.

## UI

The app uses PyQt6:

- `QtConfiguratorWindow` is the main window.
- `QListWidget` renders the left category sidebar.
- `QTreeWidget` renders subcategories and option rows.
- `SliderEditor` combines a horizontal slider with a numeric spinbox for practical ranged values.
- Dark mode styling is applied through a local Qt stylesheet.

The tree layout intentionally groups settings by behavior rather than raw file order. `entry_subcategory()` decides the subcategory for each option.

## Normal vs Advanced

`Normal` mode uses `NORMAL_MODE_KEYS` to show common settings that map closely to the in-game menus.

`Advanced` mode shows every parsed readable option, except options hidden by hardware/upscaler filtering.

The Normal list is intentionally conservative. When adding a key to Normal mode, verify that it is a user-facing option or a clearly useful equivalent.

## Upscaler Filtering

Upscaler behavior is controlled by:

- `UPSCALER_CONFIG_KEYS`
- `UPSCALER_VISIBLE_KEYS`
- `RTX_ONLY_AA_CHOICES`
- `is_rtx_gpu_name()`

The app reads `GPUName:0.0` from the config. DLSS and DLAA remain visible only when the GPU name contains both `NVIDIA` and `RTX`.

When the selected anti-aliasing technique changes, the tree is re-rendered from cached entries and only relevant upscaler child settings remain visible.

## Filesystem Safety

The app edits only:

- `players\options.3.cod22.cst`
- `players\<profile-id>\settings.3.local.cod22.cst`

It does not edit `.csb`, hashed `.cfg`, MP, BR, DMZ, or co-op files.

Backups are written under `backups\<timestamp>\` next to the executable in a portable build, or next to the repo root when run from source.
