"""
Tests for format_results() in search_cards_cached.py.

Covers the --ascii / --art flag, which was broken because format_results
looked for a non-existent 'art' key on cards (real keys are 'card' and
'reversed') and ignored the card position.
"""

import sys
import types

# search_cards_cached imports embedding_cache at module load.
# Stub it here so tests don't need the optional dependency installed.
if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub

import pytest
from search_cards_cached import format_results


@pytest.fixture
def cards_with_art():
    """Cards with the real ASCII-art keys used by cards.json."""
    return [
        {
            "name": "The Fool",
            "desc": "New beginnings",
            "rdesc": "Folly",
            "card": "UPRIGHT_FOOL_ART_MARKER",
            "reversed": "REVERSED_FOOL_ART_MARKER",
        },
        {
            "name": "The Magician",
            "desc": "Manifestation",
            "rdesc": "Manipulation",
            "card": "UPRIGHT_MAGICIAN_ART_MARKER",
            "reversed": "REVERSED_MAGICIAN_ART_MARKER",
        },
    ]


def test_ascii_shows_upright_art_for_upright_position(cards_with_art):
    results = [("The Fool", "upright", 0.9)]
    out = format_results(results, cards_with_art, {},
                         show_ascii=True, format_type="text")
    assert "UPRIGHT_FOOL_ART_MARKER" in out


def test_ascii_shows_reversed_art_for_reversed_position(cards_with_art):
    results = [("The Magician", "reversed", 0.8)]
    out = format_results(results, cards_with_art, {},
                         show_ascii=True, format_type="text")
    assert "REVERSED_MAGICIAN_ART_MARKER" in out


def test_ascii_disabled_omits_art(cards_with_art):
    results = [("The Fool", "upright", 0.9)]
    out = format_results(results, cards_with_art, {},
                         show_ascii=False, format_type="text")
    assert "UPRIGHT_FOOL_ART_MARKER" not in out
    assert "REVERSED_FOOL_ART_MARKER" not in out


def test_json_output_matches_shared_schema(cards_with_art):
    """JSON schema must match search_cards.py: card_name, position, similarity, meaning."""
    import json as _json
    results = [("The Fool", "upright", 0.9)]
    out = format_results(results, cards_with_art, {},
                         show_ascii=True, format_type="json")
    parsed = _json.loads(out)
    assert parsed == [{"card_name": "The Fool", "position": "upright",
                       "similarity": 0.9, "meaning": "New beginnings"}]


def test_text_output_shows_upright_meaning(cards_with_art):
    results = [("The Fool", "upright", 0.9)]
    out = format_results(results, cards_with_art, {},
                         show_ascii=False, format_type="text")
    assert "Meaning:" in out
    assert "New beginnings" in out


def test_text_output_shows_reversed_meaning(cards_with_art):
    results = [("The Magician", "reversed", 0.8)]
    out = format_results(results, cards_with_art, {},
                         show_ascii=False, format_type="text")
    assert "Meaning:" in out
    assert "Manipulation" in out


def test_meaning_shown_with_ascii_enabled(cards_with_art):
    results = [("The Fool", "upright", 0.9)]
    out = format_results(results, cards_with_art, {},
                         show_ascii=True, format_type="text")
    assert "New beginnings" in out
    assert "UPRIGHT_FOOL_ART_MARKER" in out
    # Meaning must appear before the art block.
    assert out.index("New beginnings") < out.index("UPRIGHT_FOOL_ART_MARKER")


def test_unknown_card_does_not_crash_or_inject_meaning(cards_with_art):
    results = [("Not A Real Card", "upright", 0.5)]
    out = format_results(results, cards_with_art, {},
                         show_ascii=False, format_type="text")
    assert "Meaning:" not in out
    assert "Not A Real Card" in out
