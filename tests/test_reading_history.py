"""
Tests for view_reading_history() rendering of saved readings.

Covers:
- yes_no readings must surface the saved YES/NO answer.
- Card list rendering must not leave a trailing comma after the last card.
- Non-yes_no spreads still render without mentioning YES/NO.
- save_reading must recover from a corrupt history file by backing it up.
- view_reading_history must skip malformed entries instead of aborting.
"""

import glob
import json
import os
import re

import pytest

import tarot


@pytest.fixture
def isolated_history_file(tmp_path, monkeypatch):
    target = tmp_path / "reading_history.json"
    monkeypatch.setattr(tarot, "HISTORY_FILE", str(target))
    return target


def _write(isolated_history_file, entries):
    isolated_history_file.write_text(json.dumps(entries))


def _strip_spread_name(out: str) -> str:
    """Remove 'YES_NO spread' substrings so YES/NO matches test only the answer."""
    return re.sub(r"YES_NO\s+spread", "", out)


def test_yes_no_reading_history_shows_no_answer(isolated_history_file, capsys):
    _write(
        isolated_history_file,
        [
            {
                "timestamp": "2025-01-01 12:00:00",
                "spread": "yes_no",
                "cards": [["The Fool", True]],
                "answer": "NO",
            }
        ],
    )

    tarot.view_reading_history()

    out = _strip_spread_name(capsys.readouterr().out)
    assert "NO" in out, "saved yes_no answer 'NO' must appear in history output"
    assert "YES" not in out, "answer was NO; YES must not appear"


def test_yes_no_reading_history_shows_yes_answer(isolated_history_file, capsys):
    _write(
        isolated_history_file,
        [
            {
                "timestamp": "2025-02-02 09:30:00",
                "spread": "yes_no",
                "cards": [["The Sun", False]],
                "answer": "YES",
            }
        ],
    )

    tarot.view_reading_history()

    out = _strip_spread_name(capsys.readouterr().out)
    assert "YES" in out


def test_history_card_list_has_no_trailing_comma(isolated_history_file, capsys):
    _write(
        isolated_history_file,
        [
            {
                "timestamp": "2025-03-03 10:00:00",
                "spread": "three_card",
                "cards": [
                    ["The Fool", False],
                    ["The Magician", True],
                    ["The Empress", False],
                ],
            }
        ],
    )

    tarot.view_reading_history()

    out = capsys.readouterr().out
    for line in out.splitlines():
        stripped = line.rstrip()
        if "The Empress" in stripped:
            assert not stripped.endswith(","), (
                f"card list line must not end with trailing comma: {stripped!r}"
            )
            break
    else:
        pytest.fail("card list line containing 'The Empress' not found in output")


def test_non_yes_no_reading_does_not_show_yes_no_answer(
    isolated_history_file, capsys
):
    _write(
        isolated_history_file,
        [
            {
                "timestamp": "2025-04-04 11:00:00",
                "spread": "three_card",
                "cards": [
                    ["The Fool", False],
                    ["The Magician", True],
                    ["The Empress", False],
                ],
            }
        ],
    )

    tarot.view_reading_history()

    out = capsys.readouterr().out
    assert "YES" not in out
    assert "NO" not in out


def test_save_reading_recovers_from_corrupt_history(isolated_history_file, capsys):
    isolated_history_file.write_text("garbage{ not json")

    new_reading = {
        "spread": "single_card",
        "cards": [["The Fool", False]],
    }
    tarot.save_reading(new_reading)

    saved = json.loads(isolated_history_file.read_text())
    assert isinstance(saved, list)
    assert len(saved) == 1
    assert saved[0]["spread"] == "single_card"
    assert saved[0]["cards"] == [["The Fool", False]]
    assert "timestamp" in saved[0]

    backups = glob.glob(str(isolated_history_file) + ".bak.*")
    assert len(backups) == 1, f"expected exactly one backup, got: {backups}"
    assert open(backups[0]).read() == "garbage{ not json"

    out = capsys.readouterr().out
    assert "saved" in out.lower()


def test_save_reading_after_recovery_appends_normally(isolated_history_file):
    isolated_history_file.write_text("{not even close to json")

    tarot.save_reading({"spread": "single_card", "cards": [["The Fool", False]]})
    tarot.save_reading({"spread": "single_card", "cards": [["The Sun", True]]})

    saved = json.loads(isolated_history_file.read_text())
    assert len(saved) == 2
    assert saved[0]["cards"] == [["The Fool", False]]
    assert saved[1]["cards"] == [["The Sun", True]]


def test_view_history_skips_malformed_entries(isolated_history_file, capsys):
    _write(
        isolated_history_file,
        [
            {"timestamp": "2025-01-01 10:00:00", "spread": "single"},
            {
                "timestamp": "2025-01-02 10:00:00",
                "spread": "three_card",
                "cards": [
                    ["The Fool", False],
                    ["The Magician", True],
                    ["The Empress", False],
                ],
            },
            {"spread": "single_card", "cards": [["The Sun", False]]},
            {
                "timestamp": "2025-01-03 10:00:00",
                "spread": "single_card",
                "cards": [["The Moon", True]],
            },
        ],
    )

    tarot.view_reading_history()

    out = capsys.readouterr().out
    assert "The Magician" in out, "valid entry after malformed entry must still render"
    assert "The Moon" in out, "valid entry after another malformed entry must render"
    assert "Error loading history" not in out, (
        "single malformed entry must not abort the whole view"
    )


def test_view_history_renders_when_first_entry_is_malformed(
    isolated_history_file, capsys
):
    _write(
        isolated_history_file,
        [
            {"timestamp": "2025-01-01 10:00:00"},
            {
                "timestamp": "2025-01-02 10:00:00",
                "spread": "single_card",
                "cards": [["The Star", False]],
            },
        ],
    )

    tarot.view_reading_history()

    out = capsys.readouterr().out
    assert "The Star" in out
    assert "Error loading history" not in out
