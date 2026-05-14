"""
Tests for search-CLI display behavior when a reversed card lacks
'reversed' art (tarot-ko3).

Mirrors test_display_card_reversed_fallback.py for the search paths:
- search_cards.py:display_search_results (--ascii branch)
- search_cards_cached.py:format_results (show_ascii branch)

Before the fix, both paths silently rendered upright art under a
REVERSED label when a card had no 'reversed' key. After the fix, both
paths print a clear notice before falling back to upright art.
"""

import io
from contextlib import redirect_stdout

import search_cards
import search_cards_cached


NOTICE_MARKER = "no reversed art"


def _make_card(with_reversed):
    card = {
        "name": "Test Card",
        "desc": "upright meaning",
        "rdesc": "reversed meaning",
        "card": "UPRIGHT_ART_MARKER",
    }
    if with_reversed:
        card["reversed"] = "REVERSED_ART_MARKER"
    return card


# --- search_cards.py:display_search_results ---

def _display_results_text(card, position):
    buf = io.StringIO()
    with redirect_stdout(buf):
        search_cards.display_search_results(
            results=[(card["name"], position, 0.9)],
            cards_data=[card],
            output_format=None,
            system='combined',
            interpretations_data=None,
            show_art=True,
        )
    return buf.getvalue()


def test_search_cards_reversed_with_art_shows_reversed_art():
    out = _display_results_text(_make_card(with_reversed=True), 'reversed')
    assert "REVERSED" in out
    assert "REVERSED_ART_MARKER" in out
    assert "UPRIGHT_ART_MARKER" not in out
    assert NOTICE_MARKER not in out


def test_search_cards_reversed_without_art_shows_notice_and_upright():
    out = _display_results_text(_make_card(with_reversed=False), 'reversed')
    assert "REVERSED" in out
    assert "UPRIGHT_ART_MARKER" in out
    assert NOTICE_MARKER in out


def test_search_cards_upright_no_notice():
    out = _display_results_text(_make_card(with_reversed=True), 'upright')
    assert "UPRIGHT_ART_MARKER" in out
    assert NOTICE_MARKER not in out


# --- search_cards_cached.py:format_results ---

def _format_cached_text(card, position):
    return search_cards_cached.format_results(
        results=[(card["name"], position, 0.9)],
        cards=[card],
        interpretations={},
        format_type='text',
        show_ascii=True,
        system='combined',
    )


def test_cached_reversed_with_art_shows_reversed_art():
    out = _format_cached_text(_make_card(with_reversed=True), 'reversed')
    assert "REVERSED" in out
    assert "REVERSED_ART_MARKER" in out
    assert "UPRIGHT_ART_MARKER" not in out
    assert NOTICE_MARKER not in out


def test_cached_reversed_without_art_shows_notice_and_upright():
    out = _format_cached_text(_make_card(with_reversed=False), 'reversed')
    assert "REVERSED" in out
    assert "UPRIGHT_ART_MARKER" in out
    assert NOTICE_MARKER in out


def test_cached_upright_no_notice():
    out = _format_cached_text(_make_card(with_reversed=True), 'upright')
    assert "UPRIGHT_ART_MARKER" in out
    assert NOTICE_MARKER not in out
