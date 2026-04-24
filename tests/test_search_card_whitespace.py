"""
Tests that `tarot.search_card` accepts whitespace-padded card names and
echoes the attempted name in the "Card not found" message.

The cached variant (search_cards_cached.py) strips whitespace via
resolve_card_name, tarot.compare_interpretations strips its input, and
search_cards.py --similar was fixed to strip in semantic-tarot-dxd.
tarot.search_card should match that behavior so callers don't rely on
every call-site remembering to strip first.
"""

import pytest

import tarot


@pytest.mark.parametrize(
    "name",
    ["  The Fool  ", "  The Fool", "The Fool  ", "\tThe Fool\n"],
)
def test_search_card_strips_whitespace(name, capsys):
    result = tarot.search_card(name)
    captured = capsys.readouterr()
    assert result is not None, (
        f"expected a card for padded name {name!r}\n"
        f"stdout: {captured.out!r}"
    )
    assert result["name"] == "The Fool"
    assert "Card not found" not in captured.out


def test_search_card_case_insensitive(capsys):
    result = tarot.search_card("the fool")
    assert result is not None
    assert result["name"] == "The Fool"


def test_search_card_unknown_echoes_name(capsys):
    result = tarot.search_card("Not A Real Card")
    captured = capsys.readouterr()
    assert result is None
    assert "Not A Real Card" in captured.out


def test_search_card_unknown_echoes_stripped_name(capsys):
    result = tarot.search_card("   Bogus Card   ")
    captured = capsys.readouterr()
    assert result is None
    assert "Bogus Card" in captured.out
