# Contract: tarot.search_card must strip whitespace and echo the attempted name

## Bug (semantic-tarot-teq)

`tarot.py::search_card` does a case-insensitive name comparison
(`card['name'].lower() == card_name.lower()`) but does not strip
surrounding whitespace. Calling `search_card("  The Fool  ")` fails
with a generic `Card not found.` message that does not echo the
attempted name.

This mirrors the (closed) `semantic-tarot-dxd` / `-n7u` pattern that
was fixed for `search_cards.py --similar`. The in-repo callers in
`main()` happen to strip before calling, but the function itself is
inconsistent with `compare_interpretations()` (which strips) and with
the `--similar` CLI (which now strips).

## Fix

In `tarot.py::search_card`, strip `card_name` before the
case-insensitive lookup so `"  The Fool  "`, `"The Fool  "`, and
`"  The Fool"` all resolve to `The Fool`. Include the stripped name
in the "Card not found" message so users can see what the program
actually searched for.

## Criteria

- [x] `search_card("  The Fool  ")` returns a card dict (not None)
      and displays the card. Verify via a new test that calls
      `tarot.search_card` with whitespace-padded names and asserts
      the return value is non-None with `name == "The Fool"`.
- [x] Leading-only and trailing-only whitespace also resolve to the
      canonical card. Verify with parametrized test.
- [x] Unknown card names still return None and print a message that
      includes the stripped attempted name. Verify via test with
      `capsys`.
- [x] Case-insensitive matching still works
      (`search_card("the fool")` returns a card). Verify via test.
- [x] Existing tests still pass. Verify: `pytest` exits 0.
