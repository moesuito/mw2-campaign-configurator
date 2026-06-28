from __future__ import annotations

import datetime as dt
import pathlib
import re
import shutil
import stat
import sys
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk


APP_TITLE = "MW2 Campaign Configurator"
COLOR_HEADER = "#050505"
COLOR_NAV = "#e5eaee"
COLOR_NAV_ACTIVE = "#c8102e"
COLOR_NAV_TEXT = "#1d2730"
COLOR_BORDER = "#8d969f"
COLOR_FOOTER = "#f2eeee"
SECTION_NAMES = {
    "Accessibility",
    "Audio",
    "Display",
    "Gameplay",
    "Graphics",
    "Interface",
    "Mouse and Gamepad",
    "System",
    "Touch",
}

VALUE_RE = re.compile(r'^([^:]+):([\d.]+)\s*=\s*"([^"]*)"(?:\s*//\s*(.*))?$')
REPLACE_RE = re.compile(r'^([^=]+=\s*")([^"]*)(".*)$')
RANGE_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s+to\s+(-?\d+(?:\.\d+)?)")
CHOICE_RE = re.compile(r"one of \[(.*)\]")
RTX_ONLY_AA_CHOICES = {"DLSS", "DLAA"}
UPSCALER_CONFIG_KEYS = {
    "AMDContrastAdaptiveSharpeningStrength",
    "AMDSuperResolution",
    "AMDSuperResolutionQuality",
    "AMDSuperResolution2Quality",
    "DefaultSMAATechnique",
    "DLSSPerfMode",
    "DLSSSharpness",
    "NVIDIAImageScaling",
    "NVIDIAImageScalingQuality",
    "NVIDIAImageScalingSharpness",
    "SMAAQuality",
    "XeSSQuality",
}
UPSCALER_VISIBLE_KEYS = {
    "DLSS": {"DLSSPerfMode", "DLSSSharpness"},
    "DLAA": {"DLSSSharpness"},
    "XeSS": {"XeSSQuality"},
    "FSR2": {"AMDSuperResolution2Quality"},
    "SMAA T2x": {"DefaultSMAATechnique", "SMAAQuality"},
    "Filmic SMAA T2x": {"DefaultSMAATechnique", "SMAAQuality"},
}


@dataclass
class ConfigEntry:
    document_label: str
    line_index: int
    section: str
    description: str
    key: str
    version: str
    value: str
    meta: str
    stores_choice_index: bool = False

    @property
    def token(self) -> str:
        return f"{self.key}:{self.version}"

    @property
    def kind(self) -> str:
        if self.value in {"true", "false"}:
            return "bool"
        if self.choices:
            return "choice"
        if self.range_bounds:
            return "range"
        return "text"

    @property
    def choices(self) -> list[str]:
        if not self.meta:
            return []
        match = CHOICE_RE.search(self.meta)
        if not match:
            return []
        return [part.strip() for part in match.group(1).split(",")]

    @property
    def range_bounds(self) -> tuple[float, float] | None:
        if not self.meta:
            return None
        match = RANGE_RE.search(self.meta)
        if not match:
            return None
        return float(match.group(1)), float(match.group(2))

    def accepts(self, value: str) -> bool:
        if self.kind == "bool":
            return value in {"true", "false"}
        if self.choices:
            return value in self.choices or choice_label_for_value(self, value) in self.choices
        bounds = self.range_bounds
        if bounds:
            try:
                number = float(value)
            except ValueError:
                return False
            return bounds[0] <= number <= bounds[1]
        return True


def choice_label_for_value(entry: ConfigEntry, value: str) -> str:
    if value in entry.choices:
        return value
    if entry.choices and value.isdigit():
        index = int(value)
        if 0 <= index < len(entry.choices):
            return entry.choices[index]
    return value


def choice_value_for_label(entry: ConfigEntry, value: str) -> str:
    if not entry.stores_choice_index:
        return value
    if value.isdigit() and 0 <= int(value) < len(entry.choices):
        return value
    if value in entry.choices:
        return str(entry.choices.index(value))
    return value


def display_value_for_entry(entry: ConfigEntry) -> str:
    if entry.choices:
        return choice_label_for_value(entry, entry.value)
    return entry.value


