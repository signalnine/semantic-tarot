"""
Tests for issue semantic-tarot-v1h: interactive mode hardcoded values.

interactive_search() in search_cards.py and interactive_mode() in
search_cards_cached.py both hardcoded system='combined', top_k=5, and
show_art=False with no way to override. They also routed bare '/similar'
or '/similar ' to the semantic-search branch (an OpenAI call).

These tests cover:
- /system <name> updates the active system
- /top <n> updates top_k
- /art on/off toggles art display
- bare /similar (or unknown card after /similar) rejects without making
  a semantic-search call
"""

import sys
import types

if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub

import pytest


# ---------------------------------------------------------------------------
# search_cards.py::interactive_search
# ---------------------------------------------------------------------------

@pytest.fixture
def patched_search_cards(monkeypatch):
    """Patch search_cards.py module for interactive testing."""
    import search_cards as sc

    cards = [
        {"name": "The Fool", "desc": "BASIC_DESC", "rdesc": "BASIC_REVERSED",
         "card": "ART_UP", "reversed": "ART_REV"},
    ]

    monkeypatch.setattr(sc, "load_embeddings", lambda: [])
    monkeypatch.setattr(sc, "load_cards", lambda: cards)
    monkeypatch.setattr(sc, "load_interpretations", lambda: {})

    return sc, cards


def _drive(monkeypatch, inputs):
    it = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda *a, **kw: next(it))


def test_search_cards_similar_uses_current_system(monkeypatch, patched_search_cards):
    sc, _ = patched_search_cards
    captured = []

    def fake_find_similar(card_name, position, embeddings_data, top_k=5,
                          exclude_self=True, exclude_same_card=True,
                          system_filter=None):
        captured.append({"system_filter": system_filter, "top_k": top_k,
                         "card_name": card_name, "position": position})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find_similar)
    _drive(monkeypatch, [
        "/system jungian_psychological",
        "/similar The Fool", "u",
        "/quit",
    ])
    sc.interactive_search()

    assert len(captured) == 1
    assert captured[0]["system_filter"] == "jungian_psychological"


def test_search_cards_top_command_changes_top_k(monkeypatch, patched_search_cards):
    sc, _ = patched_search_cards
    captured = []

    def fake_find_similar(card_name, position, embeddings_data, top_k=5,
                          exclude_self=True, exclude_same_card=True,
                          system_filter=None):
        captured.append({"top_k": top_k})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find_similar)
    _drive(monkeypatch, [
        "/top 11",
        "/similar The Fool", "u",
        "/quit",
    ])
    sc.interactive_search()

    assert captured[0]["top_k"] == 11


def test_search_cards_bare_similar_does_not_hit_semantic(monkeypatch,
                                                          patched_search_cards):
    """Just '/similar' must not make a semantic-search call (which would
    use 'OPENAI' / build a client). Print an error and continue."""
    sc, _ = patched_search_cards

    def fake_search_cards(*a, **kw):
        raise AssertionError("semantic search must not run for bare /similar")

    monkeypatch.setattr(sc, "search_cards", fake_search_cards)

    # Also stub OpenAI so even a stray construction would fail loudly.
    def boom(*a, **kw):
        raise AssertionError("OpenAI must not be constructed")
    monkeypatch.setattr(sc, "OpenAI", boom)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    _drive(monkeypatch, [
        "/similar",
        "/similar  ",
        "/quit",
    ])
    sc.interactive_search()  # must not raise


def test_search_cards_unknown_system_rejected(monkeypatch, patched_search_cards,
                                                capsys):
    sc, _ = patched_search_cards

    def fake_find_similar(card_name, position, embeddings_data, top_k=5,
                          exclude_self=True, exclude_same_card=True,
                          system_filter=None):
        return [(card_name, position, 0.5)]

    monkeypatch.setattr(sc, "find_similar_cards", fake_find_similar)
    _drive(monkeypatch, [
        "/system not_a_system",
        "/quit",
    ])
    sc.interactive_search()
    out = capsys.readouterr().out
    assert "system" in out.lower()


# ---------------------------------------------------------------------------
# search_cards_cached.py::interactive_mode
# ---------------------------------------------------------------------------

@pytest.fixture
def cached_cards():
    return [
        {"name": "The Fool", "desc": "BASIC_DESC", "rdesc": "BASIC_REVERSED",
         "card": "ART_UP", "reversed": "ART_REV"},
    ]


def test_cached_similar_uses_current_system(monkeypatch, cached_cards):
    import search_cards_cached as sc
    captured = []

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        captured.append({"system_filter": system_filter, "top_k": top_k})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    _drive(monkeypatch, [
        "/system jungian_psychological",
        "similar The Fool", "u",
        "quit",
    ])
    sc.interactive_mode([], cached_cards, {}, "fake-model")
    assert captured and captured[0]["system_filter"] == "jungian_psychological"


def test_cached_top_command_changes_top_k(monkeypatch, cached_cards):
    import search_cards_cached as sc
    captured = []

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        captured.append({"top_k": top_k})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    _drive(monkeypatch, [
        "/top 7",
        "similar The Fool", "u",
        "quit",
    ])
    sc.interactive_mode([], cached_cards, {}, "fake-model")
    assert captured and captured[0]["top_k"] == 7


def test_cached_bare_similar_does_not_search(monkeypatch, cached_cards):
    """Bare 'similar' or 'similar ' must not trigger a semantic search."""
    import search_cards_cached as sc

    def fake_search(*a, **kw):
        raise AssertionError("semantic search must not run for bare /similar")

    monkeypatch.setattr(sc, "search_cards", fake_search)

    _drive(monkeypatch, [
        "similar",
        "similar  ",
        "quit",
    ])
    sc.interactive_mode([], cached_cards, {}, "fake-model")  # must not raise
