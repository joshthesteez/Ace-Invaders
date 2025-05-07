# blackjack_game/settings.py
# Consolidated from config.py and game/settings.py

import json
import os

# Default settings
DEFAULT_SETTINGS = {
    'GAME_SETTINGS': {
        'MAX_DECKS': 8,
        'MIN_DECKS': 1,
        'DEFAULT_CUT_CARD_PERCENT': 0.75,
        'SHOW_HOUSE_EDGE': True,
        'SHOW_HINTS': True,
    },

    'PLAYER_SETTINGS': {
        'MIN_BET': 1,
        'MAX_BET': 1000,
        'BET_INCREMENT': [1, 2, 5, 10, 25, 50, 100],
        'INITIAL_BANKROLL': 1000,
    },

    'DEALER_SETTINGS': {
        'DEALER_HIT_ON_SOFT_17': False,
        'DEALER_STAND_ON_HARD_17': True,
    }
}

# Path to settings file - find it relative to this module
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

def clear_screen():
    """Utility function to clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

# Load settings from file or use defaults
def load_settings():
    """Load settings from JSON file or return defaults if file doesn't exist."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            print("Error loading settings file. Using defaults.")
    return DEFAULT_SETTINGS

# Save settings to file
def save_settings(settings=None):
    """Save settings to JSON file."""
    if settings is None:
        settings = SETTINGS
        
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# Get the settings
SETTINGS = load_settings()
GAME_SETTINGS = SETTINGS['GAME_SETTINGS']
PLAYER_SETTINGS = SETTINGS['PLAYER_SETTINGS']
DEALER_SETTINGS = SETTINGS['DEALER_SETTINGS']

# Settings menu function
def settings_menu():
    """Settings menu with house edge display options."""
    while True:
        clear_screen()
        print("=== Ace Invaders Settings ===\n")

        print(f"1. Toggle Showing House Edge (Currently: {'ON' if SETTINGS['GAME_SETTINGS'].get('SHOW_HOUSE_EDGE', True) else 'OFF'})")
        print(f"2. Toggle Card Counting Hints (Currently: {'ON' if SETTINGS['GAME_SETTINGS'].get('SHOW_HINTS', False) else 'OFF'})")
        print(f"3. Toggle Dealer Hits Soft 17 (Currently: {'ON' if SETTINGS['DEALER_SETTINGS'].get('DEALER_HIT_ON_SOFT_17', False) else 'OFF'})")
        print(f"4. Set Blackjack Payout (Currently: {SETTINGS['GAME_SETTINGS'].get('BLACKJACK_PAYOUT', '3:2')})")
        print(f"5. Set Number of Decks (Currently: {SETTINGS['GAME_SETTINGS'].get('NUM_DECKS', 6)})")
        print("\n6. Game Rules Settings")
        print("7. Save and Return to Main Menu")

        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            current = SETTINGS['GAME_SETTINGS'].get('SHOW_HOUSE_EDGE', True)
            SETTINGS['GAME_SETTINGS']['SHOW_HOUSE_EDGE'] = not current

        elif choice == '2':
            current = SETTINGS['GAME_SETTINGS'].get('SHOW_HINTS', False)
            SETTINGS['GAME_SETTINGS']['SHOW_HINTS'] = not current
            
        elif choice == '3':
            current = SETTINGS['DEALER_SETTINGS'].get('DEALER_HIT_ON_SOFT_17', False)
            SETTINGS['DEALER_SETTINGS']['DEALER_HIT_ON_SOFT_17'] = not current
            
        elif choice == '4':
            clear_screen()
            print("=== Blackjack Payout Settings ===\n")
            print("1. 3:2 (Standard payout)")
            print("2. 6:5 (Reduced payout)")
            print("3. 1:1 (Even money payout)")
            print("\n4. Back to Settings")
            
            payout_choice = input("\nChoose a payout option: ").strip()
            
            if payout_choice == '1':
                SETTINGS['GAME_SETTINGS']['BLACKJACK_PAYOUT'] = '3:2'
            elif payout_choice == '2':
                SETTINGS['GAME_SETTINGS']['BLACKJACK_PAYOUT'] = '6:5'
            elif payout_choice == '3':
                SETTINGS['GAME_SETTINGS']['BLACKJACK_PAYOUT'] = '1:1'
                
        elif choice == '5':
            clear_screen()
            print("=== Number of Decks Settings ===\n")
            print("How many decks would you like to play with?")
            print(f"Min: {GAME_SETTINGS['MIN_DECKS']}, Max: {GAME_SETTINGS['MAX_DECKS']}")
            
            try:
                num_decks = int(input("\nEnter number of decks: ").strip())
                if GAME_SETTINGS['MIN_DECKS'] <= num_decks <= GAME_SETTINGS['MAX_DECKS']:
                    SETTINGS['GAME_SETTINGS']['NUM_DECKS'] = num_decks
                else:
                    print(f"Please enter a number between {GAME_SETTINGS['MIN_DECKS']} and {GAME_SETTINGS['MAX_DECKS']}.")
                    input("Press Enter to continue...")
            except ValueError:
                print("Please enter a valid number.")
                input("Press Enter to continue...")
                
        elif choice == '6':
            game_rules_settings()

        elif choice == '7':
            save_settings()
            print("\nSettings saved! Returning to Main Menu...")
            input("Press Enter to continue...")
            break

        else:
            print("\nInvalid option.")
            input("Press Enter to try again...")