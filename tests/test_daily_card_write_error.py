"""
Tests for daily_card() persistence write-failure handling (tarot-yc1).

Before the fix, the write of daily_card.json was unwrapped, so a disk
full / permission-denied / read-only-filesystem condition raised after
the card had already been drawn and displayed. The user would see their
card followed by a stack trace.

The fix mirrors save_reading(): wrap the write in try/except and emit a
non-fatal warning so the call returns normally.
"""

import builtins
import json

import pytest

import tarot


HEADER = "CARD OF THE DAY"
WARN_MARKER = "Could not save daily card"


@pytest.fixture
def isolated_daily_file(tmp_path, monkeypatch):
    target = tmp_path / "daily_card.json"
    monkeypatch.setattr(tarot, "DAILY_CARD_FILE", str(target))
    monkeypatch.setattr(tarot, "display_card", lambda *a, **k: None)
    return target


def _patch_open_write_to_raise(monkeypatch, target_path, exc):
    """Make open() raise exc when writing to target_path; pass through otherwise."""
    real_open = builtins.open
    target = str(target_path)

    def fake_open(file, mode='r', *args, **kwargs):
        if str(file) == target and 'w' in mode:
            raise exc
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)


def test_daily_card_returns_normally_when_write_fails_permission(
    isolated_daily_file, monkeypatch, capsys
):
    _patch_open_write_to_raise(
        monkeypatch, isolated_daily_file, PermissionError("read-only fs")
    )

    tarot.daily_card()

    out = capsys.readouterr().out
    assert out.count(HEADER) == 1
    assert WARN_MARKER in out
    assert not isolated_daily_file.exists()


def test_daily_card_returns_normally_when_write_fails_oserror(
    isolated_daily_file, monkeypatch, capsys
):
    _patch_open_write_to_raise(
        monkeypatch, isolated_daily_file, OSError("disk full")
    )

    tarot.daily_card()

    out = capsys.readouterr().out
    assert out.count(HEADER) == 1
    assert WARN_MARKER in out


def test_daily_card_success_path_still_saves(isolated_daily_file, capsys):
    """Sanity: when writes work, file is saved and no warning is printed."""
    tarot.daily_card()

    out = capsys.readouterr().out
    assert WARN_MARKER not in out
    assert isolated_daily_file.exists()
    data = json.loads(isolated_daily_file.read_text())
    assert "card_name" in data
