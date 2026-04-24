import json
import random
import os
from datetime import datetime
from typing import List, Dict, Optional

# Load JSON files
with open('cards.json') as file:
    tarot_deck = json.load(file)

# Load interpretation systems
try:
    with open('interpretations.json') as file:
        interpretations_db = json.load(file)
except FileNotFoundError:
    interpretations_db = {}

HISTORY_FILE = 'reading_history.json'
DAILY_CARD_FILE = 'daily_card.json'

# Interpretation systems available
INTERPRETATION_SYSTEMS = {
    'rws_traditional': 'Rider-Waite-Smith (Traditional)',
    'thoth_crowley': 'Thoth/Crowley (Esoteric)',
    'jungian_psychological': 'Jungian/Psychological (Archetypes)',
    'modern_intuitive': 'Modern/Intuitive (Contemporary)'
}

# Current interpretation mode (can be changed by user)
current_interpretation_mode = 'rws_traditional'

# Major Arcana cards (0-21)
MAJOR_ARCANA = [
    "The Fool", "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot",
    "Strength", "The Hermit", "Wheel of Fortune", "Justice",
    "The Hanged Man", "Death", "Temperance", "The Devil",
    "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"
]

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def get_interpretation(card_name: str, is_reversed: bool = False, mode: str = None) -> str:
    """Get interpretation for a card based on the current interpretation mode"""
    if mode is None:
        mode = current_interpretation_mode

    if card_name not in interpretations_db:
        return None

    card_interp = interpretations_db[card_name]
    if mode not in card_interp:
        return None

    position = 'reversed' if is_reversed else 'upright'
    return card_interp[mode].get(position, '')

def display_card(card: Dict, is_reversed: bool = False, show_all_interpretations: bool = False):
    """Display a card with its information"""
    global current_interpretation_mode

    print(f"\n{'═' * 50}")
    print(f"Card: {card['name']}")
    if is_reversed:
        print("Position: REVERSED")
        print(f"Meaning: {card['rdesc']}")
        print(f"\n{card.get('reversed', card['card'])}")
    else:
        print("Position: Upright")
        print(f"Meaning: {card['desc']}")
        print(f"\n{card['card']}")

    # Show interpretations from different systems
    if card['name'] in interpretations_db:
        if show_all_interpretations:
            print(f"\n{'─' * 50}")
            print("MULTIPLE PERSPECTIVES:")
            print(f"{'─' * 50}")
            for mode_key, mode_name in INTERPRETATION_SYSTEMS.items():
                interp = get_interpretation(card['name'], is_reversed, mode_key)
                if interp:
                    print(f"\n• {mode_name}:")
                    print(f"  {interp}")
        else:
            # Show current interpretation mode
            interp = get_interpretation(card['name'], is_reversed, current_interpretation_mode)
            if interp:
                print(f"\n{'─' * 50}")
                print(f"{INTERPRETATION_SYSTEMS[current_interpretation_mode]}:")
                print(f"{interp}")

    print(f"{'═' * 50}\n")

def search_card(card_name: str):
    """Search for a card by name.

    Surrounding whitespace is stripped before the case-insensitive
    lookup so callers don't have to remember to sanitize input. This
    matches `compare_interpretations` and `search_cards.py --similar`.
    """
    needle = card_name.strip()
    for card in tarot_deck:
        if card['name'].lower() == needle.lower():
            display_card(card)
            return card
    print(f"Card not found: {needle}")
    return None

