# Contract: Five bd issues

Tracks bd issues semantic-tarot-{5aa, ab7, 4f4, 1ho, 1sr}.

## semantic-tarot-5aa: view_reading_history KeyError on non-list JSON

- [x] When `reading_history.json` contains a JSON object (dict), `view_reading_history()` does not raise. Verify via test: write `{"not":"a list"}` to history file, call `view_reading_history()`, assert it does not raise. Expect cleanup behavior consistent with `_load_history_or_recover`: corrupt file is backed up and the function reports a non-error message.
- [x] Same for a JSON string payload (e.g. `"hello"`) and a JSON number payload.
- [x] Existing tests in `test_reading_history.py` continue to pass.

## semantic-tarot-ab7: daily_card AttributeError on non-dict JSON

- [x] When `daily_card.json` contains a JSON list, `daily_card()` does not raise AttributeError. It falls through to fresh-card generation (writes a new dict-shaped file with today's date and a valid card_name). Verify via test.
- [x] Same when the file contains a JSON string or number or null.
- [x] Existing tests in `test_daily_card.py` continue to pass.

## semantic-tarot-1ho: search_cards.py relative paths

- [x] `EMBEDDINGS_FILE`, `CARDS_FILE`, `INTERPRETATIONS_FILE` resolve to absolute paths anchored to `__file__`. Verified via a unit test that imports the module and asserts `os.path.isabs(...)` for each constant.
- [x] Running `search_cards.py --similar 'The Fool' --top 2` from `/tmp` produces output (does not error with "Embeddings file not found"). Verified via subprocess test.

## semantic-tarot-4f4: search_cards_cached.py + generate scripts relative paths

- [x] `search_cards_cached.py`: `CARDS_FILE`, `INTERPRETATIONS_FILE`, and the auto-detected embeddings_file are absolute paths anchored to `__file__`. Verified via subprocess test running `--similar 'The Fool' --top 2 --model v1.5` from `/tmp`.
- [x] `generate_embeddings.py`: `CARDS_FILE`, `INTERPRETATIONS_FILE`, `EMBEDDINGS_OUTPUT_FILE` are absolute paths. Unit test asserts `os.path.isabs`.
- [x] `generate_embeddings_cached.py`: `CARDS_FILE`, `INTERPRETATIONS_FILE` are absolute paths. Unit test asserts `os.path.isabs`.

## semantic-tarot-1sr: /similar prefix match too loose

- [x] In `search_cards.py` interactive_search, `/similars`, `/similar2`, `/similartothis` are NOT routed to the /similar branch. Verify via test that pipes input `/similars\n/quit\n` and asserts the output does not say "/similar requires a card name" or "Card not found".
- [x] Bare `/similar` (no args) still produces the help message. `/similar The Fool` still works.

## Done

- [x] All new tests pass.
- [x] All existing tests still pass: `pytest` exits 0 with original 166 passed + 1 skipped, plus new tests.
