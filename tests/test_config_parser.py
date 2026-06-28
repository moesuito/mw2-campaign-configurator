import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mw2_campaign_configurator import ConfigDocument


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
