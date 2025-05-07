# game/main_loop.py

import os
import time
import sys
import random
import msvcrt  # For Windows compatibility
from colorama import init, Fore, Style
from art import *

from blackjack_game.profile_manager import ProfileManager, PlayerProfile
from blackjack_game.settings import settings_menu
from blackjack_game.game_session import GameSession, Table, load_table_from_json
import json

# Initialize colorama
init(autoreset=True)

def flush_input():
    """Flush any buffered key presses (Windows only)."""
    try:
        while msvcrt.kbhit():
            msvcrt.getch()
    except:
        pass


def print_scanlines(height, width):
    gold = Fore.YELLOW
    os.system('cls' if os.name == 'nt' else 'clear')
    for i in range(height):
        if i % 2 == 0:
            print(gold + "-" * width)
        else:
            print()

def type_logo_colored(logo_lines, ace_color, invaders_color, split_index, delay=0.002):
    """Print logo with colors line-by-line, character-by-character."""
    for idx, line in enumerate(logo_lines):
        color = ace_color if idx < split_index else invaders_color
        for char in line:
            sys.stdout.write(color + Style.BRIGHT + char + Style.RESET_ALL)
            sys.stdout.flush()
            time.sleep(delay)
        print()

def pulse_logo_colored(logo_lines, ace_color, invaders_color, split_index, cycles=3, sleep_time=0.3):
    """Pulse the logo brightness (dim and bright cycles) with correct colors."""
    for _ in range(cycles):
        os.system('cls' if os.name == 'nt' else 'clear')
        # Dim version
        for idx, line in enumerate(logo_lines):
            color = ace_color if idx < split_index else invaders_color
            print(color + Style.DIM + line + Style.RESET_ALL)
        time.sleep(sleep_time)

        os.system('cls' if os.name == 'nt' else 'clear')
        # Bright version
        for idx, line in enumerate(logo_lines):
            color = ace_color if idx < split_index else invaders_color
            print(color + Style.BRIGHT + line + Style.RESET_ALL)
        time.sleep(sleep_time)

def animated_logo_intro():
    # Update the path to point to the resources directory
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources/logo.txt'))
    
    # Check if the file exists, and if not, try alternate paths
    if not os.path.exists(path):
        # Try the project root directory
        alt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logo.txt'))
        if os.path.exists(alt_path):
            path = alt_path
        else:
            # As a fallback, create a simple logo
            print("Logo file not found. Using simple text header.")
            logo_lines = [
                "  ___   ___ ___   ___ _  ___   _____ ___  ___ ___ ___ ",
                " / _ \\ / __| __| |_ _| \\| \\ \\ / / _ \\   \\| __| _ \\ __|",
                "| (_) | (__| _|   | || .` |\\ V /|   / |) | _||   / _| ",
                " \\___/ \\___|___| |___|_|\\_| \\_/ |_|_\\___/|___|_|_\\___|"
            ]
            
            split_index = 2  # Arbitrary split for coloring
            red = Fore.LIGHTRED_EX
            green = Fore.LIGHTGREEN_EX
            
            for idx, line in enumerate(logo_lines):
                color = red if idx < split_index else green
                print(color + Style.BRIGHT + line + Style.RESET_ALL)
            
            time.sleep(1)
            
            # Return early as we've printed the logo
            print("\n")
            for _ in range(3):
                sys.stdout.write(Fore.LIGHTYELLOW_EX + "\rPress Enter to Start..." + Style.RESET_ALL)
                sys.stdout.flush()
                time.sleep(0.5)
                sys.stdout.write("\r                      ")
                sys.stdout.flush()
                time.sleep(0.5)

            flush_input()
            input(Fore.LIGHTYELLOW_EX + "\rPress Enter to Start..." + Style.RESET_ALL)
            os.system('cls' if os.name == 'nt' else 'clear')
            return

    with open(path, 'r') as f:
        logo_lines = [line.rstrip('\n') for line in f.readlines()]

    # Rest of the function remains the same
    width = max(len(line) for line in logo_lines)
    height = len(logo_lines)

    split_index = len(logo_lines) // 2  # Where ACE ends and INVADERS starts
    red = Fore.LIGHTRED_EX
    green = Fore.LIGHTGREEN_EX

    # --- Step 1: CRT Flicker ---
    for _ in range(5):
        if random.random() > 0.5:
            print(Fore.WHITE + Style.BRIGHT + "\n" * random.randint(5, 10) + "█" * random.randint(10, 30) + Style.RESET_ALL)
        else:
            print("\n" * random.randint(5, 10))
        time.sleep(0.08)
        os.system('cls' if os.name == 'nt' else 'clear')

    time.sleep(0.5)

    # --- Step 2: CRT Gold Scanlines ---
    print_scanlines(height, width)
    time.sleep(0.5)

    # --- Step 3: Typing Logo with Gradient ---
    os.system('cls' if os.name == 'nt' else 'clear')
    type_logo_colored(logo_lines, ace_color=red, invaders_color=green, split_index=split_index)
    time.sleep(0.5)

    # --- Step 4: Pulse Glow with Gradient ---
    pulse_logo_colored(logo_lines, ace_color=red, invaders_color=green, split_index=split_index)

    # --- Step 5: Blinking Press Start ---
    print("\n")
    for _ in range(3):
        sys.stdout.write(Fore.LIGHTYELLOW_EX + "\rPress Enter to Start..." + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(0.5)
        sys.stdout.write("\r                      ")
        sys.stdout.flush()
        time.sleep(0.5)

    # Flush any early Enter presses BEFORE asking for input
    flush_input()

    input(Fore.LIGHTYELLOW_EX + "\rPress Enter to Start..." + Style.RESET_ALL)
    os.system('cls' if os.name == 'nt' else 'clear')

# Load table1.json for campaign mode
def load_starter_table():
    """Load the starter table configuration from table1.json."""
    try:
        # Create a path to the table1.json file
        table_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            '../resources/tables/campaign/table1.json'
        ))
        
        # If the file doesn't exist, create a SimpleTable from default values
        if not os.path.exists(table_path):
            return SimpleTable()
            
        # Load the table using our function from game_session.py
        return load_table_from_json(table_path)
    except Exception as e:
        print(f"Error loading table: {e}")
        return SimpleTable()  # Fallback to default table


