"""Tests for relative-path bugs (bd 1ho, 4f4) - data files anchored to __file__."""

import os
import subprocess
import sys

import pytest


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_search_cards_constants_are_absolute():
    import search_cards
    assert os.path.isabs(search_cards.EMBEDDINGS_FILE)
    assert os.path.isabs(search_cards.CARDS_FILE)
    assert os.path.isabs(search_cards.INTERPRETATIONS_FILE)


def test_search_cards_cached_constants_are_absolute():
    import search_cards_cached
    assert os.path.isabs(search_cards_cached.CARDS_FILE)
    assert os.path.isabs(search_cards_cached.INTERPRETATIONS_FILE)


def test_generate_embeddings_constants_are_absolute():
    import generate_embeddings
    assert os.path.isabs(generate_embeddings.CARDS_FILE)
    assert os.path.isabs(generate_embeddings.INTERPRETATIONS_FILE)
    assert os.path.isabs(generate_embeddings.EMBEDDINGS_OUTPUT_FILE)


def test_generate_embeddings_cached_constants_are_absolute():
    pytest.importorskip("embedding_cache")
    import generate_embeddings_cached
    assert os.path.isabs(generate_embeddings_cached.CARDS_FILE)
    assert os.path.isabs(generate_embeddings_cached.INTERPRETATIONS_FILE)


def test_search_cards_runs_from_other_dir(tmp_path):
    """--similar should not need OPENAI_API_KEY (existing fix) and must
    find data files when invoked from outside the repo."""
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        [sys.executable, os.path.join(REPO, "search_cards.py"),
         "--similar", "The Fool", "--top", "2"],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    combined = result.stdout + result.stderr
    assert "Embeddings file not found" not in combined, combined
    assert result.returncode == 0, combined


def test_search_cards_cached_runs_from_other_dir(tmp_path):
    """search_cards_cached.py with embedding-cache should find its embeddings
    file relative to the script when invoked from outside the repo.
    Skipped if cached embeddings file is missing in the repo."""
    embeddings = os.path.join(REPO, "card_embeddings_v1_5.json")
    if not os.path.exists(embeddings):
        pytest.skip("card_embeddings_v1_5.json not present in repo")
    result = subprocess.run(
        [sys.executable, os.path.join(REPO, "search_cards_cached.py"),
         "--similar", "The Fool", "--top", "2", "--model", "v1.5"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=120,
    )
    combined = result.stdout + result.stderr
    assert "Embeddings file not found" not in combined, combined
    assert "cards.json" not in result.stderr or "FileNotFoundError" not in result.stderr, combined
