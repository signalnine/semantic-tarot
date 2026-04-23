"""
Tests for find_similar_cards() in search_cards_cached.py.

Covers the default exclude-same-card behavior: by default, find_similar_cards
must exclude the same card in both positions so results show truly different
cards. This matches search_cards.py::find_similar_cards and is documented in
CLAUDE.md under "Similarity Exclusion".
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
from search_cards_cached import find_similar_cards


@pytest.fixture
def embeddings_data():
    """Synthetic embeddings where Fool upright/reversed are near-identical
    (tests whether the opposite-position card leaks into results)."""
    return [
        {"card_name": "The Fool", "position": "upright",
         "interpretation_system": "combined",
         "embedding": [1.0, 0.0, 0.0]},
        {"card_name": "The Fool", "position": "reversed",
         "interpretation_system": "combined",
         "embedding": [0.99, 0.01, 0.0]},
        {"card_name": "The Magician", "position": "upright",
         "interpretation_system": "combined",
         "embedding": [0.5, 0.5, 0.0]},
        {"card_name": "The Magician", "position": "reversed",
         "interpretation_system": "combined",
         "embedding": [0.4, 0.6, 0.0]},
        {"card_name": "The High Priestess", "position": "upright",
         "interpretation_system": "combined",
         "embedding": [0.0, 1.0, 0.0]},
    ]


def test_excludes_same_card_both_positions_by_default(embeddings_data):
    """By default, same card in opposite position must not appear in results."""
    results = find_similar_cards(
        card_name="The Fool",
        position="upright",
        embeddings_data=embeddings_data,
        top_k=5,
    )
    card_names = [name for name, _pos, _score in results]
    assert "The Fool" not in card_names, (
        f"Same card must be excluded from its own similar results by default, "
        f"got: {results}"
    )
