"""
Regression test for tarot-nv3: search_cards.py and search_cards_cached.py
must emit identical JSON/YAML schema for equivalent queries.
"""

import json
import sys
import types

# search_cards_cached imports embedding_cache at module load.
if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub

import yaml

import search_cards
import search_cards_cached


CARDS = [
    {
        "name": "The Fool",
        "desc": "New beginnings, leap of faith",
        "rdesc": "Recklessness, holding back",
        "card": "FOOL_UP_ART",
        "reversed": "FOOL_REV_ART",
    },
    {
        "name": "The Magician",
        "desc": "Manifestation, willpower",
        "rdesc": "Manipulation, blocked talent",
        "card": "MAG_UP_ART",
        "reversed": "MAG_REV_ART",
    },
]

INTERPRETATIONS = {
    "The Fool": {
        "rws_traditional": {"upright": "RWS up Fool", "reversed": "RWS rev Fool"},
        "thoth_crowley": {"upright": "Thoth up Fool", "reversed": "Thoth rev Fool"},
    },
}


def test_combined_json_schema_matches_between_scripts():
    results = [("The Fool", "upright", 0.93), ("The Magician", "reversed", 0.87)]

    direct = search_cards.format_results_as_data(
        results, CARDS, system='combined', interpretations_data=INTERPRETATIONS,
    )
    cached_json = search_cards_cached.format_results(
        results, CARDS, INTERPRETATIONS, format_type='json', system='combined',
    )
    cached = json.loads(cached_json)

    assert direct == cached
    for entry in cached:
        assert set(entry.keys()) == {"card_name", "position", "similarity", "meaning"}


def test_system_specific_yaml_schema_matches_between_scripts():
    results = [("The Fool", "upright", 0.99)]

    direct = search_cards.format_results_as_data(
        results, CARDS, system='rws_traditional', interpretations_data=INTERPRETATIONS,
    )
    cached_yaml = search_cards_cached.format_results(
        results, CARDS, INTERPRETATIONS,
        format_type='yaml', system='rws_traditional',
    )
    cached = yaml.safe_load(cached_yaml)

    assert direct == cached
    assert cached[0]['meaning'] == 'RWS up Fool'
