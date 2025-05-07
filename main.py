# blackjack_game/main.py
# Entry point for the Ace Invaders blackjack game

from blackjack_game.main_loop import main_menu

def main():
    """
    Main entry point for the Ace Invaders blackjack game.
    
    This function initializes the game and displays the main menu.
    """
    print("Starting Ace Invaders Blackjack...")
    main_menu()

if __name__ == "__main__":
    main()