def is_rtx_gpu_name(gpu_name: str) -> bool:
    normalized = gpu_name.upper()
    return "NVIDIA" in normalized and "RTX" in normalized


def filtered_aa_choices(entry: ConfigEntry, has_rtx: bool) -> list[str]:
    choices = entry.choices
    if entry.key != "AATechniquePreferred" or has_rtx:
        return choices
    return [choice for choice in choices if choice not in RTX_ONLY_AA_CHOICES]


def is_entry_visible_for_aa(entry: ConfigEntry, selected_aa: str) -> bool:
    if entry.key not in UPSCALER_CONFIG_KEYS:
        return True
    return entry.key in UPSCALER_VISIBLE_KEYS.get(selected_aa, set())


class ConfigDocument:
    def __init__(self, path: pathlib.Path, label: str, lines: list[str], entries: list[ConfigEntry]):
        self.path = path
        self.label = label
        self.lines = lines
        self.entries = entries

    @classmethod
    def load(cls, path: pathlib.Path, label: str) -> "ConfigDocument":
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        entries: list[ConfigEntry] = []
        section = "General"
        pending_description = ""

        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("//"):
                comment = stripped[2:].strip()
                if comment in SECTION_NAMES:
                    section = comment
                    pending_description = ""
                elif comment:
                    pending_description = comment
                continue

            match = VALUE_RE.match(stripped)
            if not match:
                continue

            key, version, value, meta = match.groups()
            entries.append(
                ConfigEntry(
                    document_label=label,
                    line_index=index,
                    section=section,
                    description=pending_description,
                    key=key,
                    version=version,
                    value=value,
                    meta=meta or "",
                    stores_choice_index=bool(meta and "one of [" in meta and value.isdigit()),
                )
            )
            pending_description = ""

        return cls(path, label, lines, entries)

    def set_value(self, entry: ConfigEntry, value: str) -> None:
        line = self.lines[entry.line_index]
        self.lines[entry.line_index] = REPLACE_RE.sub(lambda match: f"{match.group(1)}{value}{match.group(3)}", line)
        entry.value = value

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"

    def save(self) -> None:
        self.path.write_text(self.render(), encoding="utf-8")


