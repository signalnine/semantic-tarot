"""
Tests for the /include-same-card toggle in interactive modes
(tarot-8l0).

Both search_cards.py:interactive_search and
search_cards_cached.py:interactive_mode now accept a /include-same-card
toggle (with on|off, default off) that flips the exclude_same_card
kwarg passed to find_similar_cards(), giving interactive parity with
the --include-same-card CLI flag.
"""

import sys
import types

# search_cards_cached imports embedding_cache at module load.
if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub

import pytest

import search_cards
import search_cards_cached


@pytest.fixture
def cards():
    return [
        {"name": "The Fool", "desc": "New beginnings", "rdesc": "Folly",
         "card": "UPRIGHT", "reversed": "REVERSED"},
    ]


def _scripted_inputs(inputs):
    iterator = iter(inputs)
    return lambda *a, **kw: next(iterator)


# --- search_cards_cached.py:interactive_mode ---

def _run_cached(monkeypatch, inputs):
    calls = []

    def fake_find_similar(card_name, position, embeddings_data, top_k=5,
                          system_filter=None, exclude_same_card=True):
        calls.append({"exclude_same_card": exclude_same_card})
        return []

    monkeypatch.setattr(search_cards_cached, "find_similar_cards",
                        fake_find_similar)
    monkeypatch.setattr("builtins.input", _scripted_inputs(inputs))
    return calls


def test_cached_default_excludes_same_card(monkeypatch, cards):
    calls = _run_cached(
        monkeypatch,
        ["similar The Fool", "u", "quit"],
    )
    search_cards_cached.interactive_mode([], cards, {}, "fake-model")
    assert calls and calls[0]["exclude_same_card"] is True


def test_cached_include_same_card_on(monkeypatch, cards):
    calls = _run_cached(
        monkeypatch,
        ["/include-same-card on", "similar The Fool", "u", "quit"],
    )
    search_cards_cached.interactive_mode([], cards, {}, "fake-model")
    assert calls and calls[0]["exclude_same_card"] is False


def test_cached_include_same_card_off(monkeypatch, cards):
    """Toggle on then off should restore the default exclusion."""
    calls = _run_cached(
        monkeypatch,
        ["/include-same-card on", "/include-same-card off",
         "similar The Fool", "u", "quit"],
    )
    search_cards_cached.interactive_mode([], cards, {}, "fake-model")
    assert calls and calls[0]["exclude_same_card"] is True


def test_cached_include_same_card_bare_toggle(monkeypatch, cards):
    """Bare /include-same-card with no arg flips the flag."""
    calls = _run_cached(
        monkeypatch,
        ["/include-same-card", "similar The Fool", "u", "quit"],
    )
    search_cards_cached.interactive_mode([], cards, {}, "fake-model")
    assert calls and calls[0]["exclude_same_card"] is False


# --- search_cards.py:interactive_search ---

def _run_search(monkeypatch, inputs, cards):
    calls = []

    def fake_find_similar(card_name, position, embeddings_data, top_k=5,
                          exclude_self=True, exclude_same_card=True,
                          system_filter=None):
        calls.append({"exclude_same_card": exclude_same_card})
        return []

    monkeypatch.setattr(search_cards, "find_similar_cards",
                        fake_find_similar)
    monkeypatch.setattr(search_cards, "load_embeddings", lambda: [])
    monkeypatch.setattr(search_cards, "load_cards", lambda: cards)
    monkeypatch.setattr(search_cards, "load_interpretations", lambda: {})
    monkeypatch.setattr("builtins.input", _scripted_inputs(inputs))
    return calls


def test_search_default_excludes_same_card(monkeypatch, cards):
    calls = _run_search(
        monkeypatch,
        ["/similar The Fool", "u", "/quit"],
        cards,
    )
    search_cards.interactive_search()
    assert calls and calls[0]["exclude_same_card"] is True


def test_search_include_same_card_on(monkeypatch, cards):
    calls = _run_search(
        monkeypatch,
        ["/include-same-card on", "/similar The Fool", "u", "/quit"],
        cards,
    )
    search_cards.interactive_search()
    assert calls and calls[0]["exclude_same_card"] is False


def test_search_include_same_card_off(monkeypatch, cards):
    calls = _run_search(
        monkeypatch,
        ["/include-same-card on", "/include-same-card off",
         "/similar The Fool", "u", "/quit"],
        cards,
    )
    search_cards.interactive_search()
    assert calls and calls[0]["exclude_same_card"] is True


def test_search_include_same_card_bare_toggle(monkeypatch, cards):
    calls = _run_search(
        monkeypatch,
        ["/include-same-card", "/similar The Fool", "u", "/quit"],
        cards,
    )
    search_cards.interactive_search()
    assert calls and calls[0]["exclude_same_card"] is False
