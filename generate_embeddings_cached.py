#!/usr/bin/env python3
"""
Generate vector embeddings for tarot cards using embedding-cache.
This version uses local caching to eliminate API costs and enable offline operation.

CHANGES FROM ORIGINAL:
- Uses embedding-cache instead of OpenAI API
- Local nomic-embed-text-v1.5 model (768 dimensions vs OpenAI's 1536)
- Caches all embeddings automatically
- Works offline once model is downloaded
- Zero API costs

Usage:
    python3 generate_embeddings_cached.py
"""

import json
import os
from typing import List, Dict

# Import our new embedding cache!
from embedding_cache import embed

# Configuration -- anchor data file paths to this script so it works from
# any working directory, not just the repo root.
HERE = os.path.dirname(os.path.abspath(__file__))
CARDS_FILE = os.path.join(HERE, 'cards.json')
INTERPRETATIONS_FILE = os.path.join(HERE, 'interpretations.json')

# Model name mappings
MODEL_MAP = {
    'v1.5': 'nomic-ai/nomic-embed-text-v1.5',
    'v2-moe': 'nomic-ai/nomic-embed-text-v2-moe',
    'openai': 'openai:text-embedding-3-small'
}

def load_data():
    """Load cards and interpretations data"""
    with open(CARDS_FILE, 'r') as f:
        cards = json.load(f)

    with open(INTERPRETATIONS_FILE, 'r') as f:
        interpretations = json.load(f)

    return cards, interpretations

def create_card_text_for_system(
    card: Dict,
    interpretations: Dict,
    position: str = 'upright',
    system: str = None
) -> str:
    """
    Create text representation of a card for a specific interpretation system.

    Args:
        card: Card data from cards.json
        interpretations: Interpretation data from interpretations.json
        position: 'upright' or 'reversed'
        system: Interpretation system key (or None for combined)

    Returns:
        Text for embedding
    """
    card_name = card['name']

    # Start with card name
    parts = [f"Card: {card_name}"]
    parts.append(f"Position: {position}")

    # Add basic meanings from cards.json
    if position == 'upright':
        if 'desc' in card and card['desc']:
            parts.append(f"Basic meaning: {card['desc']}")
    else:
        if 'rdesc' in card and card['rdesc']:
            parts.append(f"Basic meaning: {card['rdesc']}")

    # Add interpretation from specific system or all systems
    if card_name in interpretations:
        card_interp = interpretations[card_name]

        if system:
            # Single system
            if system in card_interp:
                interp_text = card_interp[system].get(position, '')
                if interp_text:
                    parts.append(f"Interpretation: {interp_text}")
        else:
            # All systems (combined)
            if 'rws_traditional' in card_interp:
                rws = card_interp['rws_traditional'].get(position, '')
                if rws:
                    parts.append(f"Traditional interpretation: {rws}")

            if 'thoth_crowley' in card_interp:
                thoth = card_interp['thoth_crowley'].get(position, '')
                if thoth:
                    parts.append(f"Crowley/Thoth interpretation: {thoth}")

            if 'jungian_psychological' in card_interp:
                jungian = card_interp['jungian_psychological'].get(position, '')
                if jungian:
                    parts.append(f"Jungian/psychological interpretation: {jungian}")

            if 'modern_intuitive' in card_interp:
                modern = card_interp['modern_intuitive'].get(position, '')
                if modern:
                    parts.append(f"Modern/intuitive interpretation: {modern}")

    return "\n".join(parts)


def create_card_text(card: Dict, interpretations: Dict, position: str = 'upright') -> str:
    """
    Create comprehensive text representation of a card for embedding (all systems).

    Args:
        card: Card data from cards.json
        interpretations: Interpretation data from interpretations.json
        position: 'upright' or 'reversed'

    Returns:
        Combined text for embedding
    """
    return create_card_text_for_system(card, interpretations, position, system=None)

# Interpretation systems
INTERPRETATION_SYSTEMS = {
    'rws_traditional': 'Rider-Waite-Smith (Traditional)',
    'thoth_crowley': 'Thoth/Crowley (Esoteric)',
    'jungian_psychological': 'Jungian/Psychological (Archetypes)',
    'modern_intuitive': 'Modern/Intuitive (Contemporary)',
    'combined': 'All Systems Combined'
}


