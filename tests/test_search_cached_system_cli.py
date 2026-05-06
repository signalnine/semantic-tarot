"""
Tests for --system flag in search_cards_cached.py CLI.

Bug semantic-tarot-0rs: the cached CLI did not expose --system, so users
of the offline path were forced to use system='combined' even though
search_cards()/find_similar_cards()/format_results() in that module all
accept a system parameter and the embeddings file contains 5 systems.
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
        {"name": "The Fool", "desc": "BASIC_DESC", "rdesc": "BASIC_REVERSED",
         "card": "ART_UP", "reversed": "ART_REV"},
    ]


@pytest.fixture
def interpretations():
    return {
        "The Fool": {
            "jungian_psychological": {
                "upright": "JUNG_UPRIGHT",
                "reversed": "JUNG_REVERSED",
            },
        },
    }


@pytest.fixture
def synthetic_embeddings():
    systems = ["rws_traditional", "thoth_crowley", "jungian_psychological",
               "modern_intuitive", "combined"]
    records = []
    for pi, position in enumerate(["upright", "reversed"]):
        for si, system in enumerate(systems):
            records.append({
                "card_name": "The Fool",
                "position": position,
                "interpretation_system": system,
                "text": "",
                "embedding": [float(pi + 0.1), float(si + 0.1), 0.0],
            })
    return records


def test_similar_passes_system_filter(monkeypatch, cards, interpretations,
                                       synthetic_embeddings, tmp_path,
                                       capsys):
    """--similar with --system threads system_filter into find_similar_cards."""
    captured = {}

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        captured["system_filter"] = system_filter
        captured["card_name"] = card_name
        captured["position"] = position
        captured["top_k"] = top_k
        return []

    import json as _json
    (tmp_path / "cards.json").write_text(_json.dumps(cards))
    (tmp_path / "interpretations.json").write_text(_json.dumps(interpretations))
    (tmp_path / "card_embeddings_v1_5.json").write_text(
        _json.dumps(synthetic_embeddings)
    )

    monkeypatch.setattr(search_cards_cached, "HERE", str(tmp_path))
    monkeypatch.setattr(search_cards_cached, "CARDS_FILE",
                        str(tmp_path / "cards.json"))
    monkeypatch.setattr(search_cards_cached, "INTERPRETATIONS_FILE",
                        str(tmp_path / "interpretations.json"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(search_cards_cached, "find_similar_cards", fake_find)
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "--similar", "The Fool",
        "--system", "jungian_psychological",
    ])

    search_cards_cached.main()

    assert captured["system_filter"] == "jungian_psychological"
    assert captured["card_name"] == "The Fool"


def test_query_passes_system_filter(monkeypatch, cards, interpretations,
                                     synthetic_embeddings, tmp_path):
    """A semantic query with --system threads system_filter into search_cards."""
    captured = {}

    def fake_search(query, embeddings_data, model, top_k=5,
                    position_filter=None, system_filter=None):
        captured["query"] = query
        captured["system_filter"] = system_filter
        captured["top_k"] = top_k
        return []

    import json as _json
    (tmp_path / "cards.json").write_text(_json.dumps(cards))
    (tmp_path / "interpretations.json").write_text(_json.dumps(interpretations))
    (tmp_path / "card_embeddings_v1_5.json").write_text(
        _json.dumps(synthetic_embeddings)
    )

    monkeypatch.setattr(search_cards_cached, "HERE", str(tmp_path))
    monkeypatch.setattr(search_cards_cached, "CARDS_FILE",
                        str(tmp_path / "cards.json"))
    monkeypatch.setattr(search_cards_cached, "INTERPRETATIONS_FILE",
                        str(tmp_path / "interpretations.json"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(search_cards_cached, "search_cards", fake_search)
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "shadow work",
        "--system", "jungian_psychological",
    ])

    search_cards_cached.main()

    assert captured["query"] == "shadow work"
    assert captured["system_filter"] == "jungian_psychological"


def test_system_threaded_to_format_results(monkeypatch, cards, interpretations,
                                            synthetic_embeddings, tmp_path,
                                            capsys):
    """Output uses system-specific meaning when --system is given."""
    import json as _json
    (tmp_path / "cards.json").write_text(_json.dumps(cards))
    (tmp_path / "interpretations.json").write_text(_json.dumps(interpretations))
    (tmp_path / "card_embeddings_v1_5.json").write_text(
        _json.dumps(synthetic_embeddings)
    )

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        return [(card_name, position, 0.9)]

    monkeypatch.setattr(search_cards_cached, "HERE", str(tmp_path))
    monkeypatch.setattr(search_cards_cached, "CARDS_FILE",
                        str(tmp_path / "cards.json"))
    monkeypatch.setattr(search_cards_cached, "INTERPRETATIONS_FILE",
                        str(tmp_path / "interpretations.json"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(search_cards_cached, "find_similar_cards", fake_find)
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "--similar", "The Fool",
        "--system", "jungian_psychological",
    ])

    search_cards_cached.main()
    out = capsys.readouterr().out
    assert "JUNG_UPRIGHT" in out
    assert "BASIC_DESC" not in out


def test_system_default_is_combined(monkeypatch, cards, interpretations,
                                     synthetic_embeddings, tmp_path):
    """Without --system the default behavior matches 'combined'."""
    captured = {}

    def fake_find(card_name, position, embeddings_data, top_k=5,
                  system_filter=None, exclude_same_card=True):
        captured["system_filter"] = system_filter
        return []

    import json as _json
    (tmp_path / "cards.json").write_text(_json.dumps(cards))
    (tmp_path / "interpretations.json").write_text(_json.dumps(interpretations))
    (tmp_path / "card_embeddings_v1_5.json").write_text(
        _json.dumps(synthetic_embeddings)
    )

    monkeypatch.setattr(search_cards_cached, "HERE", str(tmp_path))
    monkeypatch.setattr(search_cards_cached, "CARDS_FILE",
                        str(tmp_path / "cards.json"))
    monkeypatch.setattr(search_cards_cached, "INTERPRETATIONS_FILE",
                        str(tmp_path / "interpretations.json"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(search_cards_cached, "find_similar_cards", fake_find)
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "--similar", "The Fool",
    ])

    search_cards_cached.main()

    assert captured["system_filter"] in (None, "combined")


def test_system_choices_validated(monkeypatch, cards, synthetic_embeddings,
                                   tmp_path, capsys):
    """argparse rejects an unknown --system value."""
    import json as _json
    (tmp_path / "cards.json").write_text(_json.dumps(cards))
    (tmp_path / "interpretations.json").write_text("{}")
    (tmp_path / "card_embeddings_v1_5.json").write_text(
        _json.dumps(synthetic_embeddings)
    )

    monkeypatch.setattr(search_cards_cached, "HERE", str(tmp_path))
    monkeypatch.setattr(search_cards_cached, "CARDS_FILE",
                        str(tmp_path / "cards.json"))
    monkeypatch.setattr(search_cards_cached, "INTERPRETATIONS_FILE",
                        str(tmp_path / "interpretations.json"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "search_cards_cached.py",
        "--similar", "The Fool",
        "--system", "definitely_not_a_system",
    ])

    with pytest.raises(SystemExit):
        search_cards_cached.main()
