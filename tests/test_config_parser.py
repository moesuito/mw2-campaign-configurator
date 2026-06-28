import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mw2_campaign_configurator import (
    ConfigDocument,
    choice_label_for_value,
    choice_value_for_label,
    filtered_aa_choices,
    is_entry_visible_for_aa,
    is_normal_mode_entry,
    is_rtx_gpu_name,
    should_use_slider,
)


def test_parse_and_update_preserves_line_shape(tmp_path):
    path = tmp_path / "options.3.cod22.cst"
    path.write_text(
        '0\n\n// Display\n\n// Fullscreen mode\n'
        'DisplayMode:0.0 = "Windowed" // one of [Windowed, Fullscreen]\n'
        '// Percentage\nResolutionMultiplier:0.0 = "75" // 0 to 200\n',
        encoding="utf-8",
    )

    doc = ConfigDocument.load(path, "Options")

    assert len(doc.entries) == 2
    assert doc.entries[0].section == "Display"
    assert doc.entries[0].kind == "choice"
    assert doc.entries[1].kind == "range"

    doc.set_value(doc.entries[0], "Fullscreen")
    doc.set_value(doc.entries[1], "100")

    assert 'DisplayMode:0.0 = "Fullscreen" // one of [Windowed, Fullscreen]' in doc.render()
    assert 'ResolutionMultiplier:0.0 = "100" // 0 to 200' in doc.render()


def test_entry_accepts_known_control_values(tmp_path):
    path = tmp_path / "settings.3.local.cod22.cst"
    path.write_text(
        '// Gameplay\n'
        'ADSFovScaling:0.0 = "false"\n'
        'Fov:0.0 = "105.000000" // 60.000000 to 120.000000\n',
        encoding="utf-8",
    )

    doc = ConfigDocument.load(path, "Settings")
    bool_entry, range_entry = doc.entries

    assert bool_entry.accepts("true")
    assert not bool_entry.accepts("yes")
    assert range_entry.accepts("120")
    assert not range_entry.accepts("121")


def test_index_backed_choice_displays_label_and_saves_index(tmp_path):
    path = tmp_path / "options.3.cod22.cst"
    path.write_text(
        '// Graphics\n'
        'AATechniquePreferred:0.1 = "2" // one of [SMAA T2x, Filmic SMAA T2x, DLSS, DLAA, XeSS, FSR2]\n',
        encoding="utf-8",
    )

    doc = ConfigDocument.load(path, "Options")
    entry = doc.entries[0]

    assert entry.stores_choice_index
    assert choice_label_for_value(entry, entry.value) == "DLSS"
    assert choice_value_for_label(entry, "FSR2") == "5"

    doc.set_value(entry, choice_value_for_label(entry, "FSR2"))
    assert 'AATechniquePreferred:0.1 = "5"' in doc.render()


def test_dlss_choices_require_rtx_gpu(tmp_path):
    path = tmp_path / "options.3.cod22.cst"
    path.write_text(
        '// Graphics\n'
        'AATechniquePreferred:0.0 = "DLSS" // one of [SMAA T2x, Filmic SMAA T2x, DLSS, DLAA, XeSS]\n'
        'DLSSPerfMode:0.0 = "Balanced" // one of [Ultra Performance, Maximum Performance, Balanced, Maximum Quality]\n'
        'XeSSQuality:0.0 = "Balanced" // one of [Maximum Performance, Balanced, Maximum Quality]\n',
        encoding="utf-8",
    )

    doc = ConfigDocument.load(path, "Options")
    aa_entry, dlss_entry, xess_entry = doc.entries

    assert is_rtx_gpu_name("NVIDIA GeForce RTX 3060 Laptop GPU")
    assert not is_rtx_gpu_name("NVIDIA GeForce GTX 1660")
    assert not is_rtx_gpu_name("AMD Radeon RX 7800 XT")
    assert "DLSS" not in filtered_aa_choices(aa_entry, has_rtx=False)
    assert "DLAA" not in filtered_aa_choices(aa_entry, has_rtx=False)
    assert is_entry_visible_for_aa(dlss_entry, "DLSS")
    assert not is_entry_visible_for_aa(xess_entry, "DLSS")
    assert is_entry_visible_for_aa(xess_entry, "XeSS")


def test_fsr_visibility_is_not_rtx_gated(tmp_path):
    path = tmp_path / "options.3.cod22.cst"
    path.write_text(
        '// Graphics\n'
        'AMDSuperResolution:0.0 = "Off" // one of [Off, CAS - Sharpening only, AMD FSR 1.0]\n'
        'AMDSuperResolutionQuality:0.0 = "Maximum Quality" // one of [Maximum Performance, Balanced, Maximum Quality, Ultra Quality]\n'
        'AATechniquePreferred:0.1 = "5" // one of [SMAA T2x, Filmic SMAA T2x, DLSS, DLAA, XeSS, FSR2]\n'
        'AMDSuperResolution2Quality:0.0 = "Balanced" // one of [Maximum Performance, Balanced, Maximum Quality, Ultra Quality]\n',
        encoding="utf-8",
    )

    doc = ConfigDocument.load(path, "Options")
    fsr1_toggle, fsr1_quality, fsr2_selector, fsr2_quality = doc.entries

    assert "FSR2" in filtered_aa_choices(fsr2_selector, has_rtx=False)
    assert is_entry_visible_for_aa(fsr1_quality, "AMD FSR 1.0")
    assert is_entry_visible_for_aa(fsr2_quality, "FSR 2.0")
    assert not is_entry_visible_for_aa(fsr1_toggle, "AMD FSR 1.0")


def test_normal_mode_and_slider_classification(tmp_path):
    path = tmp_path / "options.3.cod22.cst"
    path.write_text(
        '// Graphics\n'
        'ResolutionMultiplier:0.0 = "75" // 0 to 200\n'
        'StaticSunshadowClipmapResolution:0.0 = "1024" // 0 to 2147483647\n'
        'VirtualTexturingMemoryMode:0.1 = "Large" // one of [Extra Small, Small, Medium, Large, Extra Large]\n'
        '// Audio\n'
        'Volume:0.0 = "1.000000" // 0.000000 to 1.000000\n',
        encoding="utf-8",
    )

    doc = ConfigDocument.load(path, "Options")
    resolution, static_shadow, virtual_texture, volume = doc.entries

    assert is_normal_mode_entry(resolution)
    assert is_normal_mode_entry(volume)
    assert not is_normal_mode_entry(virtual_texture)
    assert should_use_slider(resolution)
    assert should_use_slider(volume)
    assert not should_use_slider(static_shadow)
