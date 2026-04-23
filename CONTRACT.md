# Contract: tarot.py search_by_keyword must cover interpretation text

## Bug

`tarot.search_by_keyword()` (menu option 9, "Search by keyword") only
checks `card['name']`, `card['desc']`, and `card['rdesc']` from
`cards.json`. Those are one-line blurbs. Central themes that live in
`interpretations.json` -- "shadow" is the canonical example, appearing
20+ times across the Jungian system but never in `cards.json` -- return
"No cards found matching 'shadow'", which surprises anyone relying on
the menu to browse by concept.

The menu advertises this as a general search tool and the README
describes it as "Search through all card descriptions", so the intent
is broader than the cards.json blurbs.

## Fix

Extend `search_by_keyword` to also scan every interpretation system's
upright and reversed text (case-insensitively). A card that matches in
multiple places appears once. Existing name/desc/rdesc matches keep
working. The empty-keyword guard from the previous fix (`tarot-fx5`)
is preserved.

## Criteria

- [x] `search_by_keyword("shadow")` returns a non-empty list.
      Verify: call the function directly, assert result is truthy.
- [x] `search_by_keyword("Fool")` still returns The Fool (name match).
      Verify: result contains a card whose name is "The Fool".
- [x] A keyword taken from `cards.json` desc still matches that card.
      Verify: pick first card, use first word of its `desc`, assert the
      card is in the results.
- [x] Case-insensitive for interpretation matches: "shadow", "SHADOW",
      and "ShAdOw" return the same set of cards.
      Verify: compare sorted name lists from the three queries.
- [x] Cards are not duplicated when the keyword matches in multiple
      systems for the same card.
      Verify: len(names) == len(set(names)).
- [x] Nonsense keyword returns an empty list.
      Verify: search for an obvious non-word, assert `== []`.
- [x] Empty / whitespace-only keyword still returns [] without flooding
      output (regression guard for the prior empty-keyword fix).
      Verify: `search_by_keyword("")` and `search_by_keyword("   ")`
      both return `[]`.
- [x] Full existing test suite still passes. Verify: `pytest` exits 0.
