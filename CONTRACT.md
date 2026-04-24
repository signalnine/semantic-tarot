# Contract: search_cards.py interactive mode must not require OPENAI_API_KEY for /similar

## Bug (tarot-4lg)

`search_cards.py::interactive_search` (line 372) bails out at startup
with "Error: OPENAI_API_KEY environment variable not set" if the
environment variable is unset. But the in-session `/similar <card>`
command operates entirely on pre-generated local embeddings -- it never
calls the OpenAI API.

This is the same bug pattern that was fixed for CLI mode in commit
1978891 (`fix(search_cards): --similar no longer requires OPENAI_API_KEY`).
The interactive equivalent was missed: a user who just wants to browse
similarities locally must still have an API key, or use the CLI form.

## Fix

Defer the OpenAI client construction until a semantic search is actually
attempted. `/similar` should run without an API key. Semantic search
(non-`/` queries) should error gracefully when the key is missing,
without exiting the interactive session.

## Criteria

- [x] `interactive_search` starts and accepts input even when
      `OPENAI_API_KEY` is unset. Verify via test that patches input to
      run `/similar The Fool`, `u`, then `/quit` and asserts the session
      runs to completion without exiting early.
- [x] `/similar <card>` produces results without an API key. Verify the
      output contains `UPRIGHT` (or `REVERSED`) for at least one card.
- [x] `/similar` does not construct an `OpenAI` client even when a key
      is set. Verify by monkeypatching `OpenAI` to raise and confirming
      `/similar` still works.
- [x] A semantic (non-`/`) query without an API key prints an error
      message containing `OPENAI_API_KEY` but does NOT exit the
      interactive loop -- the user can still issue `/similar` or
      `/quit` afterward. Verify via test.
- [x] A semantic query with an API key set still works (sanity check
      via existing unit tests; do not regress).
- [x] All existing tests still pass: `pytest` exits 0 with current
      pass count + new tests.
