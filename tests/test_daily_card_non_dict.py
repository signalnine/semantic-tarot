"""Tests for daily_card handling non-dict JSON payloads (bd ab7)."""

import json

import pytest

import tarot


@pytest.fixture
def isolated_daily_file(tmp_path, monkeypatch):
    target = tmp_path / "daily_card.json"
    monkeypatch.setattr(tarot, "DAILY_CARD_FILE", str(target))
    monkeypatch.setattr(tarot, "display_card", lambda *a, **k: None)
    return target


def _today():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def test_list_payload_does_not_raise_and_regenerates(isolated_daily_file, capsys):
    isolated_daily_file.write_text("[1,2,3]")

    tarot.daily_card()

    saved = json.loads(isolated_daily_file.read_text())
    assert isinstance(saved, dict)
    assert saved["date"] == _today()
    deck_names = {c["name"] for c in tarot.tarot_deck}
    assert saved["card_name"] in deck_names

    out = capsys.readouterr().out
    assert "Traceback" not in out
    assert "AttributeError" not in out


def test_string_payload_does_not_raise_and_regenerates(isolated_daily_file):
    isolated_daily_file.write_text(json.dumps("hello"))

    tarot.daily_card()

    saved = json.loads(isolated_daily_file.read_text())
    assert isinstance(saved, dict)
    assert saved["date"] == _today()


def test_number_payload_does_not_raise_and_regenerates(isolated_daily_file):
    isolated_daily_file.write_text("42")

    tarot.daily_card()

    saved = json.loads(isolated_daily_file.read_text())
    assert isinstance(saved, dict)


def test_null_payload_does_not_raise_and_regenerates(isolated_daily_file):
    isolated_daily_file.write_text("null")

    tarot.daily_card()

    saved = json.loads(isolated_daily_file.read_text())
    assert isinstance(saved, dict)
