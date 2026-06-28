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
    is_rtx_gpu_name,
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
