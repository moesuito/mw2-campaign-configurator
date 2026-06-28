from __future__ import annotations

import datetime as dt
import ctypes
import pathlib
import re
import shutil
import stat
import sys
from dataclasses import dataclass
from ctypes import wintypes

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


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
    "FSR 2.0": {"AMDSuperResolution2Quality"},
    "AMD FSR 1.0": {"AMDSuperResolutionQuality"},
    "CAS - Sharpening only": {"AMDContrastAdaptiveSharpeningStrength"},
    "SMAA T2x": {"DefaultSMAATechnique", "SMAAQuality"},
    "Filmic SMAA T2x": {"DefaultSMAATechnique", "SMAAQuality"},
}
NORMAL_MODE_KEYS = {
    "AATechniquePreferred",
    "ADSFovScaling",
    "ADSSensitivity",
    "ADSTimingSensitivity",
    "AudioMix",
    "AudioWantedChannelsNumber",
    "AMDContrastAdaptiveSharpeningStrength",
    "AMDSuperResolution",
    "AMDSuperResolutionQuality",
    "AMDSuperResolution2Quality",
    "AltShellShock",
    "Brightness",
    "BulletImpacts",
    "CapFps",
    "CinematicVolume",
    "ConstrainMouse",
    "DLSSPerfMode",
    "DLSSSharpness",
    "DefaultSMAATechnique",
    "DeferredPhysics",
    "DepthOfField",
    "DisplayGamma",
    "DisplayMode",
    "DynamicSceneResolution",
    "DynamicSceneResolutionTarget",
    "EffectsVolume",
    "EnableGamepad",
    "FilmGrain",
    "FilmicStrength",
    "Fov",
    "FreeLook",
    "GTAOQuality",
    "HDR",
    "HDRGamma",
    "HDRMaxLum",
    "HDRMinLum",
    "HitMarkersVolume",
    "HUDHorizBound",
    "HUDVertBound",
    "LicensedContentVolume",
    "LicensedMusicVolume",
    "ModelLodDistanceQuality",
    "ModelLodQuality",
    "Monitor",
    "MonoSound",
    "MonoSoundAmount",
    "MouseAcceleration",
    "MouseFilter",
    "MouseHorizontalSensibility",
    "MouseInvertPitch",
    "MouseMonitorDistanceCoeff",
    "MouseSmoothing",
    "MouseVerticalSensibility",
    "MusicVolume",
    "MuteAudioWhileOutOfFocus",
    "NVIDIAImageScaling",
    "NVIDIAImageScalingQuality",
    "NVIDIAImageScalingSharpness",
    "NvidiaReflex",
    "ParticleLighting",
    "ParticleQualityLevel",
    "ParticuleResolution",
    "PreferredDisplayMode",
    "RefreshRate",
    "Resolution",
    "ResolutionMultiplier",
    "SkipIntro",
    "SMAAQuality",
    "SSAOTechnique",
    "SSRMode",
    "ScreenSpaceShadowQuality",
    "ShaderQuality",
    "ShadowMapResolution",
    "SpotShadowCacheSize",
    "SpotShadowQualityLevel",
    "SunShadowCascade",
    "Tessellation",
    "TextureFilter",
    "TextureQuality",
    "ThirdPersonFov",
    "UiQuality",
    "VSync",
    "VSyncInMenu",
    "VoiceChat",
    "VoiceChatEffect",
    "VoiceChatVolume",
    "VoiceInputDevice",
    "VoicePushToTalk",
    "VoiceVolume",
    "Volume",
    "VolumetricQuality",
    "WarTracksVolume",
    "WaterCausticsMode",
    "WaterWaveWetness",
    "WeatherGridVolumesQuality",
    "WorldStreamingQuality",
    "XeSSQuality",
}
NON_SLIDER_RANGE_KEYS = {
    "AudioMix",
    "RendererWorkerCount",
    "StaticSunshadowClipmapResolution",
    "WeaponCycleDelay",
    "WindowHeight",
    "WindowWidth",
    "WindowX",
    "WindowY",
}
NORMAL_LABELS = {
    "AATechniquePreferred": "Upscaling / Anti-Aliasing",
    "AMDContrastAdaptiveSharpeningStrength": "CAS Strength",
    "AMDSuperResolution2Quality": "FSR 2.0 Quality",
    "AMDSuperResolutionQuality": "FSR 1.0 Quality",
    "AspectRatio": "Aspect Ratio",
    "Brightness": "Brightness",
    "BulletImpacts": "Bullet Impacts",
    "CapFps": "Custom Frame Rate Limit",
    "CinematicVolume": "Cinematic Volume",
    "DLSSPerfMode": "DLSS Quality",
    "DLSSSharpness": "DLSS Sharpness",
    "DefaultSMAATechnique": "SMAA Mode",
    "DeferredPhysics": "Deferred Physics Quality",
    "DepthOfField": "Depth of Field",
    "DisplayGamma": "Display Gamma",
    "DisplayMode": "Display Mode",
    "DynamicSceneResolution": "Dynamic Resolution",
    "DynamicSceneResolutionTarget": "Dynamic Resolution Target",
    "EffectsVolume": "Effects Volume",
    "FilmGrain": "Film Grain",
    "FilmicStrength": "Filmic Strength",
    "Fov": "Field of View",
    "GTAOQuality": "Ambient Occlusion Quality",
    "HDR": "HDR",
    "HitMarkersVolume": "Hit Marker Volume",
    "HUDHorizBound": "Horizontal HUD Bounds",
    "HUDVertBound": "Vertical HUD Bounds",
    "LicensedContentVolume": "Licensed Content Volume",
    "LicensedMusicVolume": "Licensed Music Volume",
    "ModelLodDistanceQuality": "Level of Detail Distance",
    "ModelLodQuality": "Model Quality",
    "MonoSound": "Mono Audio",
    "MonoSoundAmount": "Mono Amount",
    "MouseAcceleration": "Mouse Acceleration",
    "MouseFilter": "Mouse Filtering",
    "MouseHorizontalSensibility": "Mouse Sensitivity",
    "MouseInvertPitch": "Invert Mouse Look",
    "MouseMonitorDistanceCoeff": "Monitor Distance Coefficient",
    "MouseSmoothing": "Mouse Smoothing",
    "MouseVerticalSensibility": "Vertical Sensitivity Multiplier",
    "MusicVolume": "Music Volume",
    "MuteAudioWhileOutOfFocus": "Mute When Out of Focus",
    "NVIDIAImageScaling": "NVIDIA Image Scaling",
    "NVIDIAImageScalingQuality": "NVIDIA Image Scaling Quality",
    "NVIDIAImageScalingSharpness": "NVIDIA Image Scaling Sharpness",
    "NvidiaReflex": "NVIDIA Reflex Low Latency",
    "ParticleLighting": "Particle Lighting",
    "ParticleQualityLevel": "Particle Quality",
    "ParticuleResolution": "Particle Resolution",
    "PreferredDisplayMode": "Preferred Display Mode",
    "RefreshRate": "Refresh Rate",
    "Resolution": "Display Resolution",
    "ResolutionMultiplier": "Render Resolution Scale",
    "SMAAQuality": "SMAA Quality",
    "SSAOTechnique": "Ambient Occlusion",
    "SSRMode": "Screen Space Reflections",
    "ScreenSpaceShadowQuality": "Screen Space Shadows",
    "ShaderQuality": "Shader Quality",
    "ShadowMapResolution": "Shadow Map Resolution",
    "SpotShadowCacheSize": "Spot Shadow Cache",
    "SpotShadowQualityLevel": "Spot Shadow Quality",
    "SunShadowCascade": "Sun Shadow Quality",
    "Tessellation": "Tessellation",
    "TextureFilter": "Texture Filtering",
    "TextureQuality": "Texture Resolution",
    "ThirdPersonFov": "3rd Person Field of View",
    "UiQuality": "UI Quality",
    "VSync": "V-Sync",
    "VSyncInMenu": "Menu V-Sync",
    "VideoMemoryScale": "Video Memory Scale",
    "VoiceChat": "Voice Chat",
    "VoiceChatEffect": "Voice Chat Effect",
    "VoiceChatVolume": "Voice Chat Volume",
    "VoiceInputDevice": "Voice Input Device",
    "VoicePushToTalk": "Push to Talk",
    "VoiceVolume": "Dialogue Volume",
    "Volume": "Master Volume",
    "VolumetricQuality": "Volumetric Quality",
    "WarTracksVolume": "War Tracks Volume",
    "WaterCausticsMode": "Water Caustics",
    "WeatherGridVolumesQuality": "Weather Grid Volumes",
    "WorldStreamingQuality": "On-Demand Texture Streaming",
    "XeSSQuality": "XeSS Quality",
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
    if entry.token == "AATechniquePreferred:0.1":
        return False
    if entry.key == "AMDSuperResolution":
        return False
    if entry.key not in UPSCALER_CONFIG_KEYS:
        return True
    return entry.key in UPSCALER_VISIBLE_KEYS.get(selected_aa, set())


def is_normal_mode_entry(entry: ConfigEntry) -> bool:
    return entry.key in NORMAL_MODE_KEYS


def should_use_slider(entry: ConfigEntry) -> bool:
    bounds = entry.range_bounds
    if not bounds or entry.key in NON_SLIDER_RANGE_KEYS:
        return False
    span = bounds[1] - bounds[0]
    if span <= 0 or span > 1000:
        return False
    return (
        bounds == (0.0, 1.0)
        or bounds == (0.0, 100.0)
        or entry.key in {
            "ResolutionMultiplier",
            "Fov",
            "ThirdPersonFov",
            "MaxFpsInGame",
            "MaxFpsInMenu",
            "MaxFpsOutOfFocus",
            "Brightness",
            "FilmGrain",
            "DLSSSharpness",
            "AMDContrastAdaptiveSharpeningStrength",
            "NVIDIAImageScalingSharpness",
            "VideoMemoryScale",
        }
    )


def entry_subcategory(entry: ConfigEntry) -> str:
    if entry.section == "Graphics":
        if entry.key in {"AATechniquePreferred", *UPSCALER_CONFIG_KEYS}:
            return "Anti-Aliasing / Upscaling"
        if entry.key in {"TextureQuality", "TextureFilter", "ModelLodQuality", "ModelLodDistanceQuality", "WorldStreamingQuality", "VirtualTexturingLargeMemory", "VirtualTexturingMemoryMode"}:
            return "Details & Textures"
        if entry.key in {"ShadowMapResolution", "SpotShadowQualityLevel", "SpotShadowCacheSize", "ScreenSpaceShadowQuality", "SunShadowCascade", "SSAOTechnique", "GTAOQuality", "SSRMode", "ReflectionProbeHalfResolution", "ReflectionProbeRelighting", "VolumetricQuality", "WeatherGridVolumesQuality", "WaterCausticsMode", "WaterWaveWetness"}:
            return "Shadows & Lighting"
        if entry.key in {"DepthOfField", "FilmGrain", "FilmicStrength", "HDR", "HDRGamma", "HDRMaxLum", "HDRMinLum"}:
            return "Post Processing"
        if entry.key in {"ParticleQualityLevel", "ParticleLighting", "ParticuleResolution", "BulletImpacts", "PersistentDamageLayer", "DeferredPhysics", "ShaderQuality", "Tessellation"}:
            return "Effects & Geometry"
        return "Advanced Graphics"
    if entry.section == "Display":
        if entry.key in {"DisplayMode", "PreferredDisplayMode", "Monitor", "RefreshRate", "Resolution", "ResolutionMultiplier", "AspectRatio", "DisplayGamma", "HDR"}:
            return "Display"
        if entry.key in {"VSync", "VSyncInMenu", "CapFps", "MaxFpsInGame", "MaxFpsInMenu", "MaxFpsOutOfFocus", "NvidiaReflex", "DynamicSceneResolution", "DynamicSceneResolutionTarget"}:
            return "Frame Rate"
        return "Window"
    if entry.section == "Audio":
        if "Volume" in entry.key or entry.key in {"AudioMix", "CinematicVolume"}:
            return "Volumes"
        if "Voice" in entry.key or "Mic" in entry.key or "Microphone" in entry.key:
            return "Voice Chat"
        return "Playback"
    if entry.section == "Mouse and Gamepad":
        if "ADS" in entry.key:
            return "ADS Sensitivity"
        if "Vehicle" in entry.key or "Flight" in entry.key or "Air" in entry.key or "Land" in entry.key:
            return "Vehicles"
        return "Mouse"
    return entry.section


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


@dataclass(frozen=True)
class DisplayMode:
    width: int
    height: int
    refresh_rate: int

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass
class DisplayInfo:
    name: str
    device_name: str
    modes: list[DisplayMode]


class POINTL(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmPosition", POINTL),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", wintypes.WCHAR * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


def discover_windows_displays() -> list[DisplayInfo]:
    if sys.platform != "win32":
        return []

    user32 = ctypes.windll.user32
    enum_display_devices = user32.EnumDisplayDevicesW
    enum_display_devices.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DISPLAY_DEVICEW), wintypes.DWORD]
    enum_display_devices.restype = wintypes.BOOL
    enum_display_settings = user32.EnumDisplaySettingsW
    enum_display_settings.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DEVMODEW)]
    enum_display_settings.restype = wintypes.BOOL

    attached_to_desktop = 0x00000001
    displays: list[DisplayInfo] = []
    adapter_index = 0
    while True:
        adapter = DISPLAY_DEVICEW()
        adapter.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not enum_display_devices(None, adapter_index, ctypes.byref(adapter), 0):
            break
        adapter_index += 1
        if not adapter.StateFlags & attached_to_desktop:
            continue

        monitor_name = ""
        monitor = DISPLAY_DEVICEW()
        monitor.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if enum_display_devices(adapter.DeviceName, 0, ctypes.byref(monitor), 0):
            monitor_name = monitor.DeviceString

        modes_by_key: dict[tuple[int, int, int], DisplayMode] = {}
        mode_index = 0
        while True:
            devmode = DEVMODEW()
            devmode.dmSize = ctypes.sizeof(DEVMODEW)
            if not enum_display_settings(adapter.DeviceName, mode_index, ctypes.byref(devmode)):
                break
            mode_index += 1
            if devmode.dmPelsWidth <= 0 or devmode.dmPelsHeight <= 0 or devmode.dmDisplayFrequency <= 0:
                continue
            key = (int(devmode.dmPelsWidth), int(devmode.dmPelsHeight), int(devmode.dmDisplayFrequency))
            modes_by_key[key] = DisplayMode(*key)

        modes = sorted(
            modes_by_key.values(),
            key=lambda item: (item.width * item.height, item.width, item.height, item.refresh_rate),
            reverse=True,
        )
        display_name = monitor_name or adapter.DeviceString or adapter.DeviceName
        displays.append(DisplayInfo(name=display_name, device_name=adapter.DeviceName, modes=modes))

    return displays


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


