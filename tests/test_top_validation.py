"""
Tests for --top / top_k validation.

Bug tarot-6u7: Negative values for --top are accepted and slice the
results list with Python's wraparound semantics. With --top -1 against
The Fool the user expects an error or zero results; instead they get
153 results (all matches except the last). This is surprising and
disagrees with the docstring "Number of results to return".

Both search_cards.py and search_cards_cached.py expose --top via
argparse and accept a top_k argument on find_similar_cards/search_cards.
Validation must reject negative inputs in both layers.
"""

import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


# search_cards_cached imports embedding_cache at module load. Stub it so
# tests don't need the optional dependency installed.
if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub


@pytest.fixture
def embeddings_for_search_cards():
    """Real card_embeddings.json or skip."""
    path = REPO_ROOT / "card_embeddings.json"
    if not path.exists():
        pytest.skip("card_embeddings.json not generated")
    with path.open() as f:
        return json.load(f)


@pytest.fixture
def synthetic_v1_5_embeddings(tmp_path):
    """Synthetic v1.5 embeddings shaped like the real cached file."""
    cards = json.loads((REPO_ROOT / "cards.json").read_text())
    systems = [
        "rws_traditional", "thoth_crowley", "jungian_psychological",
        "modern_intuitive", "combined",
    ]
    records = []
    for ci, card in enumerate(cards):
        for pi, position in enumerate(["upright", "reversed"]):
            for si, system in enumerate(systems):
                records.append({
                    "card_name": card["name"],
                    "position": position,
                    "interpretation_system": system,
                    "text": "",
                    "embedding": [float(ci + 1), float(pi + 0.1), float(si + 0.1)],
                })
    return records


class TestFindSimilarRejectsNegative:
    """find_similar_cards in both modules must reject negative top_k."""

    def test_search_cards_module(self, embeddings_for_search_cards):
        from search_cards import find_similar_cards
        with pytest.raises(ValueError, match="top_k"):
            find_similar_cards(
                card_name="The Fool",
                position="upright",
                embeddings_data=embeddings_for_search_cards,
                top_k=-1,
            )

    def test_search_cards_cached_module(self, synthetic_v1_5_embeddings):
        from search_cards_cached import find_similar_cards
        with pytest.raises(ValueError, match="top_k"):
            find_similar_cards(
                card_name="The Fool",
                position="upright",
                embeddings_data=synthetic_v1_5_embeddings,
                top_k=-1,
            )


class TestCliRejectsNegativeTop:
    """CLI parsers in both scripts must reject --top with a negative value."""

    def _run(self, script, *extra):
        return subprocess.run(
            [sys.executable, script, *extra],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_search_cards_cli(self):
        path = REPO_ROOT / "card_embeddings.json"
        if not path.exists():
            pytest.skip("card_embeddings.json not generated")
        result = self._run("search_cards.py", "--similar", "The Fool", "--top", "-1")
        assert result.returncode != 0, (
            f"expected non-zero exit, got {result.returncode}\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )
        combined = result.stderr + result.stdout
        assert "top" in combined.lower() or "negative" in combined.lower()

    def test_search_cards_cached_cli(self, synthetic_v1_5_embeddings, tmp_path):
        # The cached CLI auto-detects card_embeddings_v1_5.json; create one
        # in a tmp dir and run from there so we don't clobber repo state.
        work = tmp_path
        # Symlink/copy required files.
        for name in ("cards.json", "interpretations.json"):
            (work / name).write_text((REPO_ROOT / name).read_text())
        (work / "card_embeddings_v1_5.json").write_text(
            json.dumps(synthetic_v1_5_embeddings)
        )
        # Stub embedding_cache so the script can be imported without the
        # optional dependency installed. The --similar path never invokes
        # the model, so a no-op stub is sufficient.
        (work / "embedding_cache.py").write_text(
            "def embed(*a, **k): return None\n"
            "class EmbeddingCache:\n"
            "    def __init__(self, *a, **k): pass\n"
            "    def embed(self, *a, **k): return None\n"
        )

        env = os.environ.copy()
        env["PYTHONPATH"] = str(work) + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "search_cards_cached.py"),
             "--similar", "The Fool", "--top", "-1"],
            cwd=work,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode != 0, (
            f"expected non-zero exit, got {result.returncode}\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )
        combined = result.stderr + result.stdout
        assert "top" in combined.lower() or "negative" in combined.lower()


class TestZeroTopStillWorks:
    """top_k=0 is valid (means "no results"); fix must not break it."""

    def test_find_similar_zero(self, synthetic_v1_5_embeddings):
        from search_cards_cached import find_similar_cards
        result = find_similar_cards(
            card_name="The Fool", position="upright",
            embeddings_data=synthetic_v1_5_embeddings, top_k=0,
        )
        assert result == []

    def test_find_similar_zero_search_cards(self, embeddings_for_search_cards):
        from search_cards import find_similar_cards
        result = find_similar_cards(
            card_name="The Fool", position="upright",
            embeddings_data=embeddings_for_search_cards, top_k=0,
        )
        assert result == []
