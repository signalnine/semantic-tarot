"""
Tests for display_card behavior when a reversed card lacks 'reversed' art.

Covers tarot-tym: prior to the fix, display_card silently fell back to
the upright art while still labeling 'Position: REVERSED', producing
upright-looking imagery under a REVERSED label. The fix prints an
explicit notice so the user is not misled.
"""

import io
from contextlib import redirect_stdout

import tarot


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


def _capture(card, is_reversed):
    buf = io.StringIO()
    with redirect_stdout(buf):
        tarot.display_card(card, is_reversed=is_reversed)
    return buf.getvalue()


def test_reversed_with_art_shows_reversed_art():
    out = _capture(_make_card(with_reversed=True), is_reversed=True)
    assert "Position: REVERSED" in out
    assert "REVERSED_ART_MARKER" in out
    assert "UPRIGHT_ART_MARKER" not in out
    assert NOTICE_MARKER not in out


def test_reversed_without_art_shows_notice_and_upright_art():
    out = _capture(_make_card(with_reversed=False), is_reversed=True)
    assert "Position: REVERSED" in out
    assert "UPRIGHT_ART_MARKER" in out
    assert NOTICE_MARKER in out


def test_upright_never_shows_reversed_notice():
    out = _capture(_make_card(with_reversed=True), is_reversed=False)
    assert "Position: Upright" in out
    assert "UPRIGHT_ART_MARKER" in out
    assert NOTICE_MARKER not in out


def test_upright_without_reversed_field_does_not_show_notice():
    out = _capture(_make_card(with_reversed=False), is_reversed=False)
    assert "Position: Upright" in out
    assert NOTICE_MARKER not in out
