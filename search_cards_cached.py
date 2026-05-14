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

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Configuration -- anchor data file paths to this script so the CLI works
# from any working directory, not just the repo root.
HERE = os.path.dirname(os.path.abspath(__file__))
CARDS_FILE = os.path.join(HERE, 'cards.json')
INTERPRETATIONS_FILE = os.path.join(HERE, 'interpretations.json')

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


def parse_position(raw: str) -> str:
    """Parse user-typed position input into 'reversed' or 'upright'.

    Accepts 'r', 'rev', 'reversed' (case-insensitive, with surrounding
    whitespace) as reversed. Anything else (including empty) is upright.
    """
    if raw is None:
        return 'upright'
    s = raw.strip().lower()
    if s in ('r', 'rev', 'reversed'):
        return 'reversed'
    return 'upright'


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
    if top_k < 0:
        raise ValueError(f"top_k must be non-negative, got {top_k}")

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
    if top_k < 0:
        raise ValueError(f"top_k must be non-negative, got {top_k}")

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
    format_type: str = 'text',
    system: str = 'combined'
) -> str:
    """
    Format search results for display.

    Args:
        results: List of (card_name, position, score) tuples
        cards: Card data
        interpretations: Interpretation data
        show_ascii: Whether to show ASCII art
        format_type: Output format ('text', 'json', 'yaml')
        system: Interpretation system; when not 'combined', the meaning
            shown is taken from interpretations.json for that system

    Returns:
        Formatted string
    """
    def _resolve_meaning(card_name, position):
        """Mirror the text branch's priority: system-specific interpretation,
        then the basic upright/reversed description from cards.json. Empty
        string when no card data is available."""
        card = next((c for c in cards if c['name'] == card_name), None)
        if not card:
            return ''
        meaning = None
        if system != 'combined' and interpretations:
            card_interp = interpretations.get(card_name)
            if card_interp and system in card_interp:
                meaning = card_interp[system].get(position)
        if not meaning:
            meaning_key = 'rdesc' if position == 'reversed' else 'desc'
            meaning = card.get(meaning_key) or card.get('desc', '')
        return meaning or ''

    def _structured_results():
        # Schema matches search_cards.py:format_results_as_data so downstream
        # tools can parse output from either CLI identically.
        return [
            {
                'card_name': card_name,
                'position': position,
                'similarity': float(score),
                'meaning': _resolve_meaning(card_name, position),
            }
            for card_name, position, score in results
        ]

    if format_type == 'json':
        return json.dumps(_structured_results(), indent=2)

    elif format_type == 'yaml':
        # Don't silently degrade to text when pyyaml is missing -- callers
        # other than main() (e.g. interactive flows) would think they got
        # YAML and emit text. Raise so the missing dependency is visible.
        if not YAML_AVAILABLE:
            raise RuntimeError(
                "YAML output requested but pyyaml is not installed. "
                "Install with: pip install pyyaml"
            )
        return yaml.dump(_structured_results(), default_flow_style=False)

    else:  # text format
        output_lines = []
        for i, (card_name, position, score) in enumerate(results, 1):
            output_lines.append(f"\n{i}. {card_name} ({position.upper()})")
            output_lines.append(f"   Similarity: {score:.4f}")

            # Find card data
            card = next((c for c in cards if c['name'] == card_name), None)
            if card:
                meaning = None
                if system != 'combined' and interpretations:
                    card_interp = interpretations.get(card_name)
                    if card_interp and system in card_interp:
                        meaning = card_interp[system].get(position)
                if not meaning:
                    meaning_key = 'rdesc' if position == 'reversed' else 'desc'
                    meaning = card.get(meaning_key) or card.get('desc', '')
                if meaning:
                    output_lines.append(f"   Meaning: {meaning}")

                if show_ascii:
                    if position == 'reversed' and card.get('reversed'):
                        art = card['reversed']
                        output_lines.append("")
                        output_lines.append(art)
                    else:
                        art = card.get('card', '')
                        if art:
                            output_lines.append("")
                            if position == 'reversed':
                                # Avoid silently showing upright art under a REVERSED label.
                                output_lines.append("(no reversed art for this card; showing upright)")
                            output_lines.append(art)

        return "\n".join(output_lines)


