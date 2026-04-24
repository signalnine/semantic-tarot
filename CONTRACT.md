# Contract: tarot.compare_interpretations must echo attempted card name on miss

## Bug (tarot-6ka)

`tarot.py::compare_interpretations` strips the user's input and does
a case-insensitive lookup, but when no card matches it prints a bare
`"✗ Card not found."` with no echo of what was attempted. This is
inconsistent with:

- `tarot.search_card` (fixed in 2f069d4) -- prints the stripped name
- `search_cards.py --similar` (fixed in e86e56f) -- prints the stripped name
- `search_cards.py` interactive `/similar` -- prints the entered name

A user running menu option 15 ("Compare all interpretations for a card")
and mistyping a name has no signal of what was actually searched, which
makes typos invisible.

## Fix

In `tarot.py::compare_interpretations`, when the lookup fails, include
the stripped attempted name in the "Card not found" message. Match the
phrasing used elsewhere in the file: `f"✗ Card not found: {needle}"`.

## Criteria

- [x] `compare_interpretations` with an unknown card name prints a
      message containing the stripped attempted name. Verify via test
      that monkeypatches `builtins.input` to return an unknown name and
      asserts the printed output contains that name.
- [x] Whitespace is stripped before echoing -- padding does not appear
      in the output. Verify via test with `"   Bogus Card   "` input.
- [x] When the card IS found, no "Card not found" line is printed.
      Verify via test with `"The Fool"` input.
- [x] Case-insensitive matching still works (e.g. `"the fool"` finds
      The Fool). Verify via test.
- [x] Existing tests still pass. Verify: `pytest` exits 0 with the
      same pass count + 1 (new tests).
