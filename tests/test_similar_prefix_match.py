"""Tests for tight /similar prefix match in interactive search (bd 1sr).

Mirrors search_cards_cached.py:446-447 which already does the right thing.
"""

import io

import pytest

import search_cards


@pytest.fixture
def patch_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def _run_with_input(monkeypatch, capsys, lines):
    inputs = iter(lines)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(inputs))
    try:
        search_cards.interactive_search()
    except StopIteration:
        pass
    return capsys.readouterr().out


def test_similars_not_routed_to_similar_branch(patch_no_api_key, monkeypatch, capsys):
    """`/similars` must NOT trigger the /similar branch's error messages."""
    out = _run_with_input(monkeypatch, capsys, ["/similars", "/quit"])
    assert "/similar requires a card name" not in out
    assert "Card not found" not in out


def test_similar2_not_routed_to_similar_branch(patch_no_api_key, monkeypatch, capsys):
    out = _run_with_input(monkeypatch, capsys, ["/similar2", "/quit"])
    assert "/similar requires a card name" not in out
    assert "Card not found" not in out


def test_similartothis_not_routed_to_similar_branch(patch_no_api_key, monkeypatch, capsys):
    out = _run_with_input(monkeypatch, capsys, ["/similartothis", "/quit"])
    assert "/similar requires a card name" not in out
    assert "Card not found" not in out


def test_bare_similar_still_prompts_for_card_name(patch_no_api_key, monkeypatch, capsys):
    out = _run_with_input(monkeypatch, capsys, ["/similar", "/quit"])
    assert "/similar requires a card name" in out


def test_similar_with_card_still_works(patch_no_api_key, monkeypatch, capsys):
    out = _run_with_input(
        monkeypatch, capsys,
        ["/similar The Fool", "u", "/quit"],
    )
    assert "Card not found" not in out
    assert "Finding cards similar" in out
