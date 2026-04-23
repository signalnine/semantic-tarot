"""
`search_cards.py --similar <card>` uses only pre-generated local embeddings
and must not require OPENAI_API_KEY. Semantic search still requires it.
"""

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_main(argv, monkeypatch):
    """Run search_cards.main() with argv patched, API key cleared, cwd at repo root."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["search_cards.py", *argv])
    monkeypatch.chdir(REPO_ROOT)

    import search_cards
    importlib.reload(search_cards)
    try:
        search_cards.main()
        return 0
    except SystemExit as e:
        return e.code if e.code is not None else 0


def test_similar_runs_without_api_key(monkeypatch, capsys):
    rc = _run_main(["--similar", "The Fool", "--top", "3"], monkeypatch)
    captured = capsys.readouterr()
    assert rc == 0, (
        f"expected success without OPENAI_API_KEY, got {rc}\n"
        f"stdout: {captured.out!r}\nstderr: {captured.err!r}"
    )
    assert "OPENAI_API_KEY" not in captured.out
    assert "OPENAI_API_KEY" not in captured.err
    assert "UPRIGHT" in captured.out or "REVERSED" in captured.out


def test_similar_json_runs_without_api_key(monkeypatch, capsys):
    rc = _run_main(
        ["--similar", "The Fool", "--json", "--top", "3"], monkeypatch
    )
    captured = capsys.readouterr()
    assert rc == 0, (
        f"expected success, got {rc}\n"
        f"stdout: {captured.out!r}\nstderr: {captured.err!r}"
    )
    data = json.loads(captured.out)
    assert isinstance(data, list) and len(data) > 0
    assert all(isinstance(entry, dict) for entry in data)
    assert all("card_name" in entry for entry in data)


def test_semantic_search_still_requires_api_key(monkeypatch, capsys):
    rc = _run_main(["transformation"], monkeypatch)
    captured = capsys.readouterr()
    assert rc != 0
    combined = captured.out + captured.err
    assert "OPENAI_API_KEY" in combined


def test_similar_does_not_instantiate_openai_client(monkeypatch, capsys):
    """`--similar` must not build an OpenAI client even if a key is set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-value-not-used")
    monkeypatch.setattr(
        sys, "argv", ["search_cards.py", "--similar", "The Fool", "--top", "2"]
    )
    monkeypatch.chdir(REPO_ROOT)

    import search_cards
    importlib.reload(search_cards)

    def _boom(*args, **kwargs):
        raise RuntimeError("OpenAI client must not be constructed for --similar")

    monkeypatch.setattr(search_cards, "OpenAI", _boom)

    try:
        search_cards.main()
        rc = 0
    except SystemExit as e:
        rc = e.code if e.code is not None else 0

    captured = capsys.readouterr()
    assert rc == 0, (
        f"expected success, got {rc}\n"
        f"stdout: {captured.out!r}\nstderr: {captured.err!r}"
    )