VALID_SYSTEMS = (
    'rws_traditional', 'thoth_crowley', 'jungian_psychological',
    'modern_intuitive', 'combined',
)


def interactive_mode(
    embeddings_data: List[Dict],
    cards: List[Dict],
    interpretations: Dict,
    model: str,
    system: str = 'combined',
):
    """Run interactive search mode.

    `system`, top_k and ASCII-art display can be changed mid-session via
    /system, /top, and /art commands. The bare 'similar' or '/similar'
    forms (no card name) are rejected instead of being routed to
    semantic search.
    """
    current_system = system if system in VALID_SYSTEMS else 'combined'
    current_top_k = 5
    current_show_art = False
    current_include_same_card = False

    print("\n" + "=" * 70)
    print("INTERACTIVE TAROT SEARCH (with embedding-cache)")
    print("=" * 70)
    print("\nCommands:")
    print("  <query>            - Search for cards matching a query")
    print("  similar <card>     - Find similar cards")
    print("  /system <name>     - Set interpretation system")
    print("                       (rws_traditional, thoth_crowley,")
    print("                        jungian_psychological, modern_intuitive,")
    print("                        combined)")
    print("  /top <n>           - Set number of results (default 5)")
    print("  /art on|off        - Toggle ASCII art (default off)")
    print("  /include-same-card on|off")
    print("                     - Include same card in opposite position in")
    print("                       similar results (default off)")
    print("  quit/exit          - Exit interactive mode")
    print()

    while True:
        try:
            query = input("🔮 > ").strip()

            if not query:
                continue

            lower = query.lower()

            if lower in ['quit', 'exit', 'q', '/quit', '/exit', '/q']:
                print("\nGoodbye! ✨")
                break

            # /system <name>
            if lower == '/system' or lower.startswith('/system '):
                parts = query.split(None, 1)
                if len(parts) < 2 or not parts[1].strip():
                    print(f"Current system: {current_system}")
                    print("Usage: /system <name>. Choices: " + ", ".join(VALID_SYSTEMS))
                    continue
                requested = parts[1].strip()
                if requested not in VALID_SYSTEMS:
                    print(f"Error: unknown system: {requested}")
                    print("Choices: " + ", ".join(VALID_SYSTEMS))
                    continue
                current_system = requested
                print(f"System set to: {current_system}")
                continue

            # /top <n>
            if lower == '/top' or lower.startswith('/top '):
                parts = query.split(None, 1)
                if len(parts) < 2:
                    print(f"Current top: {current_top_k}")
                    print("Usage: /top <n>")
                    continue
                try:
                    n = int(parts[1].strip())
                    if n < 0:
                        raise ValueError
                except ValueError:
                    print(f"Error: /top expects a non-negative integer, got: {parts[1]!r}")
                    continue
                current_top_k = n
                print(f"Top set to: {current_top_k}")
                continue

            # /art on|off
            if lower == '/art' or lower.startswith('/art '):
                parts = query.split(None, 1)
                if len(parts) < 2:
                    current_show_art = not current_show_art
                else:
                    arg = parts[1].strip().lower()
                    if arg in ('on', 'true', '1', 'yes'):
                        current_show_art = True
                    elif arg in ('off', 'false', '0', 'no'):
                        current_show_art = False
                    else:
                        print(f"Error: /art expects on or off, got: {arg!r}")
                        continue
                print(f"Art display: {'on' if current_show_art else 'off'}")
                continue

            # /include-same-card on|off (interactive parity with --include-same-card)
            if lower == '/include-same-card' or lower.startswith('/include-same-card '):
                parts = query.split(None, 1)
                if len(parts) < 2:
                    current_include_same_card = not current_include_same_card
                else:
                    arg = parts[1].strip().lower()
                    if arg in ('on', 'true', '1', 'yes'):
                        current_include_same_card = True
                    elif arg in ('off', 'false', '0', 'no'):
                        current_include_same_card = False
                    else:
                        print(f"Error: /include-same-card expects on or off, got: {arg!r}")
                        continue
                print(f"Include same card: {'on' if current_include_same_card else 'off'}")
                continue

            # similar <card> or /similar <card>
            if lower == 'similar' or lower == '/similar' or \
                    lower.startswith('similar ') or lower.startswith('/similar '):
                # Strip the verb and any trailing whitespace.
                if lower.startswith('/'):
                    rest = query[len('/similar'):].strip()
                else:
                    rest = query[len('similar'):].strip()
                if not rest:
                    print("Error: similar requires a card name. Usage: similar <card name>")
                    continue
                canonical = resolve_card_name(rest, cards)
                if canonical is None:
                    print(f"Error: Card not found: {rest}")
                    continue
                pos_input = input("Position (u/r, default: u): ")
                position = parse_position(pos_input)
                try:
                    results = find_similar_cards(
                        canonical, position, embeddings_data,
                        top_k=current_top_k, system_filter=current_system,
                        exclude_same_card=not current_include_same_card,
                    )
                    print(format_results(results, cards, interpretations,
                                         show_ascii=current_show_art,
                                         system=current_system))
                except ValueError as e:
                    print(f"Error: {e}")
                continue

            # Semantic search
            results = search_cards(
                query, embeddings_data, model,
                top_k=current_top_k, system_filter=current_system,
            )
            print(format_results(results, cards, interpretations,
                                 show_ascii=current_show_art,
                                 system=current_system))

        except KeyboardInterrupt:
            print("\n\nGoodbye! ✨")
            break
        except Exception as e:
            print(f"Error: {e}")


