# Contract: search_cards_cached.format_results text output must show card meanings

## Bug

`format_results()` in `search_cards_cached.py` accepts `cards` and
`interpretations` but never uses them to surface a card's meaning in
the default text format. Running `python3 search_cards_cached.py
"shadow"` yields only:

```
1. CardName (UPRIGHT)
   Similarity: 0.8234
```

No meaning. `search_cards.py`'s `display_search_results` shows the
meaning on each result, so the cached variant is a regression.

## Fix

In text format, print the card's basic meaning (`card['desc']` for
upright, `card['rdesc']` for reversed) on a `Meaning:` line after
`Similarity:`. Keep JSON/YAML output unchanged. Keep ASCII-art behavior
unchanged (meaning appears before the art). A card missing from the
`cards` list is skipped silently.

## Criteria

- [x] Text output for an upright result contains the card's `desc`.
      Verify: call `format_results` with a known card, upright, and
      assert the `desc` text appears in the output.
- [x] Text output for a reversed result contains the card's `rdesc`.
      Verify: call with reversed position; assert `rdesc` text appears.
- [x] Meaning appears even when `show_ascii=False`.
      Verify: both `show_ascii=True` and `show_ascii=False` include the
      meaning in text mode.
- [x] Meaning appears on a labelled `Meaning:` line.
      Verify: output contains a line starting with `Meaning:`.
- [x] Missing card in `cards` list does not crash and does not print
      a stray meaning line.
      Verify: pass a results entry whose name is not in `cards`; no
      exception, no `Meaning:` line for that entry.
- [x] JSON output is unchanged.
      Verify: existing `test_json_output_unchanged` still passes.
- [x] ASCII-art behavior is unchanged.
      Verify: existing ASCII tests still pass; the meaning line appears
      BEFORE the ASCII-art block when both are shown.
- [x] Full existing test suite still passes. Verify: `pytest` exits 0.
