"""
Tests that `search_cards.py --similar` accepts whitespace-padded card names.

The cached variant (search_cards_cached.py) strips whitespace via
resolve_card_name, and search_cards.py's interactive `/similar` command
strips via `query[9:].strip()`. The CLI `--similar` flag should match
that behavior so users don't get a confusing "Card not found" on a
trailing space.
"""

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_main(argv, monkeypatch):
    """Run search_cards.main() with argv patched and cwd at repo root."""
    monkeypatch.setattr(sys, "argv", ["search_cards.py", *argv])
    monkeypatch.chdir(REPO_ROOT)

    import search_cards
    importlib.reload(search_cards)
    try:
        search_cards.main()
        return 0
    except SystemExit as e:
        return e.code if e.code is not None else 0


@pytest.mark.parametrize(
    "name",
    ["  The Fool  ", "  The Fool", "The Fool  ", "\tThe Fool\n"],
)
def test_similar_cli_strips_whitespace(name, monkeypatch, capsys):
    rc = _run_main(["--similar", name, "--top", "3"], monkeypatch)
    captured = capsys.readouterr()
    assert rc == 0, (
        f"expected success for padded name {name!r}, got {rc}\n"
        f"stdout: {captured.out!r}\nstderr: {captured.err!r}"
    )
    assert "UPRIGHT" in captured.out or "REVERSED" in captured.out


def test_similar_cli_unknown_card_still_fails(monkeypatch, capsys):
    rc = _run_main(["--similar", "Not A Real Card"], monkeypatch)
    captured = capsys.readouterr()
    assert rc != 0
    combined = captured.out + captured.err
    assert "Not A Real Card" in combined
