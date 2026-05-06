"""
Regression test for tarot-pg4: format_results() must not silently degrade
to text when YAML is requested but pyyaml is unavailable.
"""

import sys
import types

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
        {"name": "The Fool", "desc": "u", "rdesc": "r",
         "card": "ART_UP", "reversed": "ART_REV"},
    ]


def test_yaml_without_pyyaml_raises(monkeypatch, cards):
    monkeypatch.setattr(search_cards_cached, "YAML_AVAILABLE", False)
    results = [("The Fool", "upright", 0.9)]
    with pytest.raises(RuntimeError, match="pyyaml"):
        search_cards_cached.format_results(
            results, cards, {}, format_type="yaml",
        )


def test_yaml_with_pyyaml_still_works(cards):
    """Sanity: YAML branch still emits when pyyaml is present."""
    if not search_cards_cached.YAML_AVAILABLE:
        pytest.skip("pyyaml not installed in this environment")
    results = [("The Fool", "upright", 0.9)]
    out = search_cards_cached.format_results(
        results, cards, {}, format_type="yaml",
    )
    assert "card_name" in out and "The Fool" in out
