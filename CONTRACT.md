# Contract: Multi-card tarot readings must draw unique cards

## Bug

`tarot.py`'s `draw_card()` uses `random.choice(tarot_deck)`, which draws
*with replacement*. Every multi-card spread (three_card_reading,
celtic_cross_reading, horseshoe_reading, relationship_reading) calls
`draw_card()` in a loop, so the same card can appear two or more times
in the same reading. A real tarot reading shuffles once and deals from a
physical deck, so each card is unique within a spread.

## Fix

Add a helper that returns `n` distinct cards sampled without replacement
from `tarot_deck`, and have the multi-card readings use it. Single-card
entry points (`single_card_reading`, `yes_no_reading`, `daily_card`) are
unaffected.

## Criteria

- [x] A helper `draw_unique_cards(n, allow_reversed=True)` returns a list
      of `n` `(card, is_reversed)` tuples where every `card['name']` is
      distinct. Verify: call with `n=10`, assert `len({c['name'] for c, _
      in result}) == 10`.
- [x] `draw_unique_cards` honors `allow_reversed=False`. Verify: call with
      `n=10, allow_reversed=False` and assert every `is_reversed` is
      `False`.
- [x] Raises `ValueError` when `n` exceeds deck size. Verify: call with
      `n=len(tarot_deck)+1` and expect `ValueError`.
- [x] The three-, five-, seven-, and ten-card spreads use the helper so
      their results contain unique card names. Verify: monkeypatch
      `input` and `display_card`, run each reading, collect its
      `cards_drawn`, assert all card names distinct.
- [x] Single-card paths unchanged. Verify: `draw_card()` still returns a
      single `(card, is_reversed)` tuple as before.
- [x] Full existing test suite still passes. Verify: `pytest` exits 0.
