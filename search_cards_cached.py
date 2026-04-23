#!/usr/bin/env python3
"""
Search tarot cards using vector embeddings with embedding-cache.
This version uses local caching for query embeddings.

CHANGES FROM ORIGINAL:
- Uses embedding-cache instead of OpenAI API for query embeddings
- Queries are cached automatically (repeated searches are instant)
- Works offline
- Zero API costs

Usage:
    # Semantic search
    python3 search_cards_cached.py "new beginnings"

    # Find similar cards
    python3 search_cards_cached.py --similar "The Fool"
    python3 search_cards_cached.py --similar "The Fool" --reversed

    # Display with ASCII art
    python3 search_cards_cached.py "new beginnings" --ascii
    python3 search_cards_cached.py --similar "The Fool" --art --top 3

    # JSON/YAML output
    python3 search_cards_cached.py "transformation" --json
    python3 search_cards_cached.py --similar "The Star" --yaml

    # Interactive mode
    python3 search_cards_cached.py --interactive
"""

import json
import os
import sys
import argparse
import numpy as np
from typing import List, Dict, Tuple, Optional

# Import our new embedding cache!
from embedding_cache import embed

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Configuration
CARDS_FILE = 'cards.json'
INTERPRETATIONS_FILE = 'interpretations.json'

# Model name mappings
MODEL_MAP = {
    'v1.5': 'nomic-ai/nomic-embed-text-v1.5',
    'v2-moe': 'nomic-ai/nomic-embed-text-v2-moe',
    'openai': 'openai:text-embedding-3-small'
}


def load_embeddings(embeddings_file: str) -> List[Dict]:
    """Load pre-generated embeddings from file"""
    if not os.path.exists(embeddings_file):
        raise FileNotFoundError(
            f"Embeddings file not found: {embeddings_file}\n"
            "Please run generate_embeddings_cached.py first to create embeddings."
        )

    with open(embeddings_file, 'r') as f:
        return json.load(f)


def load_cards() -> List[Dict]:
    """Load card data"""
    with open(CARDS_FILE, 'r') as f:
        return json.load(f)


def load_interpretations() -> Dict:
    """Load interpretation data"""
    with open(INTERPRETATIONS_FILE, 'r') as f:
        return json.load(f)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First embedding vector
        vec2: Second embedding vector

    Returns:
        Similarity score between -1 and 1 (1 = most similar)
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def get_query_embedding(query: str, model: str) -> List[float]:
    """
    Generate embedding for a search query using embedding-cache.

    This version:
    - Uses local model (no API cost)
    - Caches queries automatically
    - Works offline

    Args:
        query: Search query text
        model: Full model name to use

    Returns:
        Embedding vector as list
    """
    # embedding-cache handles normalization, caching, and computation
    from embedding_cache import EmbeddingCache
    cache = EmbeddingCache(model=model)
    embedding = cache.embed(query)
    return embedding.tolist()


def search_cards(
    query: str,
    embeddings_data: List[Dict],
    model: str,
    top_k: int = 5,
    position_filter: str = None,
    system_filter: str = None
) -> List[Tuple[str, str, float]]:
    """
    Search for cards semantically similar to a query.

    Args:
        query: Search query (e.g., "new beginnings", "letting go")
        embeddings_data: List of card embeddings
        model: Full model name to use for query embedding
        top_k: Number of results to return
        position_filter: Filter by 'upright' or 'reversed' (None for both)
        system_filter: Filter by interpretation system (None for combined/all)

    Returns:
        List of (card_name, position, similarity_score) tuples
    """
    # Get query embedding (cached if seen before!)
    query_embedding = get_query_embedding(query, model)

    # Determine which system to use (default to 'combined' if not specified)
    target_system = system_filter if system_filter else 'combined'

    # Calculate similarities
    similarities = []
    for card_data in embeddings_data:
        # Apply system filter
        if card_data.get('interpretation_system', 'combined') != target_system:
            continue

        # Apply position filter if specified
        if position_filter and card_data['position'] != position_filter:
            continue

        similarity = cosine_similarity(query_embedding, card_data['embedding'])
        similarities.append((
            card_data['card_name'],
            card_data['position'],
            similarity
        ))

    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[2], reverse=True)

    return similarities[:top_k]


def resolve_card_name(name: str, cards: List[Dict]) -> Optional[str]:
    """Return the canonical card name matching `name` case-insensitively.

    Returns None if no card matches. Surrounding whitespace is ignored.
    """
    if name is None:
        return None
    needle = name.strip().lower()
    if not needle:
        return None
    for card in cards:
        if card["name"].lower() == needle:
            return card["name"]
    return None


def find_similar_cards(
    card_name: str,
    position: str,
    embeddings_data: List[Dict],
    top_k: int = 5,
    system_filter: str = None,
    exclude_same_card: bool = True,
) -> List[Tuple[str, str, float]]:
    """
    Find cards similar to a given card.

    Args:
        card_name: Name of the card to find similar cards for
        position: 'upright' or 'reversed'
        embeddings_data: List of card embeddings
        top_k: Number of similar cards to return (excluding the input card)
        system_filter: Filter by interpretation system (None for combined/all)
        exclude_same_card: Exclude same card in both positions (default True)

    Returns:
        List of (card_name, position, similarity_score) tuples
    """
    # Determine which system to use
    target_system = system_filter if system_filter else 'combined'

    # Find the embedding for the input card
    input_embedding = None
    for card_data in embeddings_data:
        if (card_data['card_name'] == card_name and
            card_data['position'] == position and
            card_data.get('interpretation_system', 'combined') == target_system):
            input_embedding = card_data['embedding']
            break

    if input_embedding is None:
        raise ValueError(f"Card not found: {card_name} ({position})")

    # Calculate similarities with all other cards
    similarities = []
    for card_data in embeddings_data:
        # Apply system filter
        if card_data.get('interpretation_system', 'combined') != target_system:
            continue

        # Exclude same card (both positions) by default; otherwise only
        # skip the exact card+position match.
        if exclude_same_card:
            if card_data['card_name'] == card_name:
                continue
        elif (card_data['card_name'] == card_name and
              card_data['position'] == position):
            continue

        similarity = cosine_similarity(input_embedding, card_data['embedding'])
        similarities.append((
            card_data['card_name'],
            card_data['position'],
            similarity
        ))

    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[2], reverse=True)

    return similarities[:top_k]


