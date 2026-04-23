# Contract: search_cards_cached interactive `similar` must honor reversed position

## Bug (semantic-tarot-evl)

In `search_cards_cached.py` `interactive_mode`, the `similar <card>`
command calls `find_similar_cards(canonical, 'upright', ...)` — position
is hardcoded. The non-cached `search_cards.py::interactive_search`
prompts for u/r and passes the chosen position. Users of the cached
variant cannot explore cards similar to a reversed card in interactive
mode.

## Fix

In cached interactive mode, after resolving the card name, prompt
`Position (u/r, default: u):` (matching `search_cards.py` wording).
Map `r` (case-insensitive) to `reversed`, anything else to `upright`,
and pass that to `find_similar_cards`.

## Criteria

- [x] Typing `r` at the position prompt causes
      `find_similar_cards` to be called with `position="reversed"`.
      Verify: monkeypatch `input` and `find_similar_cards`; assert the
      recorded position.
- [x] Pressing Enter (empty) defaults to `upright`.
      Verify: inject `""`; assert position `"upright"`.
- [x] Typing `u` stays `upright`.
      Verify: inject `"u"`; assert position `"upright"`.
- [x] Uppercase `R` also selects `reversed` (case-insensitive).
      Verify: inject `"R"`; assert position `"reversed"`.
- [x] Unknown card path: `find_similar_cards` is not called and no
      position prompt blocks the REPL.
      Verify: run `similar Not A Card`; ensure no extra input consumed
      and no call to the patched `find_similar_cards`.
- [x] Existing tests still pass. Verify: `pytest` exits 0.
