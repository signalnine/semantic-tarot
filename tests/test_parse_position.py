"""
Tests for the position-prompt parser (tarot-21p).

Before the fix, three interactive prompts (tarot.py compare_interpretations,
search_cards.py /similar, search_cards_cached.py similar) did a literal
== 'r' check, so typing 'reversed', 'rev', or anything else silently
coerced to upright. The fix introduces a shared parser that recognizes
'r', 'rev', 'reversed' (case-insensitive) as reversed and treats empty
input as the upright default.
"""

import pytest


def _parsers():
    import tarot
    import search_cards
    import search_cards_cached
    return [
        tarot.parse_position,
        search_cards.parse_position,
        search_cards_cached.parse_position,
    ]


@pytest.mark.parametrize("raw", ['r', 'R', 'rev', 'REV', 'Rev', 'reversed', 'REVERSED', 'Reversed', '  r  ', ' reversed '])
def test_reversed_inputs(raw):
    for parse in _parsers():
        assert parse(raw) == 'reversed', f"{parse.__module__}.parse_position({raw!r})"


@pytest.mark.parametrize("raw", ['u', 'U', 'upright', 'Up', '', '   '])
def test_upright_inputs(raw):
    for parse in _parsers():
        assert parse(raw) == 'upright', f"{parse.__module__}.parse_position({raw!r})"


@pytest.mark.parametrize("raw", ['no', 'yes', 'xyz', 'reverse?', '1'])
def test_unrecognized_inputs_default_upright(raw):
    """Unknown inputs default to upright -- documented behavior, but no
    longer silently swallows 'reversed' as part of that bucket."""
    for parse in _parsers():
        assert parse(raw) == 'upright', f"{parse.__module__}.parse_position({raw!r})"