PRESETS: dict[str, dict[str, str]] = {
    "Low FPS": {
        "ResolutionMultiplier:0.0": "70",
        "DynamicSceneResolution:0.0": "false",
        "DLSSPerfMode:0.0": "Maximum Performance",
        "AMDSuperResolutionQuality:0.0": "Maximum Performance",
        "AMDSuperResolution2Quality:0.0": "Maximum Performance",
        "NVIDIAImageScalingQuality:0.0": "Maximum Performance",
        "TextureQuality:0.0": "2",
        "TextureFilter:0.0": "TEXTURE_FILTER_ANISO4X",
        "ParticleQualityLevel:0.0": "low",
        "ParticleLighting:0.0": "1",
        "ShadowMapResolution:1.0": "Low",
        "SpotShadowQualityLevel:0.0": "Low",
        "ScreenSpaceShadowQuality:0.0": "Low",
        "SSAOTechnique:0.0": "Off",
        "SSRMode:0.0": "Off",
        "VolumetricQuality:0.0": "QUALITY_LOW",
        "WeatherGridVolumesQuality:0.0": "Low",
        "WorldStreamingQuality:0.0": "Low",
        "DepthOfField:0.0": "false",
        "FilmGrain:0.0": "0",
        "NvidiaReflex:0.0": "Enabled + boost",
        "CapFps:0.0": "true",
        "MaxFpsInGame:0.0": "144",
        "MaxFpsInMenu:1.0": "90",
        "MaxFpsOutOfFocus:0.0": "30",
        "Fov:0.0": "105",
        "ADSFovScaling:0.0": "false",
    },
    "Balanced": {
        "ResolutionMultiplier:0.0": "85",
        "DLSSPerfMode:0.0": "Balanced",
        "TextureQuality:0.0": "1",
        "TextureFilter:0.0": "TEXTURE_FILTER_ANISO8X",
        "ParticleQualityLevel:0.0": "medium",
        "ParticleLighting:0.0": "3",
        "ShadowMapResolution:1.0": "Normal",
        "SpotShadowQualityLevel:0.0": "Medium",
        "ScreenSpaceShadowQuality:0.0": "Low",
        "SSAOTechnique:0.0": "GTAO",
        "SSRMode:0.0": "Deferred LQ",
        "VolumetricQuality:0.0": "QUALITY_MEDIUM",
        "WeatherGridVolumesQuality:0.0": "Medium",
        "WorldStreamingQuality:0.0": "High",
        "DepthOfField:0.0": "false",
        "FilmGrain:0.0": "0",
        "NvidiaReflex:0.0": "Enabled",
        "CapFps:0.0": "true",
        "MaxFpsInGame:0.0": "165",
        "MaxFpsInMenu:1.0": "120",
        "Fov:0.0": "105",
    },
    "High": {
        "ResolutionMultiplier:0.0": "100",
        "DLSSPerfMode:0.0": "Maximum Quality",
        "TextureQuality:0.0": "0",
        "TextureFilter:0.0": "TEXTURE_FILTER_ANISO16X",
        "ParticleQualityLevel:0.0": "high",
        "ParticleLighting:0.0": "4",
        "ShadowMapResolution:1.0": "High",
        "SpotShadowQualityLevel:0.0": "High",
        "ScreenSpaceShadowQuality:0.0": "High",
        "SSAOTechnique:0.0": "GTAO & MDAO",
        "SSRMode:0.0": "Deferred HQ",
        "VolumetricQuality:0.0": "QUALITY_HIGH",
        "WeatherGridVolumesQuality:0.0": "High",
        "WorldStreamingQuality:0.0": "High",
        "DepthOfField:0.0": "true",
        "FilmGrain:0.0": "0.100000",
        "NvidiaReflex:0.0": "Enabled",
        "CapFps:0.0": "true",
        "MaxFpsInGame:0.0": "165",
        "MaxFpsInMenu:1.0": "120",
        "Fov:0.0": "105",
    },
    "Ultra": {
        "ResolutionMultiplier:0.0": "100",
        "DLSSPerfMode:0.0": "Maximum Quality",
        "TextureQuality:0.0": "0",
        "TextureFilter:0.0": "TEXTURE_FILTER_ANISO16X",
        "ParticleQualityLevel:0.0": "high",
        "ParticleLighting:0.0": "5",
        "ShadowMapResolution:1.0": "Ultra",
        "SpotShadowQualityLevel:0.0": "High",
        "ScreenSpaceShadowQuality:0.0": "High",
        "SSAOTechnique:0.0": "GTAO & MDAO",
        "SSRMode:0.0": "Deferred HQ",
        "VolumetricQuality:0.0": "QUALITY_HIGH",
        "WeatherGridVolumesQuality:0.0": "Ultra",
        "WorldStreamingQuality:0.0": "High",
        "DepthOfField:0.0": "true",
        "FilmGrain:0.0": "0.250000",
        "NvidiaReflex:0.0": "Enabled",
        "CapFps:0.0": "true",
        "MaxFpsInGame:0.0": "165",
        "MaxFpsInMenu:1.0": "120",
        "Fov:0.0": "100",
    },
    "Competitive": {
        "ResolutionMultiplier:0.0": "100",
        "DLSSPerfMode:0.0": "Balanced",
        "TextureQuality:0.0": "1",
        "TextureFilter:0.0": "TEXTURE_FILTER_ANISO8X",
        "ParticleQualityLevel:0.0": "low",
        "ParticleLighting:0.0": "1",
        "ShadowMapResolution:1.0": "Low",
        "SpotShadowQualityLevel:0.0": "Low",
        "ScreenSpaceShadowQuality:0.0": "Off",
        "SSAOTechnique:0.0": "Off",
        "SSRMode:0.0": "Off",
        "VolumetricQuality:0.0": "QUALITY_LOW",
        "WeatherGridVolumesQuality:0.0": "Off",
        "WorldStreamingQuality:0.0": "Low",
        "DepthOfField:0.0": "false",
        "FilmGrain:0.0": "0",
        "NvidiaReflex:0.0": "Enabled + boost",
        "CapFps:0.0": "true",
        "MaxFpsInGame:0.0": "250",
        "MaxFpsInMenu:1.0": "120",
        "MaxFpsOutOfFocus:0.0": "30",
        "Fov:0.0": "110",
        "ADSFovScaling:0.0": "false",
        "MouseAcceleration:0.0": "0",
        "MouseFilter:0.0": "0",
        "MouseSmoothing:0.0": "false",
    },
}


