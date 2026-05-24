"""
Regression tests for semantic-tarot-j5l and semantic-tarot-oww:

interactive entry points in search_cards.py and search_cards_cached.py
must honor CLI flags --system, --top, --include-same-card, --ascii/--art
instead of silently resetting them to hardcoded defaults.
"""

import sys
import types

if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub

import pytest


def _drive(monkeypatch, inputs):
    it = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda *a, **kw: next(it))


# ---------------------------------------------------------------------------
# search_cards.py::interactive_search
# ---------------------------------------------------------------------------

@pytest.fixture
def patched_search_cards(monkeypatch):
    import search_cards as sc

    cards = [
        {"name": "The Fool", "desc": "BASIC_DESC", "rdesc": "BASIC_REVERSED",
         "card": "ART_UP", "reversed": "ART_REV"},
    ]

    monkeypatch.setattr(sc, "load_embeddings", lambda: [])
    monkeypatch.setattr(sc, "load_cards", lambda: cards)
    monkeypatch.setattr(sc, "load_interpretations", lambda: {})

    return sc, cards


def test_interactive_search_honors_system_argument(monkeypatch, patched_search_cards):
    sc, _ = patched_search_cards
    captured = []

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  exclude_self=True, exclude_same_card=True, system_filter=None):
        captured.append({"system_filter": system_filter, "top_k": top_k,
                         "exclude_same_card": exclude_same_card})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    _drive(monkeypatch, ["/similar The Fool", "u", "/quit"])
    sc.interactive_search(system="jungian_psychological")

    assert captured and captured[0]["system_filter"] == "jungian_psychological"


def test_interactive_search_honors_top_k_argument(monkeypatch, patched_search_cards):
    sc, _ = patched_search_cards
    captured = []

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  exclude_self=True, exclude_same_card=True, system_filter=None):
        captured.append({"top_k": top_k})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    _drive(monkeypatch, ["/similar The Fool", "u", "/quit"])
    sc.interactive_search(top_k=9)

    assert captured and captured[0]["top_k"] == 9


def test_interactive_search_honors_include_same_card_argument(monkeypatch,
                                                                patched_search_cards):
    sc, _ = patched_search_cards
    captured = []

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  exclude_self=True, exclude_same_card=True, system_filter=None):
        captured.append({"exclude_same_card": exclude_same_card})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    _drive(monkeypatch, ["/similar The Fool", "u", "/quit"])
    sc.interactive_search(include_same_card=True)

    assert captured and captured[0]["exclude_same_card"] is False


def test_interactive_search_honors_show_art_argument(monkeypatch,
                                                       patched_search_cards):
    sc, _ = patched_search_cards
    captured = []

    def fake_display(results, cards_data, output_format=None, system=None,
                     interpretations_data=None, show_art=False):
        captured.append({"show_art": show_art})

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  exclude_self=True, exclude_same_card=True, system_filter=None):
        return [(card_name, position, 0.5)]

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    monkeypatch.setattr(sc, "display_search_results", fake_display)
    _drive(monkeypatch, ["/similar The Fool", "u", "/quit"])
    sc.interactive_search(show_art=True)

    assert captured and captured[0]["show_art"] is True


def test_main_forwards_cli_flags_to_interactive_search(monkeypatch,
                                                         patched_search_cards):
    sc, _ = patched_search_cards
    captured = {}

    def fake_interactive(system='combined', top_k=5, show_art=False,
                         include_same_card=False):
        captured["system"] = system
        captured["top_k"] = top_k
        captured["show_art"] = show_art
        captured["include_same_card"] = include_same_card

    monkeypatch.setattr(sc, "interactive_search", fake_interactive)
    monkeypatch.setattr(sys, "argv", [
        "search_cards.py", "--interactive",
        "--system", "thoth_crowley",
        "--top", "7",
        "--include-same-card",
        "--ascii",
    ])

    sc.main()

    assert captured == {
        "system": "thoth_crowley",
        "top_k": 7,
        "show_art": True,
        "include_same_card": True,
    }


# ---------------------------------------------------------------------------
# search_cards_cached.py::interactive_mode
# ---------------------------------------------------------------------------

@pytest.fixture
def cached_cards():
    return [
        {"name": "The Fool", "desc": "BASIC_DESC", "rdesc": "BASIC_REVERSED",
         "card": "ART_UP", "reversed": "ART_REV"},
    ]


def test_cached_interactive_honors_top_k(monkeypatch, cached_cards):
    import search_cards_cached as sc
    captured = []

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        captured.append({"top_k": top_k, "exclude_same_card": exclude_same_card})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    _drive(monkeypatch, ["similar The Fool", "u", "quit"])
    sc.interactive_mode([], cached_cards, {}, "fake-model", top_k=8)

    assert captured and captured[0]["top_k"] == 8


def test_cached_interactive_honors_include_same_card(monkeypatch, cached_cards):
    import search_cards_cached as sc
    captured = []

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        captured.append({"exclude_same_card": exclude_same_card})
        return []

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    _drive(monkeypatch, ["similar The Fool", "u", "quit"])
    sc.interactive_mode([], cached_cards, {}, "fake-model",
                       include_same_card=True)

    assert captured and captured[0]["exclude_same_card"] is False


def test_cached_interactive_honors_show_art(monkeypatch, cached_cards):
    import search_cards_cached as sc
    captured = []

    def fake_format(results, cards, interpretations, show_ascii=False,
                    format_type='text', system='combined'):
        captured.append({"show_ascii": show_ascii})
        return ""

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        return [(card_name, position, 0.5)]

    monkeypatch.setattr(sc, "find_similar_cards", fake_find)
    monkeypatch.setattr(sc, "format_results", fake_format)
    _drive(monkeypatch, ["similar The Fool", "u", "quit"])
    sc.interactive_mode([], cached_cards, {}, "fake-model", show_art=True)

    assert captured and captured[0]["show_ascii"] is True


def test_cached_main_forwards_all_flags(monkeypatch, cached_cards):
    import search_cards_cached as sc
    captured = {}

    def fake_interactive(embeddings_data, cards, interpretations, model,
                         system='combined', top_k=5, show_art=False,
                         include_same_card=False):
        captured["system"] = system
        captured["top_k"] = top_k
        captured["show_art"] = show_art
        captured["include_same_card"] = include_same_card

    monkeypatch.setattr(sc, "interactive_mode", fake_interactive)
    monkeypatch.setattr(sc, "load_embeddings", lambda *a, **kw: ([], "fake-model"))
    monkeypatch.setattr(sc, "load_cards", lambda: cached_cards)
    monkeypatch.setattr(sc, "load_interpretations", lambda: {})
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py", "--interactive",
        "--system", "modern_intuitive",
        "--top", "12",
        "--include-same-card",
        "--ascii",
    ])

    sc.main()

    assert captured == {
        "system": "modern_intuitive",
        "top_k": 12,
        "show_art": True,
        "include_same_card": True,
    }
