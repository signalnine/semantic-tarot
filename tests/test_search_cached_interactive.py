"""
Tests for interactive_mode() in search_cards_cached.py.

Bug semantic-tarot-evl: the `similar <card>` command in the cached
interactive REPL hardcoded position='upright', so users could not
explore similar cards for a reversed card. The non-cached variant
(search_cards.py::interactive_search) prompts for u/r and passes the
chosen position, so this test asserts parity.
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

import search_cards_cached


@pytest.fixture
def cards():
    return [
        {"name": "The Fool", "desc": "New beginnings", "rdesc": "Folly",
         "card": "UPRIGHT", "reversed": "REVERSED"},
    ]


@pytest.fixture
def embeddings():
    return []


def _run_interactive(monkeypatch, inputs, find_similar_impl=None):
    """Drive interactive_mode with a scripted input sequence."""
    calls = []

    def fake_find_similar(card_name, position, embeddings_data, top_k=5,
                          system_filter=None, exclude_same_card=True):
        calls.append({"card_name": card_name, "position": position,
                      "top_k": top_k, "system_filter": system_filter,
                      "exclude_same_card": exclude_same_card})
        if find_similar_impl is not None:
            return find_similar_impl(card_name, position)
        return []

    monkeypatch.setattr(search_cards_cached, "find_similar_cards",
                        fake_find_similar)

    input_iter = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda *a, **kw: next(input_iter))

    return calls


def test_similar_reversed_via_prompt(monkeypatch, cards, embeddings, capsys):
    """Typing 'r' at the position prompt selects reversed."""
    calls = _run_interactive(
        monkeypatch,
        ["similar The Fool", "r", "quit"],
    )
    search_cards_cached.interactive_mode(embeddings, cards, {}, "fake-model")
    assert len(calls) == 1, f"expected one find_similar_cards call, got {calls}"
    assert calls[0]["card_name"] == "The Fool"
    assert calls[0]["position"] == "reversed"


def test_similar_default_upright_on_empty_prompt(monkeypatch, cards,
                                                 embeddings):
    """Empty input at position prompt defaults to upright."""
    calls = _run_interactive(
        monkeypatch,
        ["similar The Fool", "", "quit"],
    )
    search_cards_cached.interactive_mode(embeddings, cards, {}, "fake-model")
    assert len(calls) == 1
    assert calls[0]["position"] == "upright"


def test_similar_explicit_u_stays_upright(monkeypatch, cards, embeddings):
    """Typing 'u' keeps upright."""
    calls = _run_interactive(
        monkeypatch,
        ["similar The Fool", "u", "quit"],
    )
    search_cards_cached.interactive_mode(embeddings, cards, {}, "fake-model")
    assert len(calls) == 1
    assert calls[0]["position"] == "upright"


def test_similar_case_insensitive_reversed(monkeypatch, cards, embeddings):
    """Uppercase 'R' also selects reversed."""
    calls = _run_interactive(
        monkeypatch,
        ["similar The Fool", "R", "quit"],
    )
    search_cards_cached.interactive_mode(embeddings, cards, {}, "fake-model")
    assert len(calls) == 1
    assert calls[0]["position"] == "reversed"


def test_similar_unknown_card_skips_find_and_prompt(monkeypatch, cards,
                                                    embeddings, capsys):
    """Unknown card must not consume a position prompt nor call find_similar."""
    # Only two scripted inputs: the bad similar command, then 'quit'.
    # If the code asked for position anyway, StopIteration would fire on quit.
    calls = _run_interactive(
        monkeypatch,
        ["similar Not A Card", "quit"],
    )
    search_cards_cached.interactive_mode(embeddings, cards, {}, "fake-model")
    assert calls == [], "find_similar_cards must not be called for unknown card"
    out = capsys.readouterr().out
    assert "Not A Card" in out
