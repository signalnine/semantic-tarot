"""
Tests for tarot.py module-load behavior when cards.json is missing.

Covers tarot-xew: prior to the fix, importing tarot.py with cards.json
absent raised a raw FileNotFoundError stack trace. The fix wraps the
load in try/except and exits with a clear actionable message.
"""

import os
import subprocess
import sys
import textwrap


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _run_import(env_overrides):
    """Spawn a fresh interpreter that imports tarot under the given env."""
    env = os.environ.copy()
    env.update(env_overrides)
    code = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, %r)
        import tarot  # noqa: F401
        """
    ) % REPO_ROOT
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
    )


def test_import_succeeds_when_cards_json_present():
    proc = _run_import({})
    assert proc.returncode == 0, (
        "tarot import failed with cards.json present: "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_import_with_missing_cards_json_exits_with_clear_message(tmp_path):
    # Point CARDS_FILE at a path that does not exist by relocating HERE
    # via a wrapper script. We do this by running a small Python program
    # that monkeypatches os.path.dirname before importing tarot, but the
    # simplest portable approach is to copy tarot.py into an empty dir
    # and import it from there, so its sibling cards.json is absent.
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    src = os.path.join(REPO_ROOT, "tarot.py")
    dst = isolated / "tarot.py"
    dst.write_bytes(open(src, "rb").read())

    proc = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, %r); import tarot" % str(isolated)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0, (
        "Expected non-zero exit when cards.json is missing; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    combined = proc.stdout + proc.stderr
    assert "cards.json" in combined, (
        f"Expected 'cards.json' in error output; got: {combined!r}"
    )
    # No raw FileNotFoundError traceback line should be the only signal.
    # A clear message must be present in addition (or instead).
    assert "Required" in combined or "not found" in combined, (
        f"Expected a friendly error message; got: {combined!r}"
    )
