"""
Regression test for tarot-iyo: slash-command handlers must not eat queries
that just happen to start with the same letters (e.g. /topic, /article,
/systemd, /similarity).
"""

import sys
import types

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
        {"name": "The Fool", "desc": "u", "rdesc": "r",
         "card": "ART_UP", "reversed": "ART_REV"},
    ]


def _drive_cached(monkeypatch, inputs, cards):
    calls = {"find_similar": [], "search": []}

    def fake_search(query, embeddings_data, model, top_k=5,
                    position_filter=None, system_filter=None):
        calls["search"].append({"query": query, "top_k": top_k,
                                "system_filter": system_filter})
        return []

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        calls["find_similar"].append({"card_name": card_name,
                                       "position": position,
                                       "top_k": top_k})
        return []

    monkeypatch.setattr(search_cards_cached, "search_cards", fake_search)
    monkeypatch.setattr(search_cards_cached, "find_similar_cards", fake_find)

    input_iter = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda *a, **kw: next(input_iter))

    search_cards_cached.interactive_mode([], cards, {}, "fake-model")
    return calls


def test_cached_topic_query_falls_through_to_search(monkeypatch, cards):
    """'/topic 5' must not be misrouted to /top."""
    calls = _drive_cached(monkeypatch, ["/topic 5", "quit"], cards)
    assert calls["search"], "'/topic 5' should reach the search handler"
    assert calls["search"][0]["query"] == "/topic 5"
    assert calls["search"][0]["top_k"] == 5  # still default; not mutated by /top


def test_cached_article_query_falls_through_to_search(monkeypatch, cards):
    """'/article on' must not flip the art toggle."""
    calls = _drive_cached(monkeypatch, ["/article on", "quit"], cards)
    assert calls["search"], "'/article on' should reach the search handler"
    assert calls["search"][0]["query"] == "/article on"


def test_cached_systemd_query_falls_through_to_search(monkeypatch, cards):
    """'/systemd boot' must not reach the /system handler."""
    calls = _drive_cached(monkeypatch, ["/systemd boot", "quit"], cards)
    assert calls["search"], "'/systemd boot' should reach the search handler"
    assert calls["search"][0]["query"] == "/systemd boot"


def _drive_search(monkeypatch, inputs, cards):
    """Drive search_cards.interactive_search; api-key prompts return ''."""
    calls = {"find_similar": [], "search": []}

    def fake_search_cards_func(embeddings, cards_data, interpretations_data,
                               client, query, top_k, system, position=None):
        calls["search"].append({"query": query, "top_k": top_k,
                                "system": system})
        return []

    def fake_find(card_name, position, embeddings, top_k=5,
                  exclude_same_card=True, system=None, system_filter=None):
        calls["find_similar"].append({"card_name": card_name,
                                       "position": position})
        return []

    monkeypatch.setattr(search_cards, "search_cards", fake_search_cards_func)
    monkeypatch.setattr(search_cards, "find_similar_cards", fake_find)
    # Force the no-API-key fallthrough so search returns immediately.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    input_iter = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda *a, **kw: next(input_iter))

    # Bypass file loads by patching the loaders at module level.
    monkeypatch.setattr(search_cards, "load_embeddings", lambda: [])
    monkeypatch.setattr(search_cards, "load_cards", lambda: cards)
    monkeypatch.setattr(search_cards, "load_interpretations", lambda: {})

    search_cards.interactive_search()
    return calls


def test_search_cards_similarity_query_falls_through(monkeypatch, cards,
                                                     capsys):
    """'/similarity' must not be misrouted to /similar (which would error)."""
    # /similarity should fall through; with no API key, search prints a notice
    # rather than calling find_similar_cards.
    _drive_search(monkeypatch, ["/similarity", "/quit"], cards)
    out = capsys.readouterr().out
    assert "/similar requires a card name" not in out


def test_search_cards_topic_query_falls_through(monkeypatch, cards, capsys):
    """'/topic 5' must not be misrouted to /top (would mutate top_k)."""
    _drive_search(monkeypatch, ["/topic 5", "/quit"], cards)
    out = capsys.readouterr().out
    assert "Top set to:" not in out


def test_search_cards_article_query_falls_through(monkeypatch, cards, capsys):
    """'/article on' must not flip the art toggle."""
    _drive_search(monkeypatch, ["/article on", "/quit"], cards)
    out = capsys.readouterr().out
    assert "Art display:" not in out


def test_search_cards_systemd_query_falls_through(monkeypatch, cards, capsys):
    """'/systemd boot' must not reach the /system handler."""
    _drive_search(monkeypatch, ["/systemd boot", "/quit"], cards)
    out = capsys.readouterr().out
    assert "Unknown system:" not in out
    assert "System set to:" not in out