class SliderEditor(QWidget):
    def __init__(self, entry: ConfigEntry):
        super().__init__()
        self.entry = entry
        self.bounds = entry.range_bounds or (0.0, 1.0)
        self.scale = 1000 if self.bounds[1] - self.bounds[0] <= 10 else 1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, self.to_slider(self.bounds[1]))
        self.slider.setMinimum(self.to_slider(self.bounds[0]))
        self.spin = QDoubleSpinBox()
        self.spin.setRange(self.bounds[0], self.bounds[1])
        self.spin.setDecimals(0 if QtConfiguratorWindow.is_integerish(entry.value, self.bounds) else 6)
        self.spin.setSingleStep(QtConfiguratorWindow._range_step(self.bounds))

        try:
            initial = float(entry.value)
        except ValueError:
            initial = self.bounds[0]
        self.spin.setValue(initial)
        self.slider.setValue(self.to_slider(initial))

        self.slider.valueChanged.connect(self.on_slider_changed)
        self.spin.valueChanged.connect(self.on_spin_changed)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spin)

    def to_slider(self, value: float) -> int:
        return int(round(value * self.scale))

    def from_slider(self, value: int) -> float:
        return value / self.scale

    def on_slider_changed(self, value: int) -> None:
        target = self.from_slider(value)
        if abs(self.spin.value() - target) > 0.000001:
            self.spin.blockSignals(True)
            self.spin.setValue(target)
            self.spin.blockSignals(False)

    def on_spin_changed(self, value: float) -> None:
        target = self.to_slider(value)
        if self.slider.value() != target:
            self.slider.blockSignals(True)
            self.slider.setValue(target)
            self.slider.blockSignals(False)

    def value(self) -> float:
        return self.spin.value()


class QtConfiguratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.repo_dir = app_data_dir()
        self.displays = discover_windows_displays()
        self.documents: list[ConfigDocument] = []
        self.controls: dict[tuple[str, int], object] = {}
        self.current_section = ""
        self.game_dir = default_game_dir()
        self.loaded_values: dict[tuple[str, int], str] = {}
        self.current_profile = ""
        self.is_rendering = False

        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 760)
        icon_path = self.repo_dir / "assets" / "app.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()
        self.reload_profiles(auto=True)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 14, 14, 14)
        title = QLabel('<span style="font-size:30px;font-weight:700;">MW2</span>'
                       '<span style="font-size:21px;"> Campaign Settings Editor</span>')
        title.setObjectName("headerTitle")
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        layout.addWidget(header)

        top = QFrame()
        top.setObjectName("topBar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.addWidget(QLabel("MWII Folder"))
        self.folder_edit = QLineEdit(str(self.game_dir))
        top_layout.addWidget(self.folder_edit, 1)
        browse = QPushButton("Browse")
        browse.clicked.connect(self.choose_game_dir)
        top_layout.addWidget(browse)
        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self.reload_profiles)
        top_layout.addWidget(reload_button)
        top_layout.addWidget(QLabel("Profile"))
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(lambda _value: self.on_profile_changed())
        top_layout.addWidget(self.profile_combo)
        layout.addWidget(top)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body_wrap = QWidget()
        body_wrap.setLayout(body)
        layout.addWidget(body_wrap, 1)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(166)
        self.sidebar.currentTextChanged.connect(self.select_section)
        body.addWidget(self.sidebar)

        main = QWidget()
        main.setObjectName("mainPanel")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(20, 16, 20, 10)
        main_layout.setSpacing(10)
        self.section_title = QLabel("Settings")
        self.section_title.setObjectName("sectionTitle")
        main_layout.addWidget(self.section_title)
        self.section_rule = QFrame()
        self.section_rule.setFrameShape(QFrame.Shape.HLine)
        self.section_rule.setObjectName("sectionRule")
        main_layout.addWidget(self.section_rule)

        self.home_panel = QWidget()
        self.home_panel.setObjectName("homePanel")
        home_layout = QVBoxLayout(self.home_panel)
        home_layout.setContentsMargins(0, 0, 0, 0)
        home_layout.setSpacing(8)
        home_layout.addStretch(1)
        self.home_title = QLabel("MW2 Campaign Configurator")
        self.home_title.setObjectName("homeTitle")
        self.home_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(self.home_title)
        self.home_copy = QLabel("Edit campaign-effective Modern Warfare II settings files, manage presets, and control file locking from one portable tool.")
        self.home_copy.setObjectName("homeCopy")
        self.home_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.home_copy.setWordWrap(True)
        home_layout.addWidget(self.home_copy)
        home_layout.addStretch(1)
        main_layout.addWidget(self.home_panel, 1)

        self.tools_panel = QWidget()
        tools = QHBoxLayout(self.tools_panel)
        tools.setContentsMargins(0, 0, 0, 0)
        tools.addWidget(QLabel("Mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Normal", "Advanced"])
        self.mode_combo.currentTextChanged.connect(lambda _value: self.render_options())
        tools.addWidget(self.mode_combo)
        tools.addSpacing(12)
        tools.addWidget(QLabel("Preset"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(PRESETS))
        self.preset_combo.setCurrentText("Balanced")
        tools.addWidget(self.preset_combo)
        preset_button = QPushButton("Load Preset")
        preset_button.clicked.connect(self.apply_preset_to_ui)
        tools.addWidget(preset_button)
        tools.addSpacing(18)
        tools.addWidget(QLabel("Search"))
        self.search_edit = QLineEdit()
        self.search_edit.returnPressed.connect(self.render_options)
        tools.addWidget(self.search_edit, 1)
        filter_button = QPushButton("Filter")
        filter_button.clicked.connect(self.render_options)
        tools.addWidget(filter_button)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_filter)
        tools.addWidget(clear_button)
        tools.addSpacing(12)
        self.reset_button = QPushButton("Reset Selected")
        self.reset_button.setEnabled(False)
        self.reset_button.clicked.connect(self.reset_selected_setting)
        tools.addWidget(self.reset_button)
        self.section_meta = QLabel("")
        self.section_meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tools.addWidget(self.section_meta)
        main_layout.addWidget(self.tools_panel)

        self.tree = QTreeWidget()
        self.tree.setObjectName("optionsTree")
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Option", "Source", "Value"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(False)
        self.tree.setAnimated(True)
        self.tree.header().setStretchLastSection(True)
        self.tree.setColumnWidth(0, 430)
        self.tree.setColumnWidth(1, 300)
        self.tree.itemSelectionChanged.connect(self.update_reset_button_state)
        main_layout.addWidget(self.tree, 1)
        self.tools_panel.hide()
        self.tree.hide()
        body.addWidget(main, 1)

        footer = QFrame()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 5, 8, 5)
        reload_settings = QPushButton("Reload Settings")
        reload_settings.clicked.connect(self.reload_profiles)
        footer_layout.addWidget(reload_settings)
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_all)
        footer_layout.addWidget(self.save_button)
        self.lock_toggle_button = QPushButton("Unlock Files")
        self.lock_toggle_button.clicked.connect(self.toggle_file_lock)
        footer_layout.addWidget(self.lock_toggle_button)
        self.status_label = QLabel("Select the game folder.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        footer_layout.addWidget(self.status_label, 1)
        self.dirty_label = QLabel("")
        self.dirty_label.setStyleSheet("color: #ffa500; font-weight: bold; margin-left: 10px; margin-right: 10px;")
        self.dirty_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer_layout.addWidget(self.dirty_label)
        about = QPushButton("About...")
        about.clicked.connect(self.show_about)
        footer_layout.addWidget(about)
        restore = QPushButton("Restore Backup")
        restore.clicked.connect(self.restore_latest_backup)
        footer_layout.addWidget(restore)
        open_backups = QPushButton("Open Backups")
        open_backups.clicked.connect(self.open_backup_folder)
        footer_layout.addWidget(open_backups)
        layout.addWidget(footer)

        self.toast_label = QLabel(root)
        self.toast_label.setObjectName("toast")
        self.toast_label.hide()

        self.setStyleSheet(
            """
            QWidget#root, QWidget#mainPanel {
                background: #111418;
                color: #e8edf2;
            }
            QFrame#header {
                background: #050607;
            }
            QLabel#headerTitle {
                color: white;
            }
            QFrame#topBar {
                background: #171b20;
                border-bottom: 1px solid #2a3037;
                color: #e8edf2;
            }
            QListWidget#sidebar {
                background: #161b21;
                border: 0;
                color: #dce3ea;
                outline: 0;
            }
            QListWidget#sidebar::item {
                padding: 12px 20px;
            }
            QListWidget#sidebar::item:selected {
                background: #c8102e;
                color: white;
                font-weight: 700;
            }
            QTreeWidget#optionsTree {
                background: #111418;
                alternate-background-color: #151a20;
                color: #e8edf2;
                border: 1px solid #2a3037;
                gridline-color: #2a3037;
                selection-background-color: #2b3a48;
                selection-color: #ffffff;
            }
            QTreeWidget#optionsTree::item {
                padding: 4px;
            }
            QTreeWidget#optionsTree::branch {
                background: transparent;
            }
            QHeaderView::section {
                background: #20262e;
                color: #f2f5f7;
                padding: 6px;
                border: 0;
                border-right: 1px solid #2a3037;
                font-weight: 700;
            }
            QLabel#sectionTitle {
                font-size: 20px;
                font-weight: 700;
                color: #f2f5f7;
            }
            QLabel#homeTitle {
                font-size: 30px;
                font-weight: 700;
                color: #ffffff;
            }
            QLabel#homeCopy {
                color: #b8c2cc;
                font-size: 14px;
                max-width: 620px;
            }
            QLabel#toast {
                background: #203528;
                color: #ffffff;
                border: 1px solid #2fbf77;
                border-radius: 6px;
                padding: 10px 14px;
                font-weight: 700;
            }
            QFrame#sectionRule {
                color: #343c46;
                background: #343c46;
                max-height: 1px;
            }
            QFrame#footer {
                background: #171b20;
                border-top: 1px solid #2a3037;
                color: #e8edf2;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background: #0c0f12;
                color: #f2f5f7;
                border: 1px solid #3a4652;
                padding: 3px 5px;
            }
            QPushButton {
                background: #232a32;
                color: #f2f5f7;
                border: 1px solid #4a5562;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background: #303946;
            }
            QPushButton[lockState="locked"] {
                background: #8a1f2d;
                border-color: #c8102e;
                color: #ffffff;
            }
            QPushButton[lockState="locked"]:hover {
                background: #a82737;
            }
            QPushButton[lockState="unlocked"] {
                background: #1f6f4a;
                border-color: #2fbf77;
                color: #ffffff;
            }
            QPushButton[lockState="unlocked"]:hover {
                background: #26895b;
            }
            QPushButton[lockState="disabled"] {
                background: #1f252c;
                border-color: #343c46;
                color: #808a94;
            }
            QCheckBox {
                color: #e8edf2;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #303946;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
                background: #c8102e;
            }
            QScrollBar:vertical {
                background: #111418;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background: #3a4652;
                min-height: 24px;
            }
            """
        )

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.position_toast()

    def position_toast(self) -> None:
        if not hasattr(self, "toast_label"):
            return
        parent = self.centralWidget()
        if not parent:
            return
        self.toast_label.adjustSize()
        margin = 18
        x = max(margin, parent.width() - self.toast_label.width() - margin)
        y = max(margin, parent.height() - self.toast_label.height() - 54)
        self.toast_label.move(x, y)

    def show_toast(self, message: str) -> None:
        self.toast_label.setText(message)
        self.position_toast()
        self.toast_label.show()
        self.toast_label.raise_()
        QTimer.singleShot(2000, self.toast_label.hide)

    def show_home_screen(self) -> None:
        self.controls.clear()
        self.tree.clear()
        self.section_meta.setText("")
        self.section_title.hide()
        self.section_rule.hide()
        self.home_panel.show()
        self.tools_panel.hide()
        self.tree.hide()

    def show_options_screen(self) -> None:
        self.section_title.show()
        self.section_rule.show()
        self.home_panel.hide()
        self.tools_panel.show()
        self.tree.show()

    def files_have_readonly(self) -> bool:
        return bool(self.documents) and any(is_readonly(doc.path) for doc in self.documents)

    def set_home_message(self, title: str, copy: str) -> None:
        if hasattr(self, "home_title") and hasattr(self, "home_copy"):
            self.home_title.setText(title)
            self.home_copy.setText(copy)

    def update_save_button(self) -> None:
        if not hasattr(self, "save_button"):
            return
        if not self.documents:
            self.save_button.setEnabled(False)
            self.save_button.setToolTip("Load a valid profile to save settings.")
        elif self.files_have_readonly():
            self.save_button.setEnabled(False)
            self.save_button.setToolTip("Unlock files before saving.")
        else:
            self.save_button.setEnabled(True)
            self.save_button.setToolTip("")

    def update_lock_button(self) -> None:
        if not hasattr(self, "lock_toggle_button"):
            return
        if not self.documents:
            self.lock_toggle_button.setText("Unlock Files")
            self.lock_toggle_button.setEnabled(False)
            self.lock_toggle_button.setProperty("lockState", "disabled")
        elif self.files_have_readonly():
            self.lock_toggle_button.setText("Unlock Files")
            self.lock_toggle_button.setEnabled(True)
            self.lock_toggle_button.setProperty("lockState", "locked")
        else:
            self.lock_toggle_button.setText("Lock Files")
            self.lock_toggle_button.setEnabled(True)
            self.lock_toggle_button.setProperty("lockState", "unlocked")
        self.lock_toggle_button.style().unpolish(self.lock_toggle_button)
        self.lock_toggle_button.style().polish(self.lock_toggle_button)
        self.lock_toggle_button.update()
        self.update_save_button()

    def has_unsaved_changes(self) -> bool:
        return bool(self.changed_entries(capture=True))

    def changed_entries(self, capture: bool = True) -> dict[tuple[str, int], tuple[ConfigDocument, ConfigEntry]]:
        if capture:
            self.capture_visible_controls(validate=False)
        changed = {}
        for doc in self.documents:
            for entry in doc.entries:
                key = (doc.label, entry.line_index)
                baseline = self.loaded_values.get(key)
                if baseline is not None and entry.value != baseline:
                    changed[key] = (doc, entry)
        return changed

    def snapshot_loaded_values(self) -> None:
        self.loaded_values.clear()
        for doc in self.documents:
            for entry in doc.entries:
                self.loaded_values[(doc.label, entry.line_index)] = entry.value

    def update_dirty_indicator(self, capture: bool = True) -> None:
        if not self.documents:
            self.dirty_label.setText("")
            return
        changed = self.changed_entries(capture=capture)
        if changed:
            count = len(changed)
            self.dirty_label.setText(f"Unsaved changes ({count})")
        else:
            self.dirty_label.setText("")

    def on_value_edited(self) -> None:
        if self.is_rendering:
            return
        self.update_dirty_indicator()

    def on_profile_changed(self) -> None:
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                blocked = self.profile_combo.blockSignals(True)
                if self.current_profile:
                    self.profile_combo.setCurrentText(self.current_profile)
                self.profile_combo.blockSignals(blocked)
                return
        self.current_profile = self.profile_combo.currentText()
        self.load_documents()

    def choose_game_dir(self) -> None:
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        selected = QFileDialog.getExistingDirectory(self, "Select the Call of Duty MWII folder", self.folder_edit.text())
        if selected:
            self.folder_edit.setText(selected)
            self.reload_profiles(auto=True)

    def reload_profiles(self, auto: bool = False) -> None:
        if not auto and self.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.game_dir = pathlib.Path(self.folder_edit.text())
        profiles = discover_profiles(self.game_dir)
        if not profiles and auto:
            fallback = pathlib.Path.cwd()
            if (fallback / "players").exists():
                self.game_dir = fallback
                self.folder_edit.setText(str(fallback))
                profiles = discover_profiles(fallback)

        blocked = self.profile_combo.blockSignals(True)
        current = self.profile_combo.currentText()
        self.profile_combo.clear()
        self.profile_combo.addItems(profiles)
        if current in profiles:
            self.profile_combo.setCurrentText(current)
        self.profile_combo.blockSignals(blocked)

        if profiles:
            self.load_documents()
        else:
            self.documents = []
            self.loaded_values.clear()
            self.update_dirty_indicator(capture=False)
            self.render_options(capture=False)
            
            players_dir = self.game_dir / "players"
            if not players_dir.exists():
                self.set_home_message(
                    "MWII Players Folder Not Found",
                    "No 'players' folder was found at the selected path:\n"
                    f"{players_dir}\n\n"
                    "Guidance: Please make sure the Call of Duty MWII directory is correct. "
                    "Use the Browse button to locate the folder, or run the game once to create it."
                )
            else:
                self.set_home_message(
                    "No Campaign Profile Found",
                    "The 'players' folder exists, but no campaign profiles were found.\n\n"
                    "Guidance: The campaign may need to be launched at least once. "
                    "Close the game, then click Reload or browse for the folder."
                )
            self.set_status("No valid profile found under players\\<profile-id>.")
            self.update_lock_button()

    def load_documents(self) -> None:
        profile = self.profile_combo.currentText()
        self.current_profile = profile
        if not profile:
            return
        try:
            validate_game_dir(self.game_dir, profile)
            self.documents = [ConfigDocument.load(path, label) for path, label in target_paths(self.game_dir, profile)]
            self.enforce_hardware_constraints()
            
            self.snapshot_loaded_values()
            self.update_dirty_indicator(capture=False)
            self.set_home_message(
                "MW2 Campaign Configurator",
                "Edit campaign-effective Modern Warfare II settings files, manage presets, and control file locking from one portable tool."
            )
            
            readonly = ", ".join(f"{doc.label}: {'RO' if is_readonly(doc.path) else 'RW'}" for doc in self.documents)
            total = sum(len(doc.entries) for doc in self.documents)
            self.set_status(f"{total} options loaded. {readonly}")
            self.render_options(capture=False)
            self.update_lock_button()
        except FileNotFoundError as exc:
            self.documents = []
            self.loaded_values.clear()
            self.update_dirty_indicator(capture=False)
            self.set_home_message(
                "Required Configuration Files Missing",
                f"{str(exc)}\n\n"
                "Guidance: Make sure the campaign has been launched once to generate default configuration files. "
                "Click Reload after they are created."
            )
            self.set_status("Required files missing for profile.")
            self.render_options(capture=False)
            self.update_lock_button()
        except Exception as exc:
            self.documents = []
            self.loaded_values.clear()
            self.update_dirty_indicator(capture=False)
            self.set_home_message(
                "Error Loading Documents",
                f"An unexpected error occurred while loading files:\n{str(exc)}"
            )
            self.render_options(capture=False)
            self.update_lock_button()
            QMessageBox.critical(self, APP_TITLE, str(exc))

    def all_entries(self) -> list[ConfigEntry]:
        return [entry for doc in self.documents for entry in doc.entries]

    def entry_by_token(self, token: str) -> ConfigEntry | None:
        for entry in self.all_entries():
            if entry.token == token:
                return entry
        return None

    def entry_by_key(self, key: str) -> ConfigEntry | None:
        for entry in self.all_entries():
            if entry.key == key:
                return entry
        return None

    def current_monitor_value(self) -> str:
        widget = self.controls.get(("Options", self.entry_by_key("Monitor").line_index)) if self.entry_by_key("Monitor") else None
        if isinstance(widget, QComboBox):
            data = widget.currentData()
            return str(data) if data is not None else widget.currentText()
        entry = self.entry_by_key("Monitor")
        return entry.value if entry else ""

    def selected_display(self) -> DisplayInfo | None:
        if not self.displays:
            return None
        current = self.current_monitor_value()
        for display in self.displays:
            if current in {display.name, display.device_name, self.display_label_for_monitor(display)}:
                return display
        return self.displays[0]

    @staticmethod
    def display_label_for_monitor(display: DisplayInfo) -> str:
        return f"{display.name} ({display.device_name})" if display.device_name else display.name

    def resolution_choices(self) -> list[str]:
        display = self.selected_display()
        if not display:
            return []
        choices = []
        for mode in display.modes:
            if mode.resolution not in choices:
                choices.append(mode.resolution)
        current = self.entry_by_key("Resolution")
        if current and current.value and current.value not in choices:
            choices.insert(0, current.value)
        return choices

    def refresh_choices(self) -> list[tuple[str, str]]:
        display = self.selected_display()
        resolution = self.entry_by_key("Resolution")
        selected_resolution = resolution.value if resolution else ""
        widget = self.controls.get(("Options", resolution.line_index)) if resolution else None
        if isinstance(widget, QComboBox):
            selected_resolution = widget.currentText()
        if not display or not selected_resolution:
            return []
        rates = sorted(
            {mode.refresh_rate for mode in display.modes if mode.resolution == selected_resolution},
            reverse=True,
        )
        choices = [(f"{rate} Hz", str(rate)) for rate in rates]
        current = self.entry_by_key("RefreshRate")
        if current and current.value:
            current_int = str(int(round(float(current.value)))) if self.is_number(current.value) else current.value
            if current.value not in {value for _, value in choices} and current_int not in {value for _, value in choices}:
                choices.insert(0, (f"{current.value} Hz (current config)", current.value))
        return choices

    @staticmethod
    def is_number(value: str) -> bool:
        try:
            float(value)
        except ValueError:
            return False
        return True

    def gpu_name(self) -> str:
        entry = self.entry_by_token("GPUName:0.0")
        return entry.value if entry else ""

    def has_rtx_gpu(self) -> bool:
        return is_rtx_gpu_name(self.gpu_name())

    def aa_entries(self) -> list[ConfigEntry]:
        return [entry for entry in self.all_entries() if entry.key == "AATechniquePreferred"]

    def amd_super_resolution_entry(self) -> ConfigEntry | None:
        return self.entry_by_token("AMDSuperResolution:0.0")

    def unified_aa_choices(self) -> list[str]:
        choices: list[str] = []
        for entry in self.aa_entries():
            for choice in entry.choices:
                label = "FSR 2.0" if choice == "FSR2" else choice
                if label not in choices:
                    choices.append(label)

        amd_entry = self.amd_super_resolution_entry()
        if amd_entry:
            for choice in amd_entry.choices:
                if choice != "Off" and choice not in choices:
                    choices.append(choice)

        if not self.has_rtx_gpu():
            choices = [choice for choice in choices if choice not in RTX_ONLY_AA_CHOICES]
        return choices

    def current_aa_label(self) -> str:
        amd_entry = self.amd_super_resolution_entry()
        if amd_entry and amd_entry.value in {"AMD FSR 1.0", "CAS - Sharpening only"}:
            return amd_entry.value

        preferred = self.entry_by_token("AATechniquePreferred:0.1") or self.entry_by_token("AATechniquePreferred:0.0")
        if not preferred:
            return ""
        label = choice_label_for_value(preferred, preferred.value)
        return "FSR 2.0" if label == "FSR2" else label

    def set_choice_if_supported(self, entry: ConfigEntry, label: str) -> bool:
        raw_label = "FSR2" if label == "FSR 2.0" else label
        if raw_label not in entry.choices:
            return False
        entry.value = choice_value_for_label(entry, raw_label)
        return True

    def set_unified_aa_selection(self, label: str) -> None:
        amd_entry = self.amd_super_resolution_entry()
        if amd_entry:
            if label in {"AMD FSR 1.0", "CAS - Sharpening only"}:
                amd_entry.value = label
            elif "Off" in amd_entry.choices:
                amd_entry.value = "Off"

        aa_label = "FSR 2.0" if label == "FSR 2.0" else label
        if label in {"AMD FSR 1.0", "CAS - Sharpening only"}:
            aa_label = "SMAA T2x"

        for entry in self.aa_entries():
            self.set_choice_if_supported(entry, aa_label)

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
        if self.current_aa_label() in RTX_ONLY_AA_CHOICES:
            self.set_unified_aa_selection("SMAA T2x")

    def entries_by_section(self) -> dict[str, list[tuple[ConfigDocument, ConfigEntry]]]:
        needle = self.search_edit.text().strip().lower()
        grouped: dict[str, list[tuple[ConfigDocument, ConfigEntry]]] = {}
        selected_aa = self.current_aa_label()
        normal_mode = self.mode_combo.currentText() == "Normal"
        for doc in self.documents:
            for entry in doc.entries:
                if not is_entry_visible_for_aa(entry, selected_aa):
                    continue
                if normal_mode and not is_normal_mode_entry(entry):
                    continue
                haystack = " ".join([entry.key, entry.description, entry.section, doc.label]).lower()
                if needle and needle not in haystack:
                    continue
                section = "Graphics" if entry.key == "AATechniquePreferred" or entry.key in UPSCALER_CONFIG_KEYS else entry.section
                grouped.setdefault(section, []).append((doc, entry))
        return grouped

    def clear_filter(self) -> None:
        self.search_edit.clear()
        self.render_options()

    def select_section(self, section: str) -> None:
        if not section:
            return
        if section == self.current_section and self.controls:
            return
        self.current_section = section
        self.render_options()

    def render_sidebar(self, sections: list[str]) -> None:
        blocked = self.sidebar.blockSignals(True)
        self.sidebar.clear()
        for section in sections:
            QListWidgetItem(section, self.sidebar)
        matches = self.sidebar.findItems(self.current_section, Qt.MatchFlag.MatchExactly)
        if matches:
            self.sidebar.setCurrentItem(matches[0])
        else:
            self.sidebar.clearSelection()
            self.sidebar.setCurrentRow(-1)
        self.sidebar.blockSignals(blocked)

    def render_options(self, capture: bool = True) -> None:
        if capture:
            self.capture_visible_controls(validate=False)
        self.is_rendering = True
        try:
            self.controls.clear()
            self.tree.clear()
            normal_mode = self.mode_combo.currentText() == "Normal"
            self.tree.setColumnHidden(1, normal_mode)

            grouped = self.entries_by_section()
            if not grouped:
                self.render_sidebar([])
                QTreeWidgetItem(self.tree, ["No options loaded.", "", ""])
                self.section_title.setText("Settings")
                self.section_meta.setText("")
                if self.documents:
                    self.show_options_screen()
                else:
                    self.show_home_screen()
                return

            sections = sorted(grouped)
            self.render_sidebar(sections)
            if not self.current_section:
                self.show_home_screen()
                return
            if self.current_section not in grouped:
                self.current_section = ""
                self.render_sidebar(sections)
                self.show_home_screen()
                return

            entries = grouped[self.current_section]
            self.section_title.setText(self.current_section)
            mode_note = self.mode_combo.currentText()
            self.section_meta.setText(f"{len(entries)} options · {mode_note}")
            self.show_options_screen()

            by_subcategory: dict[str, list[tuple[ConfigDocument, ConfigEntry]]] = {}
            for doc, entry in entries:
                by_subcategory.setdefault(entry_subcategory(entry), []).append((doc, entry))

            for subcategory, sub_entries in sorted(by_subcategory.items()):
                parent = QTreeWidgetItem(self.tree, [subcategory, "", ""])
                parent.setFirstColumnSpanned(True)
                parent.setExpanded(True)
                parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                for doc, entry in sub_entries:
                    label = self.display_label(entry)
                    item = QTreeWidgetItem(parent, [label, f"{doc.label} / {entry.token}", ""])
                    item.setToolTip(0, entry.key)
                    item.setData(0, Qt.ItemDataRole.UserRole, (doc.label, entry.line_index))
                    self.tree.setItemWidget(item, 2, self.create_value_widget(doc, entry))

            self.tree.expandAll()
            if normal_mode:
                self.tree.setColumnWidth(0, 620)
            else:
                self.tree.setColumnWidth(0, 430)
                self.tree.setColumnWidth(1, 300)
        finally:
            self.is_rendering = False
            self.update_reset_button_state()

    def display_label(self, entry: ConfigEntry) -> str:
        if self.mode_combo.currentText() == "Normal":
            return NORMAL_LABELS.get(entry.key, entry.description or entry.key)
        return entry.description or entry.key

    def create_value_widget(self, doc: ConfigDocument, entry: ConfigEntry) -> QWidget:
        key = (doc.label, entry.line_index)
        if entry.key == "Monitor" and self.displays:
            widget = QComboBox()
            for display in self.displays:
                widget.addItem(self.display_label_for_monitor(display), display.name)
            current_index = 0
            for index, display in enumerate(self.displays):
                if entry.value in {display.name, display.device_name, self.display_label_for_monitor(display)}:
                    current_index = index
                    break
            widget.setCurrentIndex(current_index)
            widget.currentTextChanged.connect(lambda _value, item=entry, combo=widget: self.on_monitor_changed(item, combo))
            widget.currentIndexChanged.connect(lambda _: self.on_value_edited())
        elif entry.key == "Resolution" and self.resolution_choices():
            widget = QComboBox()
            widget.addItems(self.resolution_choices())
            if entry.value:
                widget.setCurrentText(entry.value)
            widget.currentTextChanged.connect(lambda value, item=entry: self.on_resolution_changed(item, value))
            widget.currentIndexChanged.connect(lambda _: self.on_value_edited())
        elif entry.key == "RefreshRate" and self.refresh_choices():
            widget = QComboBox()
            for label, value in self.refresh_choices():
                widget.addItem(label, value)
            current_value = entry.value
            for index in range(widget.count()):
                data = str(widget.itemData(index))
                if data == current_value or (self.is_number(data) and self.is_number(current_value) and int(float(data)) == int(round(float(current_value)))):
                    widget.setCurrentIndex(index)
                    break
            widget.currentIndexChanged.connect(lambda _: self.on_value_edited())
        elif entry.kind == "bool":
            widget = QCheckBox()
            widget.setChecked(entry.value == "true")
            widget.toggled.connect(lambda _: self.on_value_edited())
        elif entry.kind == "choice":
            widget = QComboBox()
            choices = self.unified_aa_choices() if entry.key == "AATechniquePreferred" else filtered_aa_choices(entry, self.has_rtx_gpu())
            widget.addItems(choices)
            current = self.current_aa_label() if entry.key == "AATechniquePreferred" else display_value_for_entry(entry)
            if entry.key == "AATechniquePreferred" and current not in choices and choices:
                current = choices[0]
                self.set_unified_aa_selection(current)
            widget.setCurrentText(current)
            if entry.key == "AATechniquePreferred":
                widget.currentTextChanged.connect(lambda value, item=entry: self.on_aa_changed(item, value))
            widget.currentIndexChanged.connect(lambda _: self.on_value_edited())
        elif entry.kind == "range":
            if should_use_slider(entry):
                widget = SliderEditor(entry)
                widget.spin.valueChanged.connect(lambda _: self.on_value_edited())
            else:
                widget = QDoubleSpinBox()
                bounds = entry.range_bounds or (0.0, 1.0)
                widget.setRange(bounds[0], bounds[1])
                widget.setDecimals(0 if self.is_integerish(entry.value, bounds) else 6)
                widget.setSingleStep(self._range_step(bounds))
                try:
                    widget.setValue(float(entry.value))
                except ValueError:
                    widget.setValue(bounds[0])
                widget.valueChanged.connect(lambda _: self.on_value_edited())
        else:
            widget = QLineEdit(entry.value)
            widget.textChanged.connect(lambda _: self.on_value_edited())

        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.controls[key] = widget
        return widget

    @staticmethod
    def is_integerish(value: str, bounds: tuple[float, float]) -> bool:
        return "." not in value and bounds[0].is_integer() and bounds[1].is_integer()

    @staticmethod
    def _range_step(bounds: tuple[float, float]) -> float:
        span = bounds[1] - bounds[0]
        if span <= 2:
            return 0.01
        if span <= 20:
            return 0.1
        return 1

    def capture_visible_controls(self, validate: bool = True) -> None:
        if not self.controls:
            return
        by_key = {
            (doc.label, entry.line_index): entry
            for doc in self.documents
            for entry in doc.entries
        }
        for key, widget in self.controls.items():
            entry = by_key.get(key)
            if not entry:
                continue
            if isinstance(widget, QCheckBox):
                value = "true" if widget.isChecked() else "false"
            elif isinstance(widget, QComboBox):
                if entry.key == "AATechniquePreferred":
                    self.set_unified_aa_selection(widget.currentText())
                    continue
                data = widget.currentData()
                raw_value = str(data) if data is not None else widget.currentText()
                value = choice_value_for_label(entry, raw_value)
            elif isinstance(widget, QDoubleSpinBox):
                value = self.format_number(entry, widget.value())
            elif isinstance(widget, SliderEditor):
                value = self.format_number(entry, widget.value())
            elif isinstance(widget, QLineEdit):
                value = widget.text().strip()
            else:
                continue
            if validate and not entry.accepts(value):
                raise ValueError(f"Invalid value for {entry.token}: {value}")
            entry.value = value

    @staticmethod
    def format_number(entry: ConfigEntry, value: float) -> str:
        if "." in entry.value:
            decimals = len(entry.value.split(".", 1)[1])
            return f"{value:.{decimals}f}"
        return str(int(round(value)))

    def on_aa_changed(self, entry: ConfigEntry, value: str) -> None:
        self.set_unified_aa_selection(value)
        self.enforce_hardware_constraints()
        self.render_options(capture=False)

    def on_monitor_changed(self, entry: ConfigEntry, widget: QComboBox) -> None:
        data = widget.currentData()
        entry.value = str(data) if data is not None else widget.currentText()
        resolution = self.entry_by_key("Resolution")
        choices = self.resolution_choices()
        if resolution and choices and resolution.value not in choices:
            resolution.value = choices[0]
        refresh = self.entry_by_key("RefreshRate")
        refresh_choices = self.refresh_choices()
        if refresh and refresh_choices and refresh.value not in {value for _, value in refresh_choices}:
            refresh.value = refresh_choices[0][1]
        self.render_options(capture=False)

    def on_resolution_changed(self, entry: ConfigEntry, value: str) -> None:
        entry.value = value
        refresh = self.entry_by_key("RefreshRate")
        refresh_choices = self.refresh_choices()
        if refresh and refresh_choices:
            refresh.value = refresh_choices[0][1]
        self.render_options(capture=False)

    def apply_preset_to_ui(self) -> None:
        self.capture_visible_controls(validate=False)
        preset = PRESETS[self.preset_combo.currentText()]
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
                changed += 1
        self.enforce_hardware_constraints()
        self.render_options(capture=False)
        self.update_dirty_indicator()
        note = f"Preset loaded on screen: {changed} options."
        if skipped:
            note += f" Skipped by validation: {len(skipped)}."
        self.set_status(note)

    def update_reset_button_state(self) -> None:
        selected = self.tree.selectedItems()
        if not selected:
            self.reset_button.setEnabled(False)
            return
        item = selected[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is not None:
            self.reset_button.setEnabled(True)
        else:
            self.reset_button.setEnabled(False)

    def reset_selected_setting(self) -> None:
        selected = self.tree.selectedItems()
        if not selected:
            return
        item = selected[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        doc_label, line_index = data

        target_entry = None
        for doc in self.documents:
            if doc.label == doc_label:
                for entry in doc.entries:
                    if entry.line_index == line_index:
                        target_entry = entry
                        break

        if target_entry is None:
            return

        if target_entry.key == "AATechniquePreferred":
            for doc in self.documents:
                for entry in doc.entries:
                    if entry.key == "AATechniquePreferred" or entry.key == "AMDSuperResolution" or entry.key in UPSCALER_CONFIG_KEYS:
                        key = (doc.label, entry.line_index)
                        if key in self.loaded_values:
                            entry.value = self.loaded_values[key]
        else:
            key = (doc_label, line_index)
            if key in self.loaded_values:
                target_entry.value = self.loaded_values[key]

        self.enforce_hardware_constraints()
        self.render_options(capture=False)
        self.update_dirty_indicator()
        self.update_reset_button_state()

    def open_backup_folder(self) -> None:
        path = self.repo_dir / "backups"
        path.mkdir(parents=True, exist_ok=True)
        try:
            import os
            os.startfile(str(path))
        except Exception as exc:
            QMessageBox.critical(self, APP_TITLE, f"Failed to open backup folder:\n{str(exc)}")

    def save_all(self) -> None:
        if not self.documents:
            QMessageBox.warning(self, APP_TITLE, "Load a valid game folder before saving.")
            return
        if self.files_have_readonly():
            QMessageBox.critical(self, APP_TITLE, "Files are locked. Click Unlock Files before saving.")
            return
        try:
            self.capture_visible_controls(validate=True)
            backup_dir = backup_documents(self.documents, self.repo_dir)
            for doc in self.documents:
                for entry in doc.entries:
                    if not entry.accepts(entry.value):
                        raise ValueError(f"Invalid value for {entry.token}: {entry.value}")
                    doc.set_value(entry, entry.value)
                doc.save()
            self.load_documents()
            self.set_status(f"Settings saved. Backup: {backup_dir}")
            self.show_toast("Settings saved")
        except Exception as exc:
            QMessageBox.critical(self, APP_TITLE, str(exc))

    def toggle_file_lock(self) -> None:
        if not self.documents:
            self.set_status("Load a valid game folder before changing file locks.")
            return
        try:
            if self.files_have_readonly():
                for doc in self.documents:
                    make_writable(doc.path)
            else:
                for doc in self.documents:
                    make_readonly(doc.path)
            self.load_documents()
        except Exception as exc:
            QMessageBox.critical(self, APP_TITLE, str(exc))

    def restore_latest_backup(self) -> None:
        backups = sorted((self.repo_dir / "backups").glob("*"))
        backups = [item for item in backups if item.is_dir()]
        if not backups:
            QMessageBox.warning(self, APP_TITLE, "No backup found.")
            return
        latest = backups[-1]
        try:
            restore_backup(latest, self.documents)
            self.load_documents()
            QMessageBox.information(self, APP_TITLE, f"Backup restored: {latest}")
        except Exception as exc:
            QMessageBox.critical(self, APP_TITLE, str(exc))

    def show_help(self) -> None:
        QMessageBox.information(
            self,
            APP_TITLE,
            "Use the sidebar to browse categories.\n"
            "Mouse wheel scrolling is supported in the options panel.\n"
            "Unlock files before saving. Save Settings creates a backup and keeps the current file lock state.",
        )

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            APP_TITLE,
            "MW2 Campaign Configurator\n"
            "PyQt6 portable build.\n"
            "Edits only the campaign-effective files under players.",
        )


def main() -> None:
    app = QApplication(sys.argv)
    window = QtConfiguratorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
