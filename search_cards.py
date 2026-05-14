#!/usr/bin/env python3
"""
Search tarot cards using vector embeddings.
Provides semantic search capabilities for finding related cards.

Usage:
    # Semantic search
    python3 search_cards.py "new beginnings"

    # Find similar cards
    python3 search_cards.py --similar "The Fool"
    python3 search_cards.py --similar "The Fool" --reversed

    # Display with ASCII art
    python3 search_cards.py "new beginnings" --ascii
    python3 search_cards.py --similar "The Fool" --art --top 3

    # JSON/YAML output
    python3 search_cards.py "transformation" --json
    python3 search_cards.py --similar "The Star" --yaml

    # Interactive mode
    python3 search_cards.py --interactive
"""

import json
import os
import sys
import argparse
import numpy as np
from typing import List, Dict, Tuple, Optional
from openai import OpenAI

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Configuration -- anchor data file paths to this script so the CLI works
# from any working directory, not just the repo root.
HERE = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_FILE = os.path.join(HERE, 'card_embeddings.json')
CARDS_FILE = os.path.join(HERE, 'cards.json')
INTERPRETATIONS_FILE = os.path.join(HERE, 'interpretations.json')


def load_embeddings() -> List[Dict]:
    """Load pre-generated embeddings from file"""
    if not os.path.exists(EMBEDDINGS_FILE):
        raise FileNotFoundError(
            f"Embeddings file not found: {EMBEDDINGS_FILE}\n"
            "Please run generate_embeddings.py first to create embeddings."
        )

    with open(EMBEDDINGS_FILE, 'r') as f:
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


