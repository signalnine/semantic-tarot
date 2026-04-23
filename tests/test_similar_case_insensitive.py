"""
Tests that search_cards_cached.py's --similar flag and interactive
`similar <card>` command accept case-variant card names.

find_similar_cards() compares card names exactly, so the entry points
must normalize the user's input to the canonical card name (e.g.
"the fool" -> "The Fool") before delegating.
"""

import builtins
import json
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# search_cards_cached imports embedding_cache at module load. Stub it so
# tests don't need the optional dependency installed. The stub's embed
# implementation is never actually exercised -- these tests only drive
# the --similar path, which works from precomputed embeddings.
if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub


def _run_main(*argv):
    """Run search_cards_cached.main() with patched argv, return exit code."""
    import search_cards_cached as scc

    old_argv = sys.argv
    sys.argv = ["search_cards_cached.py", *argv]
    old_cwd = Path.cwd()
    import os
    os.chdir(REPO_ROOT)
    try:
        scc.main()
        return 0
    except SystemExit as e:
        return e.code if e.code is not None else 0
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)


@pytest.mark.parametrize("name", ["the fool", "THE FOOL", "tHe FoOl"])
def test_similar_cli_accepts_case_variants(name, capsys):
    rc = _run_main("--similar", name, "--top", "3")
    captured = capsys.readouterr()
    assert rc == 0, (
        f"expected success, got {rc}\n"
        f"stdout: {captured.out!r}\nstderr: {captured.err!r}"
    )
    # At least one similar-card listing must appear.
    assert "UPRIGHT" in captured.out or "REVERSED" in captured.out


def test_similar_cli_strips_whitespace(capsys):
    rc = _run_main("--similar", "  The Fool  ", "--top", "3")
    captured = capsys.readouterr()
    assert rc == 0, (
        f"expected success, got {rc}\n"
        f"stdout: {captured.out!r}\nstderr: {captured.err!r}"
    )
    assert "UPRIGHT" in captured.out or "REVERSED" in captured.out


def test_similar_cli_unknown_card_fails(capsys):
    rc = _run_main("--similar", "Not A Real Card")
    captured = capsys.readouterr()
    assert rc != 0
    assert "Not A Real Card" in (captured.err + captured.out)


def test_interactive_similar_is_case_insensitive(capsys):
    """interactive_mode should not error on lowercase 'similar the fool'."""
    import search_cards_cached as scc

    embeddings = json.loads((REPO_ROOT / "card_embeddings_v1_5.json").read_text())
    cards = json.loads((REPO_ROOT / "cards.json").read_text())
    interpretations = json.loads((REPO_ROOT / "interpretations.json").read_text())

    inputs = iter(["similar the fool", "quit"])
    real_input = builtins.input
    builtins.input = lambda _prompt="": next(inputs)
    try:
        scc.interactive_mode(embeddings, cards, interpretations,
                             "nomic-ai/nomic-embed-text-v1.5")
    finally:
        builtins.input = real_input

    out = capsys.readouterr().out
    assert "Card not found" not in out, (
        f"interactive mode raised 'Card not found' for lowercase input: {out!r}"
    )
    assert "UPRIGHT" in out or "REVERSED" in out


def test_find_similar_cards_still_requires_canonical_name():
    """The helper's contract is unchanged: exact match required."""
    from search_cards_cached import find_similar_cards

    embeddings = json.loads((REPO_ROOT / "card_embeddings_v1_5.json").read_text())
    with pytest.raises(ValueError):
        find_similar_cards("the fool", "upright", embeddings, top_k=3)
