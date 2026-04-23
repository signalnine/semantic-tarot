"""
Tests that multi-card tarot readings draw distinct cards.

draw_card() uses random.choice() (with replacement). The multi-card
spreads called it in a loop, so the same card could repeat within one
reading. This verifies the fix: spreads now deal without replacement.
"""

import random

import pytest

import tarot


def test_draw_unique_cards_returns_distinct_cards():
    result = tarot.draw_unique_cards(10)
    assert len(result) == 10
    names = [card["name"] for card, _ in result]
    assert len(set(names)) == 10


def test_draw_unique_cards_honors_allow_reversed_false():
    result = tarot.draw_unique_cards(10, allow_reversed=False)
    assert len(result) == 10
    assert all(is_reversed is False for _, is_reversed in result)


def test_draw_unique_cards_rejects_n_larger_than_deck():
    with pytest.raises(ValueError):
        tarot.draw_unique_cards(len(tarot.tarot_deck) + 1)


def _run_spread(monkeypatch, spread_fn):
    """Run a reading with input() and display_card() stubbed out."""
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    monkeypatch.setattr(tarot, "display_card", lambda *a, **k: None)
    return spread_fn()


def test_three_card_reading_draws_unique_cards(monkeypatch):
    # seed 10 collides under the old with-replacement draw_card()
    random.seed(10)
    result = _run_spread(monkeypatch, tarot.three_card_reading)
    names = [name for name, _ in result["cards"]]
    assert len(names) == 3
    assert len(set(names)) == 3


def test_celtic_cross_draws_unique_cards(monkeypatch):
    # seed 4 collides under the old with-replacement draw_card()
    random.seed(4)
    result = _run_spread(monkeypatch, tarot.celtic_cross_reading)
    names = [name for name, _ in result["cards"]]
    assert len(names) == 10
    assert len(set(names)) == 10


def test_horseshoe_draws_unique_cards(monkeypatch):
    # seed 6 collides under the old with-replacement draw_card()
    random.seed(6)
    result = _run_spread(monkeypatch, tarot.horseshoe_reading)
    names = [name for name, _ in result["cards"]]
    assert len(names) == 7
    assert len(set(names)) == 7


def test_relationship_draws_unique_cards(monkeypatch):
    # seed 10 collides under the old with-replacement draw_card()
    random.seed(10)
    result = _run_spread(monkeypatch, tarot.relationship_reading)
    names = [name for name, _ in result["cards"]]
    assert len(names) == 5
    assert len(set(names)) == 5


def test_draw_card_single_tuple_unchanged():
    card, is_reversed = tarot.draw_card(allow_reversed=False)
    assert isinstance(card, dict)
    assert "name" in card
    assert is_reversed is False
