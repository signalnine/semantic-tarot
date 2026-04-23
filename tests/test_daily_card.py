"""
Tests for daily_card() behavior.

Covers the invariant that the "CARD OF THE DAY" header is printed
exactly once per call, and that an invalid saved card_name for today's
date is handled cleanly instead of double-printing and silently
overwriting.
"""

import json
import os
from datetime import datetime, timedelta

import pytest

import tarot


HEADER = "CARD OF THE DAY"


@pytest.fixture
def isolated_daily_file(tmp_path, monkeypatch):
    """Point DAILY_CARD_FILE at a temp path and restore after."""
    target = tmp_path / "daily_card.json"
    monkeypatch.setattr(tarot, "DAILY_CARD_FILE", str(target))
    # Silence the card display; we only care about the header line here.
    monkeypatch.setattr(tarot, "display_card", lambda *a, **k: None)
    return target


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def test_valid_today_entry_prints_header_once_and_preserves_file(
    isolated_daily_file, capsys
):
    valid_name = tarot.tarot_deck[0]["name"]
    payload = {"date": _today(), "card_name": valid_name, "is_reversed": False}
    isolated_daily_file.write_text(json.dumps(payload))
    before = isolated_daily_file.read_text()

    tarot.daily_card()

    out = capsys.readouterr().out
    assert out.count(HEADER) == 1
    assert isolated_daily_file.read_text() == before


def test_invalid_today_entry_prints_header_once_and_rewrites_file(
    isolated_daily_file, capsys
):
    payload = {
        "date": _today(),
        "card_name": "NonexistentCardThatDoesNotExistInDeck",
        "is_reversed": False,
    }
    isolated_daily_file.write_text(json.dumps(payload))

    tarot.daily_card()

    out = capsys.readouterr().out
    assert out.count(HEADER) == 1, (
        f"header printed {out.count(HEADER)} times; expected 1"
    )

    saved = json.loads(isolated_daily_file.read_text())
    assert saved["date"] == _today()
    deck_names = {c["name"] for c in tarot.tarot_deck}
    assert saved["card_name"] in deck_names


def test_stale_date_entry_prints_header_once_and_regenerates(
    isolated_daily_file, capsys
):
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    valid_name = tarot.tarot_deck[0]["name"]
    payload = {"date": yesterday, "card_name": valid_name, "is_reversed": True}
    isolated_daily_file.write_text(json.dumps(payload))

    tarot.daily_card()

    out = capsys.readouterr().out
    assert out.count(HEADER) == 1

    saved = json.loads(isolated_daily_file.read_text())
    assert saved["date"] == _today()
    deck_names = {c["name"] for c in tarot.tarot_deck}
    assert saved["card_name"] in deck_names


def test_missing_file_prints_header_once_and_creates_file(
    isolated_daily_file, capsys
):
    assert not isolated_daily_file.exists()

    tarot.daily_card()

    out = capsys.readouterr().out
    assert out.count(HEADER) == 1

    saved = json.loads(isolated_daily_file.read_text())
    assert saved["date"] == _today()
    deck_names = {c["name"] for c in tarot.tarot_deck}
    assert saved["card_name"] in deck_names
