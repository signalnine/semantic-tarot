"""
Regression test for tarot-0c8: search_cards_cached.py must expose
--include-same-card on the CLI and thread it through to find_similar_cards
so users of the cached path can reach the same alternate behavior the
non-cached search_cards.py already supports.
"""

import json
import os
import sys
import types

if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub

import pytest

import search_cards_cached


def _redirect_data_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(search_cards_cached, "HERE", str(tmp_path))
    monkeypatch.setattr(
        search_cards_cached, "CARDS_FILE",
        os.path.join(str(tmp_path), "cards.json"),
    )
    monkeypatch.setattr(
        search_cards_cached, "INTERPRETATIONS_FILE",
        os.path.join(str(tmp_path), "interpretations.json"),
    )


def _make_embeddings():
    """Two cards, two positions, system='combined', linearly independent
    enough that the same-card opposite-position is the closest neighbor."""
    return [
        {"card_name": "The Fool", "position": "upright",
         "interpretation_system": "combined",
         "text": "", "embedding": [1.0, 0.0, 0.0]},
        {"card_name": "The Fool", "position": "reversed",
         "interpretation_system": "combined",
         "text": "", "embedding": [0.99, 0.01, 0.0]},
        {"card_name": "The Magician", "position": "upright",
         "interpretation_system": "combined",
         "text": "", "embedding": [0.0, 1.0, 0.0]},
        {"card_name": "The Magician", "position": "reversed",
         "interpretation_system": "combined",
         "text": "", "embedding": [0.0, 0.0, 1.0]},
    ]


@pytest.fixture
def setup(monkeypatch, tmp_path):
    cards = [
        {"name": "The Fool", "desc": "U", "rdesc": "R",
         "card": "ART_UP", "reversed": "ART_REV"},
        {"name": "The Magician", "desc": "U", "rdesc": "R",
         "card": "ART_UP", "reversed": "ART_REV"},
    ]
    (tmp_path / "cards.json").write_text(json.dumps(cards))
    (tmp_path / "interpretations.json").write_text("{}")
    (tmp_path / "card_embeddings_v1_5.json").write_text(
        json.dumps(_make_embeddings())
    )
    _redirect_data_paths(monkeypatch, tmp_path)
    return tmp_path


def test_include_same_card_flag_threaded_to_find_similar(monkeypatch, setup):
    captured = {}

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        captured["exclude_same_card"] = exclude_same_card
        return []

    monkeypatch.setattr(search_cards_cached, "find_similar_cards", fake_find)
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "--similar", "The Fool",
        "--include-same-card",
    ])

    search_cards_cached.main()

    assert captured["exclude_same_card"] is False


def test_default_excludes_same_card(monkeypatch, setup):
    captured = {}

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        captured["exclude_same_card"] = exclude_same_card
        return []

    monkeypatch.setattr(search_cards_cached, "find_similar_cards", fake_find)
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "--similar", "The Fool",
    ])

    search_cards_cached.main()

    assert captured["exclude_same_card"] is True


def test_include_same_card_end_to_end_returns_opposite_position(
    monkeypatch, setup, capsys
):
    """End-to-end: with the flag, the same card in the opposite position
    appears in --similar results."""
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "--similar", "The Fool",
        "--top", "3",
        "--json",
    ])

    search_cards_cached.main()
    out = capsys.readouterr().out
    parsed = json.loads(out)
    names = [(e["card_name"], e["position"]) for e in parsed]
    assert ("The Fool", "reversed") not in names, (
        "default behavior must still exclude same card in opposite position"
    )

    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "--similar", "The Fool",
        "--top", "3",
        "--json",
        "--include-same-card",
    ])

    search_cards_cached.main()
    out = capsys.readouterr().out
    parsed = json.loads(out)
    names = [(e["card_name"], e["position"]) for e in parsed]
    assert ("The Fool", "reversed") in names, (
        "with --include-same-card, opposite-position same card must appear"
    )