# Simple table class for the game session
class SimpleTable(Table):
    """A simple wrapper around Table for compatibility."""
    
    def __init__(self, table_data=None):
        # Default values if no table data is provided
        name = "Starter Casino"
        description = "Standard 6-deck blackjack. Dealer hits on soft 17. Blackjack pays 3:2."
        
        rules = {
            "number_of_decks": 6,
            "dealer_hits_soft_17": True,
            "blackjack_payout": "3:2",
            "min_bet": 5,
            "max_bet": 500,
            "allow_double_down": True,
            "allow_split": True,
            "allow_surrender": False,
            "resplit_aces": False,
            "dealer_peek": True,
            "insurance_allowed": True
        }
        
        # Override defaults with provided table data if available
        if table_data:
            name = table_data.get("table_name", name)
            description = table_data.get("description", description)
            
            # Update rules from settings if provided
            if "settings" in table_data:
                rules.update(table_data["settings"])
        
        # Initialize the parent Table class
        super().__init__(name=name, description=description, rules=rules)

# Campaign mode function
def start_campaign_mode(profile):
    """Start the campaign mode with the first table."""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Display campaign mode header
    header = text2art("Campaign Mode", "small")
    print(Fore.LIGHTGREEN_EX + header + Style.RESET_ALL)
    print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)
    
    # Load the starter table
    table = load_starter_table()
    
    print(f"\nWelcome to {Fore.CYAN}{table.display_name()}{Style.RESET_ALL}!")
    print(f"\n{table.description}\n")
    print(Fore.YELLOW + "-" * 50 + Style.RESET_ALL)
    print(f"Your bankroll: ${profile.bankroll}")
    print(f"Bet range: ${table.rules.get('min_bet', 5)} - ${table.rules.get('max_bet', 500)}")
    print(Fore.YELLOW + "-" * 50 + Style.RESET_ALL)
    
    # Create a game session
    game_session = GameSession(profile, table)
    
    # Display table information including house edge
    game_session.display_table_info()
    
    input("\nPress Enter to start playing...")
    
    # Run the game session
    game_session.play()
    
    # Save player profile after the game
    print("\nSaving your progress...")
    profile_manager = ProfileManager()
    profile_manager.save_profile(profile)
    
    input("\nPress Enter to return to the main menu...")

# Main menu loop
def main_menu():
    animated_logo_intro()  # Show animated logo intro
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen after intro

    profile_manager = ProfileManager()
    profile = None

    while not profile:
        welcome = text2art("Welcome to Ace Invaders", "tarty2")
        print(Fore.LIGHTYELLOW_EX + welcome + Style.RESET_ALL)
        print(Fore.LIGHTYELLOW_EX + "==============================" + Style.RESET_ALL)
        print(Fore.LIGHTYELLOW_EX + "  A Blackjack Game Experience  " + Style.RESET_ALL)
        print(Fore.LIGHTYELLOW_EX + "==============================" + Style.RESET_ALL)

        load_prof = text2art("1. L o a d P r o f i l e", "fancy143")
        print(load_prof)
        create_prof = text2art("2. C r e a t e P r o f i l e", "fancy143")
        print(create_prof)
        exit_game = text2art("3. E x i t", "fancy143")
        print(exit_game)
        choice = input("Choose an option: ").strip()

        if choice == '1':
            profiles = profile_manager.list_profiles()
            if not profiles:
                print("\nNo saved profiles found.\n")
                time.sleep(1.5)
                continue

            print("\nSaved Profiles:")
            for i, name in enumerate(profiles, 1):
                print(f"{i}. {name}")
            index = input("Select a profile number: ").strip()
            if index.isdigit() and 0 < int(index) <= len(profiles):
                profile = profile_manager.load_profile(profiles[int(index) - 1])

        elif choice == '2':
            name = input("Enter profile name: ").strip()
            profile = profile_manager.create_profile(name)

        elif choice == '3':
            print("Goodbye!")
            exit()

    # After login, show main mode menu
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Logged in as: {profile.name} | Bankroll: ${profile.bankroll} | XP: {profile.xp}")
        print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)
        print("1. Campaign Mode")
        print("2. Sandbox Mode")
        print("3. Settings")
        print("4. Save and Quit")
        choice = input("\nChoose a mode: ").strip()

        if choice == '1':
            start_campaign_mode(profile)
        elif choice == '2':
            print("\n[SANDBOX MODE COMING SOON]\n")
            input("Press Enter to return to the menu...")
        elif choice == '3':
            settings_menu()
        elif choice == '4':
            profile_manager.save_profile(profile)
            print("\nProfile saved. Goodbye!")
            break
        else:
            print("\nInvalid option.")
            time.sleep(1.2)

if __name__ == "__main__":
    main_menu()