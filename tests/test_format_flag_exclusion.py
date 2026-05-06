"""
Regression test for tarot-4ve: passing both --json and --yaml must error
out via argparse rather than silently preferring JSON.
"""

import os
import subprocess
import sys
import types

if "embedding_cache" not in sys.modules:
    stub = types.ModuleType("embedding_cache")
    stub.embed = lambda *a, **kw: None
    stub.EmbeddingCache = object
    sys.modules["embedding_cache"] = stub

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _run(script, *args):
    return subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, script), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_search_cards_rejects_both_json_and_yaml():
    result = _run('search_cards.py', '--similar', 'The Fool', '--json', '--yaml')
    assert result.returncode != 0
    assert 'not allowed with' in result.stderr or 'argument' in result.stderr


def test_search_cards_cached_rejects_both_json_and_yaml():
    result = _run('search_cards_cached.py', '--similar', 'The Fool', '--json', '--yaml')
    assert result.returncode != 0
    assert 'not allowed with' in result.stderr or 'argument' in result.stderr


def test_search_cards_single_format_flag_still_parses():
    """Sanity check: single-flag invocations are unaffected by the
    mutually-exclusive group."""
    result = _run('search_cards.py', '--similar', 'The Fool', '--top', '1', '--json')
    assert result.returncode == 0, result.stderr