def search_by_keyword(keyword: str):
    """Search for cards by keyword in their descriptions.

    Matches the keyword (case-insensitive) against the card name, the
    brief meanings in cards.json, and every interpretation-system entry
    in interpretations.json (upright and reversed). A card matched in
    multiple systems appears once.
    """
    keyword_lower = keyword.strip().lower()
    if not keyword_lower:
        print("Please enter a keyword to search.")
        return []

    matching_cards = []

    for card in tarot_deck:
        if (keyword_lower in card['name'].lower() or
            keyword_lower in card['desc'].lower() or
            keyword_lower in card['rdesc'].lower()):
            matching_cards.append(card)
            continue

        card_interp = interpretations_db.get(card['name'])
        if not card_interp:
            continue
        for system_data in card_interp.values():
            if not isinstance(system_data, dict):
                continue
            if any(
                isinstance(text, str) and keyword_lower in text.lower()
                for text in system_data.values()
            ):
                matching_cards.append(card)
                break

    if matching_cards:
        print(f"\nFound {len(matching_cards)} card(s) matching '{keyword}':\n")
        for card in matching_cards:
            print(f"- {card['name']}")
        print()
        return matching_cards
    else:
        print(f"No cards found matching '{keyword}'.")
        return []

def draw_card(allow_reversed: bool = True) -> tuple:
    """Draw a random card, optionally reversed"""
    card = random.choice(tarot_deck)
    is_reversed = random.choice([True, False]) if allow_reversed else False
    return card, is_reversed

def draw_unique_cards(n: int, allow_reversed: bool = True) -> List[tuple]:
    """Deal n distinct cards from the deck, optionally with reversals.

    Models a physical shuffle: each card appears at most once per spread.
    """
    if n > len(tarot_deck):
        raise ValueError(
            f"Cannot draw {n} unique cards from a deck of {len(tarot_deck)}"
        )
    sampled = random.sample(tarot_deck, n)
    return [
        (card, random.choice([True, False]) if allow_reversed else False)
        for card in sampled
    ]

def single_card_reading():
    """Draw a single card"""
    print("\n" + "═" * 50)
    print("SINGLE CARD READING")
    print("═" * 50)
    card, is_reversed = draw_card()
    display_card(card, is_reversed)
    return {"spread": "single", "cards": [(card['name'], is_reversed)]}

def three_card_reading():
    """Three-card tarot reading (Past, Present, Future)"""
    print("\n" + "═" * 50)
    print("THREE CARD READING: Past, Present, Future")
    print("═" * 50)

    positions = ["PAST", "PRESENT", "FUTURE"]
    dealt = draw_unique_cards(len(positions))
    cards_drawn = []

    for position, (card, is_reversed) in zip(positions, dealt):
        print(f"\n{position}:")
        display_card(card, is_reversed)
        cards_drawn.append((card['name'], is_reversed))

        if position != "FUTURE":
            input("Press Enter to continue...")

    return {"spread": "three_card", "cards": cards_drawn}

def celtic_cross_reading():
    """Celtic Cross spread - 10 cards"""
    print("\n" + "═" * 50)
    print("CELTIC CROSS READING")
    print("═" * 50)

    positions = [
        "1. Present/Heart of the Matter",
        "2. Challenge/Crossing",
        "3. Distant Past/Foundation",
        "4. Recent Past",
        "5. Crown/Best Outcome",
        "6. Near Future",
        "7. Your Attitude",
        "8. External Influences",
        "9. Hopes and Fears",
        "10. Final Outcome"
    ]

    dealt = draw_unique_cards(len(positions))
    cards_drawn = []

    for position, (card, is_reversed) in zip(positions, dealt):
        print(f"\n{position}:")
        display_card(card, is_reversed)
        cards_drawn.append((card['name'], is_reversed))

        if position != positions[-1]:
            input("Press Enter for next card...")

    return {"spread": "celtic_cross", "cards": cards_drawn}

def horseshoe_reading():
    """Horseshoe spread - 7 cards"""
    print("\n" + "═" * 50)
    print("HORSESHOE READING")
    print("═" * 50)

    positions = [
        "1. Past",
        "2. Present",
        "3. Hidden Influences",
        "4. Obstacles",
        "5. Environment",
        "6. Best Course of Action",
        "7. Likely Outcome"
    ]

    dealt = draw_unique_cards(len(positions))
    cards_drawn = []

    for position, (card, is_reversed) in zip(positions, dealt):
        print(f"\n{position}:")
        display_card(card, is_reversed)
        cards_drawn.append((card['name'], is_reversed))

        if position != positions[-1]:
            input("Press Enter for next card...")

    return {"spread": "horseshoe", "cards": cards_drawn}

