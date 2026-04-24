"""
Tests for view_reading_history() rendering of saved readings.

Covers:
- yes_no readings must surface the saved YES/NO answer.
- Card list rendering must not leave a trailing comma after the last card.
- Non-yes_no spreads still render without mentioning YES/NO.
"""

import json
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