def format_results(
    results: List[Tuple[str, str, float]],
    cards: List[Dict],
    interpretations: Dict,
    show_ascii: bool = False,
    format_type: str = 'text'
) -> str:
    """
    Format search results for display.

    Args:
        results: List of (card_name, position, score) tuples
        cards: Card data
        interpretations: Interpretation data
        show_ascii: Whether to show ASCII art
        format_type: Output format ('text', 'json', 'yaml')

    Returns:
        Formatted string
    """
    if format_type == 'json':
        output = []
        for card_name, position, score in results:
            output.append({
                'card': card_name,
                'position': position,
                'similarity': float(score)
            })
        return json.dumps(output, indent=2)

    elif format_type == 'yaml' and YAML_AVAILABLE:
        output = []
        for card_name, position, score in results:
            output.append({
                'card': card_name,
                'position': position,
                'similarity': float(score)
            })
        return yaml.dump(output, default_flow_style=False)

    else:  # text format
        output_lines = []
        for i, (card_name, position, score) in enumerate(results, 1):
            output_lines.append(f"\n{i}. {card_name} ({position.upper()})")
            output_lines.append(f"   Similarity: {score:.4f}")

            # Find card data
            card = next((c for c in cards if c['name'] == card_name), None)
            if card and show_ascii:
                art_key = 'reversed' if position == 'reversed' else 'card'
                art = card.get(art_key) or card.get('card', '')
                if art:
                    output_lines.append("")
                    output_lines.append(art)

        return "\n".join(output_lines)


def interactive_mode(embeddings_data: List[Dict], cards: List[Dict], interpretations: Dict, model: str):
    """Run interactive search mode"""
    print("\n" + "=" * 70)
    print("INTERACTIVE TAROT SEARCH (with embedding-cache)")
    print("=" * 70)
    print("\nCommands:")
    print("  <query>          - Search for cards matching a query")
    print("  similar <card>   - Find similar cards")
    print("  quit/exit        - Exit interactive mode")
    print()

    while True:
        try:
            query = input("🔮 > ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye! ✨")
                break

            if query.lower().startswith('similar '):
                # Similar card search
                card_name = query[8:].strip()
                canonical = resolve_card_name(card_name, cards)
                if canonical is None:
                    print(f"Error: Card not found: {card_name}")
                    continue
                try:
                    results = find_similar_cards(canonical, 'upright', embeddings_data, top_k=5)
                    print(format_results(results, cards, interpretations))
                except ValueError as e:
                    print(f"Error: {e}")
            else:
                # Semantic search
                results = search_cards(query, embeddings_data, model, top_k=5)
                print(format_results(results, cards, interpretations))

        except KeyboardInterrupt:
            print("\n\nGoodbye! ✨")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Search tarot cards using semantic embeddings (with embedding-cache)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--similar', metavar='CARD', help='Find cards similar to this card')
    parser.add_argument('--reversed', action='store_true', help='Use reversed position for similarity search')
    parser.add_argument('--top', type=int, default=5, help='Number of results to return (default: 5)')
    parser.add_argument('--ascii', '--art', action='store_true', help='Show ASCII art for cards')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--yaml', action='store_true', help='Output results as YAML')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive search mode')
    parser.add_argument(
        '--model',
        choices=['v1.5', 'v2-moe', 'openai'],
        default='v1.5',
        help='Embedding model to use (default: v1.5)'
    )

    args = parser.parse_args()

    # Get full model name
    model = MODEL_MAP[args.model]

    # Auto-detect embeddings file based on model
    model_suffix = args.model.replace('-', '_').replace('.', '_')
    embeddings_file = f'card_embeddings_{model_suffix}.json'

    # Load data
    try:
        embeddings_data = load_embeddings(embeddings_file)
        cards = load_cards()
        interpretations = load_interpretations()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine output format
    format_type = 'text'
    if args.json:
        format_type = 'json'
    elif args.yaml:
        if not YAML_AVAILABLE:
            print("Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        format_type = 'yaml'

    # Interactive mode
    if args.interactive:
        interactive_mode(embeddings_data, cards, interpretations, model)
        return

    # Similar card search
    if args.similar:
        position = 'reversed' if args.reversed else 'upright'
        canonical = resolve_card_name(args.similar, cards)
        if canonical is None:
            print(f"Error: Card not found: {args.similar}", file=sys.stderr)
            sys.exit(1)
        try:
            results = find_similar_cards(canonical, position, embeddings_data, top_k=args.top)
            print(format_results(results, cards, interpretations, args.ascii, format_type))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Semantic search
    if not args.query:
        parser.print_help()
        sys.exit(1)

    results = search_cards(args.query, embeddings_data, model, top_k=args.top)
    print(format_results(results, cards, interpretations, args.ascii, format_type))


if __name__ == '__main__':
    main()
