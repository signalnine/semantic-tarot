"""
`search_cards.py` interactive mode (`interactive_search`) must not require
OPENAI_API_KEY at startup. The in-session `/similar <card>` command works
entirely from local pre-generated embeddings -- it should run without a
key. Semantic queries that do need the key should report it without
killing the interactive session.

This is the interactive counterpart to test_similar_no_api_key.py, which
covers CLI `--similar` (fix 1978891). The interactive path was missed.
"""

import builtins
import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _scripted_input(monkeypatch, *responses):
    """Make `input(...)` consume `responses` in order."""
    iterator = iter(responses)

    def fake_input(prompt=""):
        try:
            return next(iterator)
        except StopIteration:
            raise AssertionError(
                f"interactive_search asked for more input than scripted "
                f"(prompt={prompt!r})"
            )

    monkeypatch.setattr(builtins, "input", fake_input)


def _reload_search_cards(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setattr(sys, "argv", ["search_cards.py"])
    import search_cards
    importlib.reload(search_cards)
    return search_cards


def test_interactive_runs_similar_without_api_key(monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _scripted_input(monkeypatch, "/similar The Fool", "u", "/quit")
    sc = _reload_search_cards(monkeypatch)

    sc.interactive_search()
    captured = capsys.readouterr()
    out = captured.out + captured.err

    assert "OPENAI_API_KEY environment variable not set" not in out, (
        f"interactive mode must not bail at startup without a key.\n"
        f"output: {out!r}"
    )
    assert "UPRIGHT" in out or "REVERSED" in out, (
        f"expected /similar to produce results.\noutput: {out!r}"
    )


def test_interactive_similar_does_not_construct_openai_client(
    monkeypatch, capsys
):
    """`/similar` in interactive mode must never instantiate an OpenAI client."""
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-value-not-used")
    _scripted_input(monkeypatch, "/similar The Fool", "u", "/quit")
    sc = _reload_search_cards(monkeypatch)

    def _boom(*args, **kwargs):
        raise RuntimeError(
            "OpenAI client must not be constructed when only /similar is used"
        )

    monkeypatch.setattr(sc, "OpenAI", _boom)
    sc.interactive_search()
    captured = capsys.readouterr()
    out = captured.out + captured.err
    assert "UPRIGHT" in out or "REVERSED" in out
    assert "OpenAI client must not be constructed" not in out


def test_interactive_semantic_without_key_warns_but_continues(
    monkeypatch, capsys
):
    """A non-`/` query without a key should warn but keep the session alive
    so the user can still run `/similar` or `/quit`."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _scripted_input(
        monkeypatch,
        "transformation",     # semantic query: should warn, not exit
        "/similar The Fool",  # should still work after the warn
        "u",
        "/quit",
    )
    sc = _reload_search_cards(monkeypatch)

    sc.interactive_search()
    captured = capsys.readouterr()
    out = captured.out + captured.err

    assert "OPENAI_API_KEY" in out, (
        "expected semantic search without a key to mention OPENAI_API_KEY.\n"
        f"output: {out!r}"
    )
    # And we made it to the /similar -- proof we did not exit early.
    assert "UPRIGHT" in out or "REVERSED" in out
