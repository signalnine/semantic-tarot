# Contract: search_cards.py --similar must accept whitespace-padded card names

## Bug (semantic-tarot-dxd)

`search_cards.py --similar` matches card names case-insensitively
(`c['name'].lower() == args.similar.lower()`) but does not strip
surrounding whitespace. Passing `--similar "  The Fool  "` fails with
`✗ Card not found:   The Fool  `. The cached variant
(`search_cards_cached.py --similar`) and `search_cards.py`'s own
interactive `/similar` command both strip whitespace before matching,
so the CLI `--similar` flag is the odd one out.

## Fix

In `search_cards.py::main`, strip `args.similar` before the
case-insensitive lookup so `"  The Fool  "`, `"The Fool  "`, and
`"  The Fool"` all resolve to `The Fool`. Use the stripped value when
constructing the "Card not found" error message as well, so feedback
matches the attempted lookup.

## Criteria

- [x] `python3 search_cards.py --similar "  The Fool  " --top 3` exits 0
      and prints results (UPRIGHT/REVERSED lines). Verify via a new
      test in `tests/` that runs `search_cards.main()` with whitespace-
      padded names and asserts success + results.
- [x] Leading-only and trailing-only whitespace also resolve to the
      canonical card. Verify with parametrized test.
- [x] Unknown card names still fail with a non-zero exit code and a
      message that names the card. Verify via test.
- [x] Existing tests still pass. Verify: `pytest` exits 0.
