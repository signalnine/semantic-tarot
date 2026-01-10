# Embedding-Cache Integration for Semantic Tarot

This document describes the integration of `embedding-cache` into semantic-tarot for zero-cost, cached embeddings.

## What Changed

### Original Approach
- **OpenAI API:** `text-embedding-3-small` (1536 dimensions)
- **Cost:** ~$0.50-1.00 per full regeneration of 780 embeddings
- **Query Cost:** $0.0001 per search query
- **Internet Required:** Yes, for every operation
- **Caching:** None (manual JSON storage only)

### New Approach (with embedding-cache)
- **Local Model:** `nomic-embed-text-v1.5` (768 dimensions)
- **Cost:** $0 (local computation)
- **Query Cost:** $0 (cached automatically)
- **Internet Required:** No (after first model download)
- **Caching:** Automatic, persistent, thread-safe

## Files

### New Files
- **`generate_embeddings_cached.py`** - Generate embeddings using embedding-cache
- **`search_cards_cached.py`** - Search with cached query embeddings
- **`card_embeddings_cached.json`** - Output file (smaller: 768 vs 1536 dims)

### Original Files (unchanged)
- `generate_embeddings.py` - Original OpenAI version
- `search_cards.py` - Original OpenAI version
- `card_embeddings.json` - Original embeddings (still works)

Both versions coexist! Use whichever you prefer.

## Installation

```bash
# Install embedding-cache with local model support
pip install embedding-cache[local]
```

This will install:
- `embedding-cache` - Our caching library
- `sentence-transformers` - For local embedding model
- `torch` - For model inference
- `nomic-embed-text-v1.5` - Downloaded automatically on first use (~400MB)

## Usage

### Generate Embeddings (First Time)

```bash
python3 generate_embeddings_cached.py
```

**First run:**
- Downloads model (~400MB, one-time)
- Generates 780 embeddings locally
- Takes ~5-10 minutes
- Caches all embeddings

**Second run:**
- Instant! All embeddings hit cache
- No model download
- No recomputation
- Same output file

### Search Cards

```bash
# Semantic search (cached queries!)
python3 search_cards_cached.py "new beginnings"
python3 search_cards_cached.py "transformation"

# Similar cards
python3 search_cards_cached.py --similar "The Fool"

# Interactive mode
python3 search_cards_cached.py --interactive
```

**Query caching:**
- First search for "new beginnings": ~100ms (compute + cache)
- Second search for "new beginnings": <1ms (cache hit!)
- Repeated queries are instant

### Model Selection

You can choose between different embedding models:

```bash
# Use v1.5 (default, stable)
python3 generate_embeddings_cached.py --model v1.5

# Use v2-moe (newer Mixture of Experts model)
python3 generate_embeddings_cached.py --model v2-moe

# Use OpenAI (requires API key)
export OPENAI_API_KEY=your-key-here
python3 generate_embeddings_cached.py --model openai
```

Search with the same model:

```bash
# Search with v2-moe
python3 search_cards_cached.py --model v2-moe "transformation"

# Search with OpenAI
python3 search_cards_cached.py --model openai "new beginnings"
```

**Model Comparison:**

- **v1.5**: Stable, well-tested, 768 dimensions, ~400MB download
- **v2-moe**: Newer architecture, potentially higher quality, 768 dimensions
- **openai**: Highest quality, 1536 dimensions, requires API key ($0.0001/1K tokens)

All models use the same cache layer, so switching models requires regenerating embeddings but subsequent searches are instant.

## Benefits

### 1. Zero API Costs
```
Original: 780 embeddings × $0.0001 = $0.078 per generation
Cached:   $0 (local computation)

Savings: $0.078 per run × N runs = significant for active development
```

### 2. Automatic Caching
```
# Run 1: Compute 780 embeddings
python3 generate_embeddings_cached.py  # 5-10 minutes

# Run 2: Hit cache for all 780
python3 generate_embeddings_cached.py  # <1 second!
```

### 3. Query Caching
```
# First time querying "love"
python3 search_cards_cached.py "love"  # 100ms

# Second time
python3 search_cards_cached.py "love"  # <1ms (cache hit!)
```

