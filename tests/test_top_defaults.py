"""
Tests for --top default values across the two CLIs.

Bug tarot-bcf: search_cards.py main() defaulted --top to 1, while
search_cards_cached.py defaults to 5. The two CLIs must agree, and
both should default to 5 to match the underlying top_k=5 default.
"""

import argparse
import importlib
import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub


def _build_search_cards_parser():
    """Run search_cards.main() far enough to construct its argparse parser.

    main() calls parse_args() and exits on missing input, so we monkeypatch
    ArgumentParser.parse_args to capture the parser instance instead.
    """
    captured = {}
    real_parse_args = argparse.ArgumentParser.parse_args

    def capture(self, *a, **kw):
        captured["parser"] = self
        raise SystemExit(0)

    argparse.ArgumentParser.parse_args = capture
    try:
        search_cards = importlib.import_module("search_cards")
        with pytest.raises(SystemExit):
            search_cards.main()
    finally:
        argparse.ArgumentParser.parse_args = real_parse_args
    return captured["parser"]


def _build_cached_parser():
    captured = {}
    real_parse_args = argparse.ArgumentParser.parse_args

    def capture(self, *a, **kw):
        captured["parser"] = self
        raise SystemExit(0)

    argparse.ArgumentParser.parse_args = capture
    try:
        cached = importlib.import_module("search_cards_cached")
        with pytest.raises(SystemExit):
            cached.main()
    finally:
        argparse.ArgumentParser.parse_args = real_parse_args
    return captured["parser"]


def _top_default(parser):
    for action in parser._actions:
        if "--top" in action.option_strings:
            return action.default
    raise AssertionError("--top action not found on parser")


def test_search_cards_top_defaults_to_five():
    parser = _build_search_cards_parser()
    assert _top_default(parser) == 5


def test_search_cards_cached_top_defaults_to_five():
    parser = _build_cached_parser()
    assert _top_default(parser) == 5


def test_search_cards_top_help_text_says_five():
    parser = _build_search_cards_parser()
    for action in parser._actions:
        if "--top" in action.option_strings:
            assert "5" in (action.help or "")
            return
    raise AssertionError("--top action not found")