def default_game_dir() -> pathlib.Path:
    return pathlib.Path.home() / "Documents" / "Call of Duty MWII"


def is_readonly(path: pathlib.Path) -> bool:
    return not bool(path.stat().st_mode & stat.S_IWRITE)


def make_writable(path: pathlib.Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IWRITE)


def make_readonly(path: pathlib.Path) -> None:
    path.chmod(path.stat().st_mode & ~stat.S_IWRITE)


def discover_profiles(game_dir: pathlib.Path) -> list[str]:
    players = game_dir / "players"
    if not players.exists():
        return []
    profiles = []
    for child in players.iterdir():
        if child.is_dir() and child.name.isdigit() and (child / "settings.3.local.cod22.cst").exists():
            profiles.append(child.name)
    return sorted(profiles)


def target_paths(game_dir: pathlib.Path, profile: str) -> list[tuple[pathlib.Path, str]]:
    return [
        (game_dir / "players" / "options.3.cod22.cst", "Options"),
        (game_dir / "players" / profile / "settings.3.local.cod22.cst", "Settings"),
    ]


def validate_game_dir(game_dir: pathlib.Path, profile: str) -> None:
    missing = [str(path) for path, _ in target_paths(game_dir, profile) if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing files:\n" + "\n".join(missing))


def app_data_dir() -> pathlib.Path:
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys.executable).resolve().parent
    return pathlib.Path(__file__).resolve().parents[1]


def backup_documents(documents: list[ConfigDocument], repo_dir: pathlib.Path) -> pathlib.Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = repo_dir / "backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    for doc in documents:
        target = backup_dir / f"{doc.label}_{doc.path.name}"
        shutil.copy2(doc.path, target)
    return backup_dir


def restore_backup(backup_dir: pathlib.Path, documents: list[ConfigDocument]) -> None:
    by_label = {doc.label: doc for doc in documents}
    for backup in backup_dir.glob("*_*.cst"):
        label = backup.name.split("_", 1)[0]
        doc = by_label.get(label)
        if not doc:
            continue
        make_writable(doc.path)
        shutil.copy2(backup, doc.path)
        make_readonly(doc.path)


class ScrollFrame(ttk.Frame):
    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="white")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, style="Main.TFrame")
        self.inner.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", self._fit_width)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _fit_width(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)


class ConfiguratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(980, 620)

        self.repo_dir = app_data_dir()
        self.game_dir_var = tk.StringVar(value=str(default_game_dir()))
        self.profile_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Select the game folder.")
        self.search_var = tk.StringVar()
        self.preset_var = tk.StringVar(value="Balanced")

        self.documents: list[ConfigDocument] = []
        self.controls: dict[tuple[str, int], tk.Variable] = {}
        self.profile_combo: ttk.Combobox | None = None
        self.category_buttons: dict[str, tk.Button] = {}
        self.category_frame: tk.Frame | None = None
        self.options_scroll: ScrollFrame | None = None
        self.options_host: ttk.Frame | None = None
        self.section_title_var = tk.StringVar(value="Settings")
        self.section_meta_var = tk.StringVar(value="")
        self.current_section: str | None = None

        self._configure_style()
        self._build_shell()
        self.reload_profiles(auto=True)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Small.TLabel", font=("Segoe UI", 9))
        style.configure("TableHead.TLabel", font=("Segoe UI", 9, "bold"), background="white")
        style.configure("Main.TFrame", background="white")

    def _build_shell(self) -> None:
        header = tk.Frame(self, bg=COLOR_HEADER, height=78)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=COLOR_HEADER)
        brand.pack(side="left", fill="y", padx=18)
        tk.Label(
            brand,
            text="MW2",
            bg=COLOR_HEADER,
            fg="white",
            font=("Segoe UI", 22, "bold"),
        ).pack(side="left", pady=12)
        tk.Label(
            brand,
            text=" Campaign Settings Editor",
            bg=COLOR_HEADER,
            fg="white",
            font=("Segoe UI", 16),
        ).pack(side="left", pady=12)

        header_actions = tk.Frame(header, bg=COLOR_HEADER)
        header_actions.pack(side="right", padx=10, pady=14)
        tk.Button(header_actions, text="Profiles", width=10, command=self.reload_profiles).pack(side="left", padx=3)
        tk.Button(header_actions, text="Settings", width=10, command=lambda: self.select_section("Graphics")).pack(side="left", padx=3)
        tk.Button(header_actions, text="Help", width=8, command=self.show_help).pack(side="left", padx=3)

        top = ttk.Frame(self, padding=(10, 8, 10, 8))
        top.pack(fill="x")

        ttk.Label(top, text="MWII Folder").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.game_dir_var).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(top, text="Browse", command=self.choose_game_dir).grid(row=0, column=2)
        ttk.Button(top, text="Reload", command=self.reload_profiles).grid(row=0, column=3, padx=(8, 0))

        ttk.Label(top, text="Profile").grid(row=0, column=4, sticky="w", padx=(14, 0))
        self.profile_combo = ttk.Combobox(top, textvariable=self.profile_var, state="readonly", width=30)
        self.profile_combo.grid(row=0, column=5, sticky="w", padx=8)
        self.profile_combo.bind("<<ComboboxSelected>>", lambda _: self.load_documents())
        top.columnconfigure(1, weight=1)

        body = tk.Frame(self, bg="white")
        body.pack(fill="both", expand=True)

        side = tk.Frame(body, bg=COLOR_NAV, width=160)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        self.category_frame = tk.Frame(side, bg=COLOR_NAV)
        self.category_frame.pack(fill="both", expand=True, pady=(10, 0))

        main = ttk.Frame(body, style="Main.TFrame", padding=(20, 16, 20, 10))
        main.pack(side="left", fill="both", expand=True)

        ttk.Label(main, textvariable=self.section_title_var, style="Title.TLabel", background="white").pack(anchor="w")
        tk.Frame(main, height=1, bg="#222222").pack(fill="x", pady=(6, 10))

        toolrow = ttk.Frame(main, style="Main.TFrame")
        toolrow.pack(fill="x", pady=(0, 10))
        ttk.Label(toolrow, text="Preset", background="white").pack(side="left")
        preset_box = ttk.Combobox(toolrow, textvariable=self.preset_var, values=list(PRESETS), state="readonly", width=18)
        preset_box.pack(side="left", padx=(6, 6))
        ttk.Button(toolrow, text="Load Preset", command=self.apply_preset_to_ui).pack(side="left")

        ttk.Label(toolrow, text="Search", background="white").pack(side="left", padx=(18, 0))
        search_entry = ttk.Entry(toolrow, textvariable=self.search_var, width=28)
        search_entry.pack(side="left", padx=(6, 6))
        search_entry.bind("<Return>", lambda _: self.render_options())
        ttk.Button(toolrow, text="Filter", command=self.render_options).pack(side="left")
        ttk.Button(toolrow, text="Clear", command=self.clear_filter).pack(side="left", padx=(6, 0))
        ttk.Label(toolrow, textvariable=self.section_meta_var, style="Small.TLabel", background="white").pack(side="right")

        self.options_host = ttk.Frame(main, style="Main.TFrame")
        self.options_host.pack(fill="both", expand=True)

        footer = tk.Frame(self, bg=COLOR_FOOTER, height=36, highlightbackground="#c8c8c8", highlightthickness=1)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        tk.Button(footer, text="Reload Settings", command=self.reload_profiles).pack(side="left", padx=(8, 4), pady=5)
        tk.Button(footer, text="Save Settings", command=self.save_all).pack(side="left", padx=4, pady=5)
        tk.Button(footer, text="Unlock Files", command=self.unlock_files).pack(side="left", padx=4, pady=5)
        tk.Label(footer, textvariable=self.status_var, bg=COLOR_FOOTER).pack(side="left", fill="x", expand=True, padx=12)
        tk.Button(footer, text="Restore Backup", command=self.restore_latest_backup).pack(side="right", padx=4, pady=5)
        tk.Button(footer, text="About...", command=self.show_about).pack(side="right", padx=(4, 8), pady=5)

    def choose_game_dir(self) -> None:
        path = filedialog.askdirectory(title="Select the Call of Duty MWII folder")
        if path:
            self.game_dir_var.set(path)
            self.reload_profiles()

    def reload_profiles(self, auto: bool = False) -> None:
        game_dir = pathlib.Path(self.game_dir_var.get())
        profiles = discover_profiles(game_dir)
        if not profiles and auto:
            fallback = pathlib.Path.cwd()
            if (fallback / "players").exists():
                self.game_dir_var.set(str(fallback))
                profiles = discover_profiles(fallback)

        if self.profile_combo:
            self.profile_combo["values"] = profiles
        if profiles:
            if self.profile_var.get() not in profiles:
                self.profile_var.set(profiles[0])
            self.load_documents()
        else:
            self.documents = []
            self.render_options(capture=False)
            self.status_var.set("No valid profile found under players\\<profile-id>.")

    def load_documents(self) -> None:
        try:
            game_dir = pathlib.Path(self.game_dir_var.get())
            profile = self.profile_var.get()
            validate_game_dir(game_dir, profile)
            self.documents = [ConfigDocument.load(path, label) for path, label in target_paths(game_dir, profile)]
            self.enforce_hardware_constraints()
            readonly = ", ".join(f"{doc.label}: {'RO' if is_readonly(doc.path) else 'RW'}" for doc in self.documents)
            total = sum(len(doc.entries) for doc in self.documents)
            self.status_var.set(f"{total} options loaded. {readonly}")
            self.render_options(capture=False)
        except Exception as exc:
            self.documents = []
            self.render_options(capture=False)
            messagebox.showerror(APP_TITLE, str(exc))

    def clear_filter(self) -> None:
        self.search_var.set("")
        self.render_options()

    def entries_by_section(self) -> dict[str, list[tuple[ConfigDocument, ConfigEntry]]]:
        needle = self.search_var.get().strip().lower()
        grouped: dict[str, list[tuple[ConfigDocument, ConfigEntry]]] = {}
        for doc in self.documents:
            for entry in doc.entries:
                haystack = " ".join([entry.key, entry.description, entry.section, doc.label]).lower()
                if needle and needle not in haystack:
                    continue
                if not is_entry_visible_for_aa(entry, self.current_aa_label()):
                    continue
                grouped.setdefault(entry.section, []).append((doc, entry))
        return grouped

    def render_options(self, capture: bool = True) -> None:
        if not self.options_host:
            return
        if capture:
            self.capture_visible_controls(validate=False)
        for child in self.options_host.winfo_children():
            child.destroy()
        self.controls.clear()

        grouped = self.entries_by_section()
        if not grouped:
            self.render_category_buttons([])
            self.section_title_var.set("Settings")
            self.section_meta_var.set("")
            frame = ttk.Frame(self.options_host, padding=16, style="Main.TFrame")
            ttk.Label(frame, text="No options loaded.", background="white").pack(anchor="w")
            frame.pack(fill="both", expand=True)
            return

        sections = sorted(grouped)
        self.render_category_buttons(sections)
        if self.current_section not in grouped:
            preferred = "Graphics" if "Graphics" in grouped else sections[0]
            self.current_section = preferred

        entries = grouped[self.current_section]
        self.section_title_var.set(self.current_section)
        self.section_meta_var.set(f"{len(entries)} options")
        self.options_scroll = ScrollFrame(self.options_host)
        self.options_scroll.pack(fill="both", expand=True)
        self._add_table_header(self.options_scroll.inner)
        for row, (doc, entry) in enumerate(entries, start=1):
            self._add_entry_row(self.options_scroll.inner, row, doc, entry)

    def render_category_buttons(self, sections: list[str]) -> None:
        if not self.category_frame:
            return
        for child in self.category_frame.winfo_children():
            child.destroy()
        self.category_buttons.clear()
        for section in sections:
            active = section == self.current_section
            button = tk.Button(
                self.category_frame,
                text=section,
                anchor="w",
                relief="flat",
                borderwidth=0,
                padx=22,
                pady=11,
                bg=COLOR_NAV_ACTIVE if active else COLOR_NAV,
                fg="white" if active else COLOR_NAV_TEXT,
                activebackground=COLOR_NAV_ACTIVE,
                activeforeground="white",
                font=("Segoe UI", 9, "bold" if active else "normal"),
                command=lambda value=section: self.select_section(value),
            )
            button.pack(fill="x")
            self.category_buttons[section] = button

    def select_section(self, section: str) -> None:
        self.current_section = section
        self.render_options()

    def _add_table_header(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Option", style="TableHead.TLabel").grid(row=0, column=0, sticky="w", padx=(8, 10), pady=(0, 6))
        ttk.Label(parent, text="Source", style="TableHead.TLabel").grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(0, 6))
        ttk.Label(parent, text="Value", style="TableHead.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 8), pady=(0, 6))
        tk.Frame(parent, height=1, bg=COLOR_BORDER).grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=(0, 3))

    def _add_entry_row(self, parent: ttk.Frame, row: int, doc: ConfigDocument, entry: ConfigEntry) -> None:
        grid_row = row + 1
        label_text = entry.description or entry.key
        ttk.Label(parent, text=label_text, wraplength=470, justify="left", background="white").grid(row=grid_row, column=0, sticky="w", padx=(8, 10), pady=4)
        ttk.Label(parent, text=f"{doc.label} / {entry.token}", style="Small.TLabel", background="white").grid(row=grid_row, column=1, sticky="w", padx=(0, 10), pady=4)

        key = (doc.label, entry.line_index)
        if entry.kind == "bool":
            var = tk.BooleanVar(value=entry.value == "true")
            widget = ttk.Checkbutton(parent, variable=var)
        elif entry.kind == "choice":
            choices = filtered_aa_choices(entry, self.has_rtx_gpu())
            current = display_value_for_entry(entry)
            if entry.key == "AATechniquePreferred" and current not in choices and choices:
                current = choices[0]
                entry.value = choice_value_for_label(entry, current)
            var = tk.StringVar(value=current)
            widget = ttk.Combobox(parent, textvariable=var, values=choices, state="readonly", width=28)
            if entry.key == "AATechniquePreferred":
                widget.bind("<<ComboboxSelected>>", lambda _event, item=entry, variable=var: self.on_aa_changed(item, variable))
        elif entry.kind == "range":
            var = tk.StringVar(value=entry.value)
            bounds = entry.range_bounds or (0, 1)
            widget = ttk.Spinbox(parent, textvariable=var, from_=bounds[0], to=bounds[1], increment=self._range_step(bounds), width=18)
        else:
            var = tk.StringVar(value=entry.value)
            widget = ttk.Entry(parent, textvariable=var, width=30)

        widget.grid(row=grid_row, column=2, sticky="ew", padx=(0, 8), pady=4)
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(2, weight=1)
        self.controls[key] = var

    def capture_visible_controls(self, validate: bool = True) -> None:
        if not self.controls:
            return
        by_key = {
            (doc.label, entry.line_index): entry
            for doc in self.documents
            for entry in doc.entries
        }
        for key, var in self.controls.items():
            entry = by_key.get(key)
            if not entry:
                continue
            if isinstance(var, tk.BooleanVar):
                value = "true" if var.get() else "false"
            else:
                value = str(var.get()).strip()
            if entry.choices:
                value = choice_value_for_label(entry, value)
            if validate and not entry.accepts(value):
                raise ValueError(f"Invalid value for {entry.token}: {value}")
            entry.value = value

    def all_entries(self) -> list[ConfigEntry]:
        return [entry for doc in self.documents for entry in doc.entries]

    def entry_by_token(self, token: str) -> ConfigEntry | None:
        for entry in self.all_entries():
            if entry.token == token:
                return entry
        return None

    def gpu_name(self) -> str:
        entry = self.entry_by_token("GPUName:0.0")
        return entry.value if entry else ""

    def has_rtx_gpu(self) -> bool:
        return is_rtx_gpu_name(self.gpu_name())

    def current_aa_label(self) -> str:
        preferred = self.entry_by_token("AATechniquePreferred:0.0") or self.entry_by_token("AATechniquePreferred:0.1")
        if not preferred:
            return ""
        return choice_label_for_value(preferred, preferred.value)

    def enforce_hardware_constraints(self) -> None:
        if self.has_rtx_gpu():
            return
        for entry in self.all_entries():
            if entry.key != "AATechniquePreferred":
                continue
            current = choice_label_for_value(entry, entry.value)
            choices = filtered_aa_choices(entry, has_rtx=False)
            if current in RTX_ONLY_AA_CHOICES and choices:
                fallback = "SMAA T2x" if "SMAA T2x" in choices else choices[0]
                entry.value = choice_value_for_label(entry, fallback)

    def on_aa_changed(self, entry: ConfigEntry, var: tk.Variable) -> None:
        entry.value = choice_value_for_label(entry, str(var.get()).strip())
        self.enforce_hardware_constraints()
        self.render_options(capture=False)

    @staticmethod
    def _range_step(bounds: tuple[float, float]) -> float:
        span = bounds[1] - bounds[0]
        if span <= 2:
            return 0.01
        if span <= 20:
            return 0.1
        return 1

    def apply_preset_to_ui(self) -> None:
        self.capture_visible_controls(validate=False)
        preset = PRESETS[self.preset_var.get()]
        changed = 0
        skipped: list[str] = []
        for doc in self.documents:
            for entry in doc.entries:
                value = preset.get(entry.token, preset.get(entry.key))
                if value is None:
                    continue
                if not entry.accepts(value):
                    skipped.append(entry.token)
                    continue
                entry.value = choice_value_for_label(entry, value) if entry.choices else value
                var = self.controls.get((doc.label, entry.line_index))
                if var is not None:
                    if isinstance(var, tk.BooleanVar):
                        var.set(value == "true")
                    else:
                        var.set(display_value_for_entry(entry))
                changed += 1

        note = f"Preset loaded on screen: {changed} options."
        if skipped:
            note += f" Skipped by validation: {len(skipped)}."
        self.status_var.set(note)

    def show_help(self) -> None:
        messagebox.showinfo(
            APP_TITLE,
            "Use the sidebar to browse categories.\n"
            "Load a preset or edit values manually.\n"
            "Save Settings creates a backup and marks the files as read-only.",
        )

    def show_about(self) -> None:
        messagebox.showinfo(
            APP_TITLE,
            "MW2 Campaign Configurator\n"
            "Edits only the campaign-effective files under players.",
        )

    def save_all(self) -> None:
        if not self.documents:
            messagebox.showwarning(APP_TITLE, "Load a valid game folder before saving.")
            return

        try:
            self.capture_visible_controls(validate=True)
            backup_dir = backup_documents(self.documents, self.repo_dir)
            for doc in self.documents:
                make_writable(doc.path)
                for entry in doc.entries:
                    if not entry.accepts(entry.value):
                        raise ValueError(f"Invalid value for {entry.token}: {entry.value}")
                    doc.set_value(entry, entry.value)
                doc.save()
                make_readonly(doc.path)
            self.load_documents()
            messagebox.showinfo(APP_TITLE, f"Settings saved.\nBackup: {backup_dir}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def unlock_files(self) -> None:
        try:
            for doc in self.documents:
                make_writable(doc.path)
            self.load_documents()
            messagebox.showinfo(APP_TITLE, "Read-only removed from the loaded files.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def restore_latest_backup(self) -> None:
        backups = sorted((self.repo_dir / "backups").glob("*"))
        backups = [item for item in backups if item.is_dir()]
        if not backups:
            messagebox.showwarning(APP_TITLE, "No backup found.")
            return
        latest = backups[-1]
        try:
            restore_backup(latest, self.documents)
            self.load_documents()
            messagebox.showinfo(APP_TITLE, f"Backup restored: {latest}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))


def main() -> None:
    app = ConfiguratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
