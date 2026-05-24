"""
Regression test for semantic-tarot-8tc: generate_embeddings_cached.py
must not require the embedding_cache package just to import the module.
embedding_cache is used only inside generate_embeddings() and should
remain a lazy import so callers that only want pure helpers
(create_card_text_for_system, load_data, etc.) can load the module
even when the optional dependency is unavailable.
"""

import importlib
import sys


def test_module_imports_when_embedding_cache_unavailable(monkeypatch):
    monkeypatch.setitem(sys.modules, "embedding_cache", None)
    sys.modules.pop("generate_embeddings_cached", None)

    module = importlib.import_module("generate_embeddings_cached")

    assert hasattr(module, "create_card_text_for_system")
    assert hasattr(module, "load_data")
    assert hasattr(module, "generate_embeddings")


def test_pure_helper_runs_without_embedding_cache(monkeypatch):
    monkeypatch.setitem(sys.modules, "embedding_cache", None)
    sys.modules.pop("generate_embeddings_cached", None)

    module = importlib.import_module("generate_embeddings_cached")

    card = {"name": "The Fool", "desc": "Beginnings", "rdesc": "Folly"}
    interpretations = {
        "The Fool": {
            "rws_traditional": {"upright": "U-RWS", "reversed": "R-RWS"},
        }
    }

    text = module.create_card_text_for_system(
        card, interpretations, "upright", "rws_traditional"
    )

    assert "The Fool" in text
    assert "U-RWS" in text
