"""
Tests for system-aware interpretation lookup in
search_cards_cached.format_results.

Bug tarot-wpc: format_results accepted an interpretations dict but never
read it; users always saw the basic cards.json description even when
they passed a non-combined system. The function must now consult
interpretations[card_name][system][position] when system != 'combined',
and fall back to the basic meaning when the lookup misses.
"""

import sys
import types

if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub

import pytest
from search_cards_cached import format_results


@pytest.fixture
def cards():
    return [
        {
            "name": "The Fool",
            "desc": "BASIC_UPRIGHT_DESC",
            "rdesc": "BASIC_REVERSED_DESC",
            "card": "ART_UP",
            "reversed": "ART_REV",
        },
    ]


@pytest.fixture
def interpretations():
    return {
        "The Fool": {
            "rws_traditional": {
                "upright": "RWS_UPRIGHT_TEXT",
                "reversed": "RWS_REVERSED_TEXT",
            },
            "jungian_psychological": {
                "upright": "JUNG_UPRIGHT_TEXT",
                "reversed": "JUNG_REVERSED_TEXT",
            },
        },
    }


def test_combined_system_uses_basic_meaning(cards, interpretations):
    out = format_results(
        [("The Fool", "upright", 0.9)],
        cards, interpretations,
        format_type="text",
        system="combined",
    )
    assert "BASIC_UPRIGHT_DESC" in out
    assert "RWS_UPRIGHT_TEXT" not in out


def test_system_specific_upright_used_when_present(cards, interpretations):
    out = format_results(
        [("The Fool", "upright", 0.9)],
        cards, interpretations,
        format_type="text",
        system="rws_traditional",
    )
    assert "RWS_UPRIGHT_TEXT" in out
    assert "BASIC_UPRIGHT_DESC" not in out


def test_system_specific_reversed_used_when_present(cards, interpretations):
    out = format_results(
        [("The Fool", "reversed", 0.8)],
        cards, interpretations,
        format_type="text",
        system="jungian_psychological",
    )
    assert "JUNG_REVERSED_TEXT" in out
    assert "BASIC_REVERSED_DESC" not in out


def test_falls_back_to_basic_when_system_missing_for_card(cards, interpretations):
    out = format_results(
        [("The Fool", "upright", 0.9)],
        cards, interpretations,
        format_type="text",
        system="thoth_crowley",
    )
    assert "BASIC_UPRIGHT_DESC" in out


def test_falls_back_to_basic_when_card_missing_from_interpretations(cards):
    out = format_results(
        [("The Fool", "upright", 0.9)],
        cards, {},
        format_type="text",
        system="rws_traditional",
    )
    assert "BASIC_UPRIGHT_DESC" in out


def test_default_system_is_combined(cards, interpretations):
    """Callers that don't pass system at all keep getting basic meanings."""
    out = format_results(
        [("The Fool", "upright", 0.9)],
        cards, interpretations,
        format_type="text",
    )
    assert "BASIC_UPRIGHT_DESC" in out
    assert "RWS_UPRIGHT_TEXT" not in out