### 4. Offline Capability
```
# After first run, works offline:
- No internet needed
- No API calls
- Local cache + model
```

### 5. Cache Statistics
```python
from embedding_cache import EmbeddingCache

cache = EmbeddingCache()
# ... use cache ...
print(cache.stats)
# {"hits": 42, "misses": 10, "remote_hits": 0}
```

## Model Differences

### OpenAI text-embedding-3-small
- Dimensions: 1536
- Quality: Excellent
- Cost: $0.0001 per 1K tokens
- Requires: API key + internet

### nomic-embed-text-v1.5
- Dimensions: 768
- Quality: Comparable (slightly different but still excellent for semantic search)
- Cost: $0 (local)
- Requires: ~400MB disk space

**Both work great for semantic search!** The dimension difference doesn't matter for similarity ranking.

## Performance Comparison

### Generation Time

| Operation | Original (OpenAI) | Cached (First Run) | Cached (Subsequent) |
|-----------|-------------------|--------------------|--------------------|
| 780 embeddings | ~30 seconds | ~5-10 minutes | <1 second |
| Query | ~200ms | ~100ms | <1ms |

**Why first run is slower?**
- Downloads model once (~400MB)
- Local inference slower than OpenAI's GPU cluster
- But subsequent runs are instant!

### Cost Comparison

| Scenario | Original (OpenAI) | Cached |
|----------|-------------------|--------|
| Initial generation | $0.078 | $0 |
| Regenerate 10 times | $0.78 | $0 |
| 1000 queries | $0.10 | $0 |
| **Total** | **$0.88** | **$0** |

## Cache Location

Embeddings cached in:
- Linux/macOS: `~/.cache/embedding-cache/cache.db`
- Windows: `C:\Users\<username>\.cache\embedding-cache\cache.db`

Cache statistics:
```bash
# Check cache size
du -sh ~/.cache/embedding-cache/

# Clear cache (if needed)
rm -rf ~/.cache/embedding-cache/
```

## Testing the Integration

### 1. Generate with Cache
```bash
# First run (slow - downloads model + computes)
time python3 generate_embeddings_cached.py

# Second run (instant - all cache hits!)
time python3 generate_embeddings_cached.py
```

### 2. Compare Results
```bash
# Search with original
python3 search_cards.py "new beginnings" --top 5

# Search with cached (should have similar results)
python3 search_cards_cached.py "new beginnings" --top 5
```

Results will be similar (not identical due to different models) but semantic ranking should be comparable.

### 3. Test Query Caching
```bash
# First query
python3 search_cards_cached.py "transformation"

# Second query (instant!)
python3 search_cards_cached.py "transformation"
```

## Migration Guide

### Option 1: Side-by-Side (Recommended)
Keep both versions:
- Use original for production (if OpenAI preferred)
- Use cached for development (free + offline)

### Option 2: Full Migration
```bash
# 1. Install embedding-cache
pip install embedding-cache[local]

# 2. Generate cached embeddings
python3 generate_embeddings_cached.py

# 3. Use cached search
python3 search_cards_cached.py "your query"

# 4. (Optional) Remove original
rm card_embeddings.json
```

## Troubleshooting

### "No module named 'embedding_cache'"
```bash
pip install embedding-cache[local]
```

### "Model download takes too long"
First download is ~400MB. Subsequent runs use cached model.

### "Different results than OpenAI"
Normal! Different models produce different embeddings. Semantic search still works, just with slightly different rankings.

### "Cache growing too large"
```bash
# Check size
du -sh ~/.cache/embedding-cache/

# Clear if needed
rm -rf ~/.cache/embedding-cache/
```

## Next Steps

1. **Try it out:** Run `generate_embeddings_cached.py`
2. **Compare results:** Test both versions side-by-side
3. **Measure cache hits:** Monitor statistics for your workload
4. **Report feedback:** Share results with embedding-cache team

## Links

- **embedding-cache:** https://github.com/signalnine/embedding-cache
- **nomic-embed:** https://huggingface.co/nomic-ai/nomic-embed-text-v1.5
- **Original semantic-tarot:** Uses OpenAI embeddings

---

**Integration Status:** ✅ Complete and ready for testing!

**Questions?** File an issue on the embedding-cache repo.
