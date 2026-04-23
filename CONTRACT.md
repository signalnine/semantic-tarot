# Contract: search_cards_cached.py --similar must accept case-variant card names

## Bug

`search_cards_cached.py`'s `find_similar_cards()` compares card names with
`card_data['card_name'] == card_name` (case-sensitive). Both entry points
-- the `--similar` CLI flag and the interactive `similar <card>` command
-- pass the user's input straight through. A lowercase or mixed-case
query like `--similar "the fool"` raises `ValueError: Card not found:
the fool (upright)` even though "The Fool" is in the deck.

The non-cached `search_cards.py` avoids this by doing a case-insensitive
lookup at the CLI layer (`c['name'].lower() == card_name.lower()`) and
passing the canonical name to `find_similar_cards`. The cached version
skips that step.

## Fix

Normalize the input at both entry points in `search_cards_cached.py`
(CLI `--similar` and interactive `similar <cmd>`): look up the canonical
card name case-insensitively before calling `find_similar_cards`. Emit a
clear "card not found" error when no match exists. `find_similar_cards`
itself remains unchanged so its contract (exact match on canonical name)
is preserved.

## Criteria

- [x] `--similar "the fool"` succeeds and returns results for "The Fool".
      Verify: invoke CLI with lowercase name, exit code 0, stdout contains
      card names.
- [x] `--similar "THE FOOL"` succeeds the same way (uppercase).
      Verify: same as above with uppercase input.
- [x] `--similar "  The Fool  "` succeeds (whitespace stripped).
      Verify: same as above with padded input.
- [x] `--similar "Not A Real Card"` fails with a clear error and non-zero
      exit code. Verify: stderr mentions the card, exit code != 0.
- [x] Interactive `similar the fool` succeeds (case-insensitive).
      Verify: drive `interactive_mode` with a stub stdin, assert output
      contains similar-card names instead of an error.
- [x] `find_similar_cards()` itself is unchanged: passing a non-canonical
      name still raises `ValueError`. Verify: call directly with lowercase
      and expect `ValueError`.
- [x] Full existing test suite still passes. Verify: `pytest` exits 0.
