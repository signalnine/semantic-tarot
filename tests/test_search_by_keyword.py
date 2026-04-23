"""
Tests for tarot.search_by_keyword.

Bug tarot-wv9: empty keyword returned every card because "" is a substring
of every description string. Menu option 9 strips input, so hitting Enter
with no text flooded the UI with all 78 cards as "matches".
"""

import pytest

import tarot


def test_empty_keyword_returns_no_results(capsys):
    result = tarot.search_by_keyword("")
    assert result == []
    out = capsys.readouterr().out
    assert "Found 78" not in out


def test_whitespace_only_keyword_returns_no_results(capsys):
    result = tarot.search_by_keyword("   ")
    assert result == []
    out = capsys.readouterr().out
    assert "Found" not in out


def test_real_keyword_still_works():
    result = tarot.search_by_keyword("fool")
    assert len(result) >= 1
    assert any(card["name"] == "The Fool" for card in result)


def test_nonmatching_keyword_returns_empty():
    result = tarot.search_by_keyword("zzznevermatches")
    assert result == []
