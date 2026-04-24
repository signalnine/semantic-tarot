"""
Tests that `tarot.compare_interpretations` echoes the attempted card
name (stripped) when the lookup fails, matching `tarot.search_card`
and `search_cards.py --similar`.

Without this, a user running menu option 15 and mistyping a card name
sees only "Card not found." and has no way to spot the typo.
"""

import builtins

import pytest

import tarot


def _patch_inputs(monkeypatch, *responses):
    """Make `input(...)` return responses[i] on the i-th call."""
    iterator = iter(responses)

    def fake_input(prompt=""):
        return next(iterator)

    monkeypatch.setattr(builtins, "input", fake_input)


def test_compare_interpretations_unknown_echoes_name(monkeypatch, capsys):
    _patch_inputs(monkeypatch, "Not A Real Card", "u")
    tarot.compare_interpretations()
    out = capsys.readouterr().out
    assert "Not A Real Card" in out, (
        f"expected attempted name in output, got: {out!r}"
    )


def test_compare_interpretations_unknown_echoes_stripped_name(monkeypatch, capsys):
    _patch_inputs(monkeypatch, "   Bogus Card   ", "u")
    tarot.compare_interpretations()
    out = capsys.readouterr().out
    assert "Bogus Card" in out
    # Padding should not survive into the echoed message.
    assert "   Bogus Card   " not in out


def test_compare_interpretations_known_card_no_not_found(monkeypatch, capsys):
    _patch_inputs(monkeypatch, "The Fool", "u")
    tarot.compare_interpretations()
    out = capsys.readouterr().out
    assert "Card not found" not in out


def test_compare_interpretations_case_insensitive(monkeypatch, capsys):
    _patch_inputs(monkeypatch, "the fool", "u")
    tarot.compare_interpretations()
    out = capsys.readouterr().out
    assert "Card not found" not in out
    assert "The Fool" in out