def yes_no_reading():
    """Simple Yes/No reading"""
    print("\n" + "═" * 50)
    print("YES/NO READING")
    print("═" * 50)
    print("\nFocus on your question...")

    card, is_reversed = draw_card()

    # Upright = Yes, Reversed = No
    answer = "NO" if is_reversed else "YES"

    print(f"\nAnswer: {answer}")
    display_card(card, is_reversed)

    return {"spread": "yes_no", "cards": [(card['name'], is_reversed)], "answer": answer}

def relationship_reading():
    """Relationship spread - 5 cards"""
    print("\n" + "═" * 50)
    print("RELATIONSHIP READING")
    print("═" * 50)

    positions = [
        "1. You",
        "2. The Other Person",
        "3. The Relationship",
        "4. Challenges",
        "5. Potential Outcome"
    ]

    dealt = draw_unique_cards(len(positions))
    cards_drawn = []

    for position, (card, is_reversed) in zip(positions, dealt):
        print(f"\n{position}:")
        display_card(card, is_reversed)
        cards_drawn.append((card['name'], is_reversed))

        if position != positions[-1]:
            input("Press Enter for next card...")

    return {"spread": "relationship", "cards": cards_drawn}

def save_reading(reading_data: Dict):
    """Save a reading to history"""
    reading_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        else:
            history = []

        history.append(reading_data)

        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)

        print(f"\n✓ Reading saved to history!")
    except Exception as e:
        print(f"\n✗ Error saving reading: {e}")

def view_reading_history():
    """View past readings"""
    if not os.path.exists(HISTORY_FILE):
        print("\nNo reading history found.")
        return

    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)

        if not history:
            print("\nNo readings in history.")
            return

        print("\n" + "═" * 50)
        print("READING HISTORY")
        print("═" * 50)

        for i, reading in enumerate(reversed(history[-10:]), 1):  # Show last 10
            print(f"\n{i}. {reading['timestamp']} - {reading['spread'].upper()} spread")
            card_parts = [
                f"{card_name}{' (R)' if is_reversed else ''}"
                for card_name, is_reversed in reading['cards']
            ]
            print(f"   Cards: {', '.join(card_parts)}")
            if 'answer' in reading:
                print(f"   Answer: {reading['answer']}")

        print(f"\nShowing last {min(len(history), 10)} of {len(history)} total readings.")
    except Exception as e:
        print(f"\n✗ Error loading history: {e}")

def daily_card():
    """Get a card for the day (same card per day)"""
    today = datetime.now().strftime("%Y-%m-%d")

    # Try to reuse today's saved card if the file exists, is for today,
    # and references a card that actually exists in the deck. Anything
    # else falls through to fresh generation so the header is only
    # printed once per call.
    if os.path.exists(DAILY_CARD_FILE):
        try:
            with open(DAILY_CARD_FILE, 'r') as f:
                daily_data = json.load(f)

            if daily_data.get('date') == today:
                saved_card = next(
                    (c for c in tarot_deck if c['name'] == daily_data.get('card_name')),
                    None
                )
                if saved_card is not None:
                    print("\n" + "═" * 50)
                    print(f"CARD OF THE DAY - {today}")
                    print("═" * 50)
                    display_card(saved_card, daily_data.get('is_reversed', False))
                    return
        except (OSError, json.JSONDecodeError):
            pass

    # Generate new daily card
    print("\n" + "═" * 50)
    print(f"CARD OF THE DAY - {today}")
    print("═" * 50)

    card, is_reversed = draw_card()
    display_card(card, is_reversed)

    # Save today's card
    daily_data = {
        'date': today,
        'card_name': card['name'],
        'is_reversed': is_reversed
    }

    with open(DAILY_CARD_FILE, 'w') as f:
        json.dump(daily_data, f)

