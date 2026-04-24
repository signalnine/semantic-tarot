# Contract: view_reading_history must surface yes_no answer

## Bug

`yes_no_reading()` returns a dict with an `answer` field ("YES" or
"NO"), and `save_reading()` persists it to `reading_history.json`.
`view_reading_history()` iterates over saved entries but only prints
the spread name and the list of cards -- the `answer` field is never
read, so users viewing their history cannot see whether a saved
yes/no reading answered YES or NO.

Additionally, the per-reading card list ends with a trailing `", "`
before the newline because the list is printed with
`print(f"{card_name}{rev_marker}", end=", ")` for every card
unconditionally.

Current output for a saved yes_no reading:

```
1. 2025-01-01 12:00:00 - YES_NO spread
   Cards: The Fool (R),
```

## Fix

1. When rendering a saved reading in `view_reading_history()`, if the
   entry has an `answer` key (i.e. yes_no readings), print the
   answer.
2. Replace the `end=", "` print loop with a single joined string so
   the last card does not get a dangling comma.

## Criteria

- [x] `view_reading_history()` output for a saved yes_no reading
      contains the string `YES` or `NO` (matching the saved answer).
- [x] `view_reading_history()` output for any reading ends each
      reading's card list with the last card name (plus optional
      `(R)`), with no trailing comma/space before the newline.
- [x] Readings without an `answer` key (three_card, celtic_cross,
      etc.) still render correctly and do not mention YES/NO.
- [x] Full existing test suite still passes (`pytest` exits 0).
