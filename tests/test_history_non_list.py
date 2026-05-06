"""Tests for view_reading_history handling non-list JSON payloads (bd 5aa)."""

import glob
import json

import pytest

import tarot


@pytest.fixture
def isolated_history_file(tmp_path, monkeypatch):
    target = tmp_path / "reading_history.json"
    monkeypatch.setattr(tarot, "HISTORY_FILE", str(target))
    return target


def test_view_history_with_dict_payload_does_not_raise(isolated_history_file, capsys):
    isolated_history_file.write_text(json.dumps({"not": "a list"}))

    tarot.view_reading_history()

    out = capsys.readouterr().out
    assert "Error" not in out
    assert "Traceback" not in out
    backups = glob.glob(str(isolated_history_file) + ".bak.*")
    assert len(backups) == 1


def test_view_history_with_string_payload_does_not_raise(isolated_history_file, capsys):
    isolated_history_file.write_text(json.dumps("hello"))

    tarot.view_reading_history()

    out = capsys.readouterr().out
    assert "Error" not in out
    backups = glob.glob(str(isolated_history_file) + ".bak.*")
    assert len(backups) == 1


def test_view_history_with_number_payload_does_not_raise(isolated_history_file, capsys):
    isolated_history_file.write_text("42")

    tarot.view_reading_history()

    out = capsys.readouterr().out
    assert "Error" not in out
    backups = glob.glob(str(isolated_history_file) + ".bak.*")
    assert len(backups) == 1