def filter_by_arcana(arcana_type: str):
    """Filter cards by Major or Minor Arcana"""
    if arcana_type.lower() == 'major':
        filtered = [card for card in tarot_deck if card['name'] in MAJOR_ARCANA]
        title = "MAJOR ARCANA"
    else:
        filtered = [card for card in tarot_deck if card['name'] not in MAJOR_ARCANA]
        title = "MINOR ARCANA"

    print("\n" + "═" * 50)
    print(title)
    print("═" * 50)
    print(f"\nTotal: {len(filtered)} cards\n")

    for card in filtered:
        print(f"- {card['name']}")
    print()

def list_all_cards():
    """List all available cards"""
    print("\n" + "═" * 50)
    print(f"ALL TAROT CARDS ({len(tarot_deck)} total)")
    print("═" * 50)

    print("\nMAJOR ARCANA:")
    for card in tarot_deck:
        if card['name'] in MAJOR_ARCANA:
            print(f"  - {card['name']}")

    print("\nMINOR ARCANA:")
    for card in tarot_deck:
        if card['name'] not in MAJOR_ARCANA:
            print(f"  - {card['name']}")
    print()

def change_interpretation_mode():
    """Change the interpretation system"""
    global current_interpretation_mode

    print("\n" + "═" * 50)
    print("SELECT INTERPRETATION SYSTEM")
    print("═" * 50)
    print("\nChoose how you'd like your cards interpreted:\n")

    modes = list(INTERPRETATION_SYSTEMS.items())
    for i, (key, name) in enumerate(modes, 1):
        marker = "→" if key == current_interpretation_mode else " "
        print(f"{marker} {i}. {name}")

        # Add description
        if key == 'rws_traditional':
            print("     Traditional meanings, story-based, beginner-friendly")
        elif key == 'thoth_crowley':
            print("     Esoteric, occult, Kabbalistic, advanced symbolism")
        elif key == 'jungian_psychological':
            print("     Psychological archetypes, shadow work, individuation")
        elif key == 'modern_intuitive':
            print("     Contemporary themes, personal connection, intuitive")

    print()
    choice = input("Enter your choice (or press Enter to keep current): ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(modes):
            current_interpretation_mode = modes[idx][0]
            print(f"\n✓ Interpretation mode changed to: {INTERPRETATION_SYSTEMS[current_interpretation_mode]}")
        else:
            print("\n✗ Invalid choice.")
    else:
        print(f"\n✓ Keeping current mode: {INTERPRETATION_SYSTEMS[current_interpretation_mode]}")

def compare_interpretations():
    """View all interpretations for a specific card"""
    print("\n" + "═" * 50)
    print("COMPARE INTERPRETATIONS")
    print("═" * 50)

    card_name = input("\nEnter card name: ").strip()

    # Find the card
    card = None
    for c in tarot_deck:
        if c['name'].lower() == card_name.lower():
            card = c
            break

    if not card:
        print(f"\n✗ Card not found: {card_name}")
        return

    # Ask for position
    position = input("Upright or Reversed? (u/r, default: u): ").strip().lower()
    is_reversed = position == 'r'

    # Display card with all interpretations
    display_card(card, is_reversed, show_all_interpretations=True)

def interpretation_guide():
    """Show guide to interpretation systems"""
    print("\n" + "═" * 50)
    print("INTERPRETATION SYSTEMS GUIDE")
    print("═" * 50)

    print("\n1. RIDER-WAITE-SMITH (Traditional)")
    print("   • Most popular and beginner-friendly system")
    print("   • Story-based interpretations from card imagery")
    print("   • Based on A.E. Waite's 1909 deck")
    print("   • Linear narrative following The Fool's Journey")

    print("\n2. THOTH/CROWLEY (Esoteric)")
    print("   • Deep occult and Kabbalistic symbolism")
    print("   • Based on Aleister Crowley's 1969 deck")
    print("   • Rich in alchemy and hermetic philosophy")
    print("   • Some cards renamed (e.g., Strength → Lust)")

    print("\n3. JUNGIAN/PSYCHOLOGICAL (Archetypes)")
    print("   • Based on Carl Jung's analytical psychology")
    print("   • Focus on archetypes and the collective unconscious")
    print("   • Emphasizes shadow work and individuation")
    print("   • Cards as mirrors for inner psychological states")

    print("\n4. MODERN/INTUITIVE (Contemporary)")
    print("   • Contemporary language and themes")
    print("   • Emphasizes personal connection to cards")
    print("   • Flexible, intuitive approach")
    print("   • Relevant to modern life situations")

    print("\n" + "─" * 50)
    print("Current mode: " + INTERPRETATION_SYSTEMS[current_interpretation_mode])
    print("═" * 50 + "\n")

def display_menu():
    """Display the main menu"""
    global current_interpretation_mode

    print("\n" + "╔" + "═" * 48 + "╗")
    print("║" + " " * 12 + "ASCII TAROT READER" + " " * 18 + "║")
    print("╚" + "═" * 48 + "╝")
    print(f"Current Interpretation: {INTERPRETATION_SYSTEMS[current_interpretation_mode]}")
    print("\n📖 READINGS:")
    print("  1. Single Card Reading")
    print("  2. Three Card Reading (Past, Present, Future)")
    print("  3. Celtic Cross (10 cards)")
    print("  4. Horseshoe Spread (7 cards)")
    print("  5. Yes/No Reading")
    print("  6. Relationship Reading (5 cards)")
    print("  7. Daily Card")
    print("\n🔍 SEARCH & BROWSE:")
    print("  8. Search card by name")
    print("  9. Search by keyword")
    print("  10. List all cards")
    print("  11. Show Major Arcana only")
    print("  12. Show Minor Arcana only")
    print("\n📚 HISTORY:")
    print("  13. View reading history")
    print("\n🔮 INTERPRETATION SYSTEMS:")
    print("  14. Change interpretation system")
    print("  15. Compare all interpretations for a card")
    print("  16. Interpretation systems guide")
    print("\n  0. Exit")
    print()

def main():
    """Main interactive menu"""
    while True:
        display_menu()
        choice = input("Enter your choice: ").strip()

        reading_data = None

        try:
            if choice == '0':
                print("\n✨ Thank you for using ASCII Tarot Reader! ✨\n")
                break
            elif choice == '1':
                reading_data = single_card_reading()
            elif choice == '2':
                reading_data = three_card_reading()
            elif choice == '3':
                reading_data = celtic_cross_reading()
            elif choice == '4':
                reading_data = horseshoe_reading()
            elif choice == '5':
                reading_data = yes_no_reading()
            elif choice == '6':
                reading_data = relationship_reading()
            elif choice == '7':
                daily_card()
            elif choice == '8':
                card_name = input("\nEnter card name: ").strip()
                search_card(card_name)
            elif choice == '9':
                keyword = input("\nEnter keyword to search: ").strip()
                results = search_by_keyword(keyword)
                if results:
                    show = input("\nShow a card? Enter card name (or press Enter to skip): ").strip()
                    if show:
                        search_card(show)
            elif choice == '10':
                list_all_cards()
            elif choice == '11':
                filter_by_arcana('major')
            elif choice == '12':
                filter_by_arcana('minor')
            elif choice == '13':
                view_reading_history()
            elif choice == '14':
                change_interpretation_mode()
            elif choice == '15':
                compare_interpretations()
            elif choice == '16':
                interpretation_guide()
            else:
                print("\n✗ Invalid choice. Please try again.")
                continue

            # Save reading if one was performed
            if reading_data:
                save = input("\nSave this reading to history? (y/n): ").strip().lower()
                if save == 'y':
                    save_reading(reading_data)

            input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n✨ Thank you for using ASCII Tarot Reader! ✨\n")
            break
        except Exception as e:
            print(f"\n✗ An error occurred: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
