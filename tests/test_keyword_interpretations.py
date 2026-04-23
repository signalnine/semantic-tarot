"""
Tests that tarot.search_by_keyword() searches interpretation text in
addition to the brief name/desc/rdesc from cards.json.

Themes like "shadow" appear dozens of times in interpretations.json
(notably in the Jungian system) but never in cards.json. The menu
advertises "Search by keyword" as a browse tool, so users reasonably
expect it to surface cards whose interpretations discuss the keyword,
not just cards whose one-line blurb happens to use the word.
"""

import tarot


def test_search_by_keyword_finds_shadow_in_interpretations():
    """'shadow' must surface cards whose interpretations discuss it.

    Verifies the fix: cards.json blurbs never mention 'shadow' but 20+
    interpretation entries do. The old implementation returned [] for
    this query.
    """
    results = tarot.search_by_keyword("shadow")
    assert results, "Expected cards whose interpretations mention 'shadow'"


def test_search_by_keyword_still_finds_name_matches():
    """Existing behavior: keyword matching a card name still works."""
    results = tarot.search_by_keyword("Fool")
    names = [c["name"] for c in results]
    assert "The Fool" in names


def test_search_by_keyword_still_finds_desc_matches():
    """Existing behavior: keyword matching cards.json desc/rdesc still works."""
    # Use a card's actual desc text to guarantee a match in cards.json
    sample = tarot.tarot_deck[0]
    needle = sample["desc"].split()[0]  # first word of The Fool's desc
    results = tarot.search_by_keyword(needle)
    names = [c["name"] for c in results]
    assert sample["name"] in names


def test_search_by_keyword_is_case_insensitive_for_interpretations():
    """Case-insensitive matching must extend to interpretation text."""
    lower = tarot.search_by_keyword("shadow")
    upper = tarot.search_by_keyword("SHADOW")
    mixed = tarot.search_by_keyword("ShAdOw")
    lower_names = sorted(c["name"] for c in lower)
    assert lower_names == sorted(c["name"] for c in upper)
    assert lower_names == sorted(c["name"] for c in mixed)


def test_search_by_keyword_returns_no_duplicates():
    """A keyword that matches a card in multiple systems must not
    duplicate that card in the results."""
    results = tarot.search_by_keyword("shadow")
    names = [c["name"] for c in results]
    assert len(names) == len(set(names)), f"Duplicate cards in results: {names}"


def test_search_by_keyword_returns_empty_for_missing_keyword():
    """Nonsense keywords still return no results."""
    results = tarot.search_by_keyword("zzzzzxyznotaword")
    assert results == []