def get_query_embedding(client: OpenAI, query: str) -> List[float]:
    """
    Generate embedding for a search query.

    Args:
        client: OpenAI client instance
        query: Search query text

    Returns:
        Embedding vector
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding


def search_cards(
    query: str,
    embeddings_data: List[Dict],
    client: OpenAI,
    top_k: int = 5,
    position_filter: str = None,
    system_filter: str = None
) -> List[Tuple[str, str, float]]:
    """
    Search for cards semantically similar to a query.

    Args:
        query: Search query (e.g., "new beginnings", "letting go")
        embeddings_data: List of card embeddings
        client: OpenAI client
        top_k: Number of results to return
        position_filter: Filter by 'upright' or 'reversed' (None for both)
        system_filter: Filter by interpretation system (None for combined/all)

    Returns:
        List of (card_name, position, similarity_score) tuples
    """
    if top_k < 0:
        raise ValueError(f"top_k must be non-negative, got {top_k}")

    # Get query embedding
    query_embedding = get_query_embedding(client, query)

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


def find_similar_cards(
    card_name: str,
    position: str,
    embeddings_data: List[Dict],
    top_k: int = 5,
    exclude_self: bool = True,
    exclude_same_card: bool = True,
    system_filter: str = None
) -> List[Tuple[str, str, float]]:
    """
    Find cards similar to a given card.

    Args:
        card_name: Name of the card to find similar cards for
        position: Position of the card ('upright' or 'reversed')
        embeddings_data: List of card embeddings
        top_k: Number of results to return
        exclude_self: Whether to exclude the exact same card and position
        exclude_same_card: Whether to exclude the same card in both positions (default True)
        system_filter: Filter by interpretation system (None for combined/all)

    Returns:
        List of (card_name, position, similarity_score) tuples
    """
    if top_k < 0:
        raise ValueError(f"top_k must be non-negative, got {top_k}")

    # Determine which system to use (default to 'combined' if not specified)
    target_system = system_filter if system_filter else 'combined'

    # Find the target card's embedding for the specified system
    target_embedding = None
    for card_data in embeddings_data:
        if (card_data['card_name'] == card_name and
            card_data['position'] == position and
            card_data.get('interpretation_system', 'combined') == target_system):
            target_embedding = card_data['embedding']
            break

    if target_embedding is None:
        raise ValueError(f"Card not found: {card_name} ({position}) for system {target_system}")

    # Calculate similarities
    similarities = []
    for card_data in embeddings_data:
        # Apply system filter
        if card_data.get('interpretation_system', 'combined') != target_system:
            continue

        # Exclude same card (both positions) if requested
        if exclude_same_card and card_data['card_name'] == card_name:
            continue

        # Exclude exact match if requested (when exclude_same_card is False)
        if not exclude_same_card and exclude_self and (
            card_data['card_name'] == card_name and
            card_data['position'] == position
        ):
            continue

        similarity = cosine_similarity(target_embedding, card_data['embedding'])
        similarities.append((
            card_data['card_name'],
            card_data['position'],
            similarity
        ))

    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[2], reverse=True)

    return similarities[:top_k]


def format_results_as_data(
    results: List[Tuple[str, str, float]],
    cards_data: List[Dict],
    system: str = 'combined',
    interpretations_data: Dict = None
) -> List[Dict]:
    """
    Format search results as structured data (for JSON/YAML output).

    Args:
        results: List of (card_name, position, similarity_score) tuples
        cards_data: Card data for additional info
        system: Interpretation system used for search
        interpretations_data: Interpretation data for system-specific meanings

    Returns:
        List of dictionaries with card information
    """
    # Create card lookup
    card_lookup = {card['name']: card for card in cards_data}

    formatted_results = []
    for card_name, position, score in results:
        card = card_lookup.get(card_name)
        if not card:
            continue

        # Get meaning based on system
        if system != 'combined' and interpretations_data and card_name in interpretations_data:
            # Use system-specific interpretation
            card_interp = interpretations_data[card_name]
            if system in card_interp and position in card_interp[system]:
                meaning = card_interp[system][position]
            else:
                # Fallback to basic meaning if system interpretation not found
                meaning = card['desc'] if position == 'upright' else card['rdesc']
        else:
            # Use basic meaning for combined system
            meaning = card['desc'] if position == 'upright' else card['rdesc']

        result_entry = {
            'card_name': card_name,
            'position': position,
            'similarity': float(score),
            'meaning': meaning
        }
        formatted_results.append(result_entry)

    return formatted_results


def display_search_results(
    results: List[Tuple[str, str, float]],
    cards_data: List[Dict],
    output_format: Optional[str] = None,
    system: str = 'combined',
    interpretations_data: Dict = None,
    show_art: bool = False
):
    """
    Display search results in the specified format.

    Args:
        results: List of (card_name, position, similarity_score) tuples
        cards_data: Card data for additional info
        output_format: Output format ('json', 'yaml', or None for human-readable)
        system: Interpretation system used for search
        interpretations_data: Interpretation data for system-specific meanings
        show_art: Whether to display ASCII art for cards (default: False)
    """
    # Handle structured output formats
    if output_format in ['json', 'yaml']:
        formatted_data = format_results_as_data(results, cards_data, system, interpretations_data)

        if output_format == 'json':
            print(json.dumps(formatted_data, indent=2))
        elif output_format == 'yaml':
            if not YAML_AVAILABLE:
                print("Error: pyyaml not installed. Install with: pip install pyyaml", file=sys.stderr)
                sys.exit(1)
            print(yaml.dump(formatted_data, default_flow_style=False, sort_keys=False))
        return

    # Human-readable format (default)
    # Create card lookup
    card_lookup = {card['name']: card for card in cards_data}

    print("\n" + "=" * 70)
    print("SEARCH RESULTS")
    print("=" * 70)

    for i, (card_name, position, score) in enumerate(results, 1):
        card = card_lookup.get(card_name)
        if not card:
            continue

        print(f"\n{i}. {card_name} ({position.upper()})")
        print(f"   Similarity: {score:.4f}")

        # Get meaning based on system
        if system != 'combined' and interpretations_data and card_name in interpretations_data:
            # Use system-specific interpretation
            card_interp = interpretations_data[card_name]
            if system in card_interp and position in card_interp[system]:
                meaning = card_interp[system][position]
            else:
                # Fallback to basic meaning
                meaning = card['desc'] if position == 'upright' else card['rdesc']
        else:
            # Use basic meaning for combined system
            meaning = card['desc'] if position == 'upright' else card['rdesc']

        # Show brief meaning
        if show_art or len(meaning) <= 100:
            # Full meaning when showing art, or when it fits
            print(f"   Meaning: {meaning}")
        else:
            # Truncated meaning when not showing art
            print(f"   Meaning: {meaning[:100]}...")

        # Show ASCII art if requested
        if show_art and card:
            print()
            if position == 'reversed' and 'reversed' in card:
                print(card['reversed'])
            else:
                if position == 'reversed':
                    # Avoid silently showing upright art under a REVERSED label.
                    print("(no reversed art for this card; showing upright)")
                print(card['card'])
            print()


VALID_SYSTEMS = (
    'rws_traditional', 'thoth_crowley', 'jungian_psychological',
    'modern_intuitive', 'combined',
)


def interactive_search():
    """Interactive search interface.

    The OpenAI client is built lazily: only semantic queries hit the
    API, so `/similar` works without OPENAI_API_KEY (it uses local
    pre-generated embeddings). A semantic query without a key prints
    an error and returns to the prompt instead of exiting the loop.
    """
    client = None  # built on first semantic query that needs it

    # Load data
    print("Loading embeddings and card data...")
    try:
        embeddings_data = load_embeddings()
        cards_data = load_cards()
        interpretations_data = load_interpretations()
        print(f"✓ Loaded {len(embeddings_data)} embeddings for {len(cards_data)} cards")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Session state -- can be changed via /system, /top, /art,
    # /include-same-card commands.
    current_system = 'combined'
    current_top_k = 5
    current_show_art = False
    current_include_same_card = False

    print("\n" + "=" * 70)
    print("TAROT CARD SEMANTIC SEARCH")
    print("=" * 70)
    print("\nSearch for cards by theme, concept, or feeling.")
    print("Examples: 'new beginnings', 'letting go', 'inner strength', 'confusion'")
    print("\nCommands:")
    print("  /similar <card name>  - Find cards similar to a specific card")
    print("  /system <name>        - Set interpretation system (rws_traditional,")
    print("                          thoth_crowley, jungian_psychological,")
    print("                          modern_intuitive, combined)")
    print("  /top <n>              - Set number of results to return (default 5)")
    print("  /art on|off           - Toggle ASCII art display (default off)")
    print("  /include-same-card on|off")
    print("                        - Include same card in opposite position in")
    print("                          /similar results (default off)")
    print("  /quit                 - Exit")
    print("=" * 70)

    while True:
        print()
        query = input("Search query: ").strip()

        if not query:
            continue

        lower = query.lower()

        if lower in ['quit', 'exit', 'q', '/quit', '/exit', '/q']:
            print("\nGoodbye!")
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
                print(f"✗ Unknown system: {requested}")
                print("Choices: " + ", ".join(VALID_SYSTEMS))
                continue
            current_system = requested
            print(f"✓ System set to: {current_system}")
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
                print(f"✗ /top expects a non-negative integer, got: {parts[1]!r}")
                continue
            current_top_k = n
            print(f"✓ Top set to: {current_top_k}")
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
                    print(f"✗ /art expects on or off, got: {arg!r}")
                    continue
            print(f"✓ Art display: {'on' if current_show_art else 'off'}")
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
                    print(f"✗ /include-same-card expects on or off, got: {arg!r}")
                    continue
            print(f"✓ Include same card: {'on' if current_include_same_card else 'off'}")
            continue

        # /similar <card>
        if lower == '/similar' or lower.startswith('/similar '):
            parts = query.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                print("✗ /similar requires a card name. Usage: /similar <card name>")
                continue
            card_name = parts[1].strip()

            # Find the card
            card = None
            for c in cards_data:
                if c['name'].lower() == card_name.lower():
                    card = c
                    break

            if not card:
                print(f"✗ Card not found: {card_name}")
                continue

            # Ask for position
            pos_input = input("Position (u/r, default: u): ")
            position = parse_position(pos_input)

            print(f"\nFinding cards similar to '{card['name']}' ({position})...")

            try:
                results = find_similar_cards(
                    card['name'],
                    position,
                    embeddings_data,
                    top_k=current_top_k,
                    system_filter=current_system,
                    exclude_same_card=not current_include_same_card,
                )
                display_search_results(results, cards_data,
                                       system=current_system,
                                       interpretations_data=interpretations_data,
                                       show_art=current_show_art)
            except ValueError as e:
                print(f"✗ Error: {e}")
            continue

        # Normal semantic search -- requires the OpenAI API.
        if client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print(
                    "Error: OPENAI_API_KEY environment variable not set"
                )
                print(
                    "Set it with: export OPENAI_API_KEY='your-key-here'"
                )
                print(
                    "(/similar still works without a key; it uses local embeddings.)"
                )
                continue
            client = OpenAI(api_key=api_key)

        print(f"\nSearching for: '{query}'...")

        try:
            results = search_cards(
                query,
                embeddings_data,
                client,
                top_k=current_top_k,
                system_filter=current_system,
            )
            display_search_results(results, cards_data,
                                   system=current_system,
                                   interpretations_data=interpretations_data,
                                   show_art=current_show_art)
        except Exception as e:
            print(f"✗ Error: {e}")


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
    """Main execution with CLI argument support"""
    parser = argparse.ArgumentParser(
        description='Search tarot cards using vector embeddings',
        epilog='Examples:\n'
               '  %(prog)s "new beginnings"\n'
               '  %(prog)s --similar "The Fool"\n'
               '  %(prog)s --similar "The Tower" --reversed\n'
               '  %(prog)s "transformation" --ascii --top 3\n'
               '  %(prog)s "transformation" --json\n'
               '  %(prog)s --similar "The Star" --yaml\n'
               '  %(prog)s --interactive',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='Search query for semantic search (e.g., "new beginnings", "letting go")'
    )
    parser.add_argument(
        '--similar', '-s',
        metavar='CARD',
        help='Find cards similar to the specified card'
    )
    parser.add_argument(
        '--reversed', '-r',
        action='store_true',
        help='Use reversed position (for --similar mode)'
    )
    parser.add_argument(
        '--include-same-card',
        action='store_true',
        help='Include same card in opposite position in similar results'
    )
    parser.add_argument(
        '--top', '-k',
        type=_non_negative_int,
        default=5,
        metavar='N',
        help='Number of results to return (default: 5)'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Launch interactive search mode'
    )
    # --json and --yaml are mutually exclusive: passing both used to silently
    # prefer JSON, which masked wrapper-script bugs.
    output_format_group = parser.add_mutually_exclusive_group()
    output_format_group.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    output_format_group.add_argument(
        '--yaml',
        action='store_true',
        help='Output results in YAML format'
    )
    parser.add_argument(
        '--system',
        choices=['rws_traditional', 'thoth_crowley', 'jungian_psychological', 'modern_intuitive', 'combined'],
        default='combined',
        metavar='SYSTEM',
        help='Filter by interpretation system: rws_traditional, thoth_crowley, jungian_psychological, modern_intuitive, combined (default: combined)'
    )
    parser.add_argument(
        '--ascii', '--art',
        action='store_true',
        dest='show_art',
        help='Display ASCII art for each card in results'
    )

    args = parser.parse_args()

    # Determine output format
    output_format = None
    if args.json:
        output_format = 'json'
    elif args.yaml:
        output_format = 'yaml'

    # If no arguments or interactive flag, run interactive mode
    if args.interactive or (not args.query and not args.similar):
        interactive_search()
        return

    # Load data (purely local; no API key needed)
    try:
        embeddings_data = load_embeddings()
        cards_data = load_cards()
        interpretations_data = load_interpretations()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Handle --similar mode
    if args.similar:
        # Normalize user input: strip surrounding whitespace before the
        # case-insensitive lookup so `--similar "  The Fool  "` resolves.
        similar_query = args.similar.strip()

        # Find the card
        card = None
        for c in cards_data:
            if c['name'].lower() == similar_query.lower():
                card = c
                break

        if not card:
            print(f"✗ Card not found: {similar_query}")
            print("\nAvailable cards:")
            for c in cards_data[:10]:  # Show first 10 as examples
                print(f"  - {c['name']}")
            print("  ...")
            sys.exit(1)

        position = 'reversed' if args.reversed else 'upright'

        # Only show status message in human-readable mode
        if not output_format:
            print(f"Finding cards similar to '{card['name']}' ({position})...")

        try:
            results = find_similar_cards(
                card['name'],
                position,
                embeddings_data,
                top_k=args.top,
                exclude_same_card=not args.include_same_card,
                system_filter=args.system
            )
            display_search_results(results, cards_data, output_format, args.system, interpretations_data, args.show_art)
        except ValueError as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Handle semantic search mode
    elif args.query:
        # Semantic search requires an OpenAI client to embed the query.
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: OPENAI_API_KEY environment variable not set")
            print("Please set it with: export OPENAI_API_KEY='your-key-here'")
            sys.exit(1)
        client = OpenAI(api_key=api_key)

        # Only show status message in human-readable mode
        if not output_format:
            print(f"Searching for: '{args.query}'...")

        try:
            results = search_cards(
                args.query,
                embeddings_data,
                client,
                top_k=args.top,
                system_filter=args.system
            )
            display_search_results(results, cards_data, output_format, args.system, interpretations_data, args.show_art)
        except Exception as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
