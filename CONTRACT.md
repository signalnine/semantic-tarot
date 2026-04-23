# Contract: daily_card must print header once and handle invalid saved card_name cleanly

## Bug

`tarot.daily_card()` has a control-flow bug when `daily_card.json` has
today's date but the saved `card_name` doesn't match any card in the deck
(e.g. deck renamed, data corruption, or manual edit).

Current behavior:
1. Reads today's entry, prints the "CARD OF THE DAY - <date>" header.
2. Loops through `tarot_deck` looking for the saved card_name; no match.
3. Falls out of the loop WITHOUT returning.
4. Execution proceeds to the fresh-generation block, which prints the
   header a SECOND time, draws a new random card, and OVERWRITES
   `daily_card.json`.

The header is printed twice and the "daily" invariant (same card per
day) is silently broken when the saved entry is stale.

## Fix

Separate the "load today's card" step from the "generate fresh" step.
Resolve the saved card first; only if today's entry resolves to a real
card do we take the early-return path. Otherwise fall through once to
the generation block, which prints the header and saves. Header is
printed exactly once in every code path.

## Criteria

- [x] When `daily_card.json` has today's date and a valid card_name, the
      header is printed exactly once and no new card is drawn/saved.
      Verify: count occurrences of "CARD OF THE DAY" in captured stdout; file unchanged.
- [x] When `daily_card.json` has today's date but an invalid card_name,
      the header is printed exactly once and a fresh card is saved.
      Verify: stdout contains the header exactly once; file now has a valid card_name.
- [x] When `daily_card.json` has a stale date, the header is printed
      exactly once and a fresh card is saved for today.
      Verify: stdout contains header once; file date is today; file card_name is in deck.
- [x] When `daily_card.json` is missing, the header is printed exactly
      once and a fresh card is saved.
      Verify: stdout contains header once; file created with today's date and a valid card.
- [x] Full existing test suite still passes. Verify: `pytest` exits 0.