def generate_embeddings(cards: List[Dict], interpretations: Dict, model: str) -> List[Dict]:
    """
    Generate embeddings for all cards (both upright and reversed) for each interpretation system.

    This version uses embedding-cache which:
    - Computes embeddings locally (no API cost)
    - Caches results automatically
    - Works offline once model is downloaded

    Returns:
        List of embedding records with metadata
    """
    embeddings_data = []

    # Systems to generate embeddings for (individual systems + combined)
    systems = ['rws_traditional', 'thoth_crowley', 'jungian_psychological', 'modern_intuitive', 'combined']

    # Collect all texts first for batch processing
    texts_to_embed = []
    metadata = []

    for card in cards:
        card_name = card['name']
        print(f"Preparing: {card_name}")

        for position in ['upright', 'reversed']:
            for system in systems:
                # Determine system key (None for combined)
                system_key = None if system == 'combined' else system

                # Create text for this specific system
                text = create_card_text_for_system(card, interpretations, position, system_key)

                texts_to_embed.append(text)
                metadata.append({
                    'card_name': card_name,
                    'position': position,
                    'interpretation_system': system,
                    'text': text
                })

    # Batch embed all texts at once - embedding-cache will handle caching!
    print(f"\nGenerating {len(texts_to_embed)} embeddings using local model + cache...")
    print("(First run may take a few minutes to download model)")
    print("(Subsequent runs will be instant due to caching!)\n")

    try:
        # This single call handles everything: normalization, caching, local computation
        from embedding_cache import EmbeddingCache
        cache = EmbeddingCache(model=model)
        embeddings = cache.embed(texts_to_embed)

        # Combine embeddings with metadata
        for i, embedding in enumerate(embeddings):
            meta = metadata[i]
            card_name = meta['card_name']
            position = meta['position']
            system = meta['interpretation_system']
            system_label = INTERPRETATION_SYSTEMS[system]

            print(f"  ✓ {card_name} [{position}] - {system_label}")

            embeddings_data.append({
                'card_name': card_name,
                'position': position,
                'interpretation_system': system,
                'text': meta['text'],
                'embedding': embedding.tolist()  # Convert numpy array to list for JSON
            })

    except Exception as e:
        print(f"  ✗ Error generating embeddings: {e}")
        raise

    return embeddings_data

def save_embeddings(embeddings_data: List[Dict], output_file: str):
    """Save embeddings to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(embeddings_data, f, indent=2)

    print(f"\n✓ Saved {len(embeddings_data)} embeddings to {output_file}")

    # Calculate file size
    file_size = os.path.getsize(output_file)
    size_mb = file_size / (1024 * 1024)
    print(f"  File size: {size_mb:.1f} MB")

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate vector embeddings for tarot cards using embedding-cache'
    )
    parser.add_argument(
        '--model',
        choices=['v1.5', 'v2-moe', 'openai'],
        default='v1.5',
        help='Embedding model to use (default: v1.5)'
    )

    args = parser.parse_args()

    # Get full model name
    model = MODEL_MAP[args.model]

    # Determine output file based on model (anchored to script dir)
    model_suffix = args.model.replace('-', '_').replace('.', '_')
    output_file = os.path.join(HERE, f'card_embeddings_{model_suffix}.json')

    print("=" * 70)
    print("Tarot Card Embedding Generator (with embedding-cache)")
    print(f"Using {model} with automatic caching")
    print("=" * 70)
    print()
    print("Benefits of embedding-cache:")
    print("  ✓ Zero API costs (local computation)")
    print("  ✓ Automatic caching (instant regeneration)")
    print("  ✓ Works offline (no internet needed after first run)")
    print("  ✓ Thread-safe caching")
    print()

    # Load data
    print("Loading card data...")
    cards, interpretations = load_data()
    print(f"✓ Loaded {len(cards)} cards")
    print()

    # Generate embeddings
    print("Generating embeddings...")
    print(f"(Creating {len(cards) * 2 * 5} embeddings: {len(cards)} cards × 2 positions × 5 systems)")
    print("Systems: Traditional, Crowley, Jungian, Modern, Combined")
    print()
    embeddings_data = generate_embeddings(cards, interpretations, model)

    # Save results
    save_embeddings(embeddings_data, output_file)

    print()
    print("=" * 70)
    print("Done!")
    print("=" * 70)
    print()
    print(f"NOTE: Output saved to {output_file}")
    print("      Run again to see instant caching in action.")

if __name__ == "__main__":
    main()
