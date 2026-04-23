# Contract: search_cards.py --similar must not require OPENAI_API_KEY

## Bug

`search_cards.py` unconditionally exits with an OPENAI_API_KEY error at
the top of `main()`, even for `--similar <card>` invocations that operate
purely on the pre-generated `card_embeddings.json` file and never call
the OpenAI API.

Current behavior (reproduced):

```
$ env -u OPENAI_API_KEY python3 search_cards.py --similar "The Fool"
Error: OPENAI_API_KEY environment variable not set
Please set it with: export OPENAI_API_KEY='your-key-here'
$ echo $?
1
```

`find_similar_cards()` consumes local embeddings only. The OpenAI client
is only needed to embed a live query string (semantic search mode and
interactive mode). Requiring the key for `--similar` blocks offline /
read-only use of the tool.

## Fix

Move the OPENAI_API_KEY check (and `OpenAI(...)` client instantiation)
out of the unconditional preamble of `main()` and into the semantic
search branch where the query embedding is actually generated. The
`--similar` branch must not touch the OpenAI client at all.

## Criteria

- [x] `search_cards.main()` called with `["--similar", "The Fool"]`
      and `OPENAI_API_KEY` unset exits 0 and prints at least one
      similar card row.
- [x] `search_cards.main()` called with
      `["--similar", "The Fool", "--json", "--top", "3"]` and no API
      key emits valid JSON (a non-empty list of dicts) on stdout.
- [x] `search_cards.main()` called with `["transformation"]` (semantic
      search) and no API key still exits non-zero with an error that
      mentions `OPENAI_API_KEY`.
- [x] `--similar` does not instantiate an OpenAI client: monkeypatching
      `search_cards.OpenAI` to a sentinel that raises on construction
      does not break `--similar`.
- [x] Full existing test suite still passes (`pytest` exits 0).