def _non_negative_int(value):
    """argparse type that rejects negative integers (used for --top)."""
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(f"invalid int value: {value!r}")
    if ivalue < 0:
        raise argparse.ArgumentTypeError(
            f"--top must be non-negative, got {ivalue}"
        )
    return ivalue


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
    parser.add_argument(
        '--include-same-card',
        action='store_true',
        help='Include same card in opposite position in similar results',
    )
    parser.add_argument('--top', type=_non_negative_int, default=5, help='Number of results to return (default: 5)')
    parser.add_argument('--ascii', '--art', action='store_true', dest='show_art', help='Show ASCII art for cards')
    # --json and --yaml are mutually exclusive: passing both used to silently
    # prefer JSON, which masked wrapper-script bugs.
    output_format_group = parser.add_mutually_exclusive_group()
    output_format_group.add_argument('--json', action='store_true', help='Output results as JSON')
    output_format_group.add_argument('--yaml', action='store_true', help='Output results as YAML')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive search mode')
    parser.add_argument(
        '--model',
        choices=['v1.5', 'v2-moe', 'openai'],
        default='v1.5',
        help='Embedding model to use (default: v1.5)'
    )
    parser.add_argument(
        '--system',
        choices=['rws_traditional', 'thoth_crowley', 'jungian_psychological',
                 'modern_intuitive', 'combined'],
        default='combined',
        metavar='SYSTEM',
        help='Filter by interpretation system: rws_traditional, thoth_crowley, jungian_psychological, modern_intuitive, combined (default: combined)'
    )

    args = parser.parse_args()

    # Get full model name
    model = MODEL_MAP[args.model]

    # Auto-detect embeddings file based on model (anchored to script dir)
    model_suffix = args.model.replace('-', '_').replace('.', '_')
    embeddings_file = os.path.join(HERE, f'card_embeddings_{model_suffix}.json')

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
        interactive_mode(embeddings_data, cards, interpretations, model,
                         system=args.system)
        return

    # Similar card search
    if args.similar:
        position = 'reversed' if args.reversed else 'upright'
        canonical = resolve_card_name(args.similar, cards)
        if canonical is None:
            print(f"Error: Card not found: {args.similar}", file=sys.stderr)
            sys.exit(1)
        try:
            results = find_similar_cards(
                canonical, position, embeddings_data,
                top_k=args.top, system_filter=args.system,
                exclude_same_card=not args.include_same_card,
            )
            print(format_results(results, cards, interpretations, args.show_art,
                                 format_type, system=args.system))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Semantic search
    if not args.query:
        parser.print_help()
        sys.exit(1)

    results = search_cards(
        args.query, embeddings_data, model,
        top_k=args.top, system_filter=args.system,
    )
    print(format_results(results, cards, interpretations, args.show_art,
                         format_type, system=args.system))


if __name__ == '__main__':
    main()
