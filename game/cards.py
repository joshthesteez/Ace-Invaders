# blackjack_game/cards.py
# Consolidated from card.py, deck.py, and ascii_art.py

import random
from game.settings import GAME_SETTINGS

#################################################
# Card Class Definition
#################################################
class Card:
    """
    Represents a playing card in the game.
    
    Attributes:
        suit (str): 'Hearts', 'Diamonds', 'Clubs', or 'Spades'
        rank (str): '2' through '10', 'J', 'Q', 'K', or 'A'
        value (int): Blackjack value of the card (1-11 for Ace, 10 for face cards)
    """
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        
        # Determine card value for blackjack
        if rank == 'A':
            self.value = 11  # Will be adjusted to 1 when needed
        elif rank in ['J', 'Q', 'K']:
            self.value = 10
        else:
            self.value = int(rank)
            
    def __str__(self):
        """Returns string representation like 'A♥' or '10♣'"""
        suit_symbols = {
            'Hearts': '♥',
            'Diamonds': '♦',
            'Clubs': '♣',
            'Spades': '♠'
        }
        return f"{self.rank}{suit_symbols[self.suit]}"
        
    def get_count_value(self):
        """Returns the card counting value in Hi-Lo system"""
        if self.rank in ['2', '3', '4', '5', '6']:
            return 1
        elif self.rank in ['10', 'J', 'Q', 'K', 'A']:
            return -1
        else:
            return 0


#################################################
# Deck Class Definition
#################################################
class Deck:
    """
    Represents a shoe of playing cards for blackjack.
    
    Attributes:
        cards (list): List of Card objects in the deck
        number_of_decks (int): Number of standard decks in the shoe
        running_count (int): Current running count for card counting
        initial_cards (int): Total cards when deck was created
        cut_card_position (int): Position of the cut card in the deck
    """
    
    def __init__(self, number_of_decks=None, cut_card_percent=0.75):
        # Set default to 1 deck if None provided
        if number_of_decks is None:
            number_of_decks = 1
            
        # Validate deck count against settings
        if number_of_decks < GAME_SETTINGS['MIN_DECKS']:
            raise ValueError(f"Number of decks must be at least {GAME_SETTINGS['MIN_DECKS']}")
        if number_of_decks > GAME_SETTINGS['MAX_DECKS']:
            raise ValueError(f"Number of decks must be at most {GAME_SETTINGS['MAX_DECKS']}")

        self.number_of_decks = number_of_decks
        self.running_count = 0
        self.cards = []
        
        self.build_deck()
        self.initial_cards = len(self.cards)
        
        # Set cut card position
        self.cut_card_position = int(self.initial_cards * (1 - cut_card_percent))
        
    def __str__(self):
        """String representation for debugging."""
        return f"Deck: {len(self.cards)} cards, {self.number_of_decks} decks, count: {self.running_count}"
        
    def build_deck(self):
        """Creates a new deck with the specified number of standard decks"""
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        for _ in range(self.number_of_decks):
            for suit in suits:
                for rank in ranks:
                    self.cards.append(Card(suit, rank))
                    
    def shuffle(self):
        """Shuffles the deck and resets the running count"""
        random.shuffle(self.cards)
        self.running_count = 0
        
    def deal_card(self, face_up=True):
        """
        Deals a card from the deck and updates running count if face up
        
        Args:
            face_up (bool): Whether the card is dealt face up
            
        Returns:
            Card: The dealt card or None if deck is empty
        """
        if not self.cards:
            return None
            
        card = self.cards.pop(0)  # Deal from the top of the deck
        
        # Update running count if card is face up
        if face_up:
            self.running_count += card.get_count_value()
            
        return card
        
    def cards_left(self):
        """Returns the number of cards left in the deck"""
        return len(self.cards)
        
    def get_true_count(self):
        """Calculates the true count based on running count and decks remaining"""
        decks_remaining = max(1, self.cards_left() / 52)  # Avoid division by zero
        return self.running_count / decks_remaining
        
    def is_cut_card(self):
        """Returns whether the cut card has been reached"""
        return self.cards_left() <= self.cut_card_position
    
    def print_deck(self):
        """Prints all cards in the deck (for debugging)."""
        for card in self.cards:
            print(card, end=' ')
        print()


#################################################
# ASCII Art for Cards 
#################################################
def render_card(card, face_up=True, horizontal=False):
    """
    Renders a single card as ASCII art.

    Args:
        card (Card): The Card object to render
        face_up (bool): Whether the card is face up
        horizontal (bool): Whether the card is displayed horizontally

    Returns:
        list of str: Each string is a line of ASCII art
    """
    if not face_up:
        if horizontal:
            return [
                "┌───────┐",
                "│░░░░░░░│",
                "└───────┘"
            ]
        else:
            return [
                "┌─────────┐",
                "│░░░░░░░░░│",
                "│░░░░░░░░░│",
                "│░░░░░░░░░│",
                "│░░░░░░░░░│",
                "│░░░░░░░░░│",
                "└─────────┘"
            ]

    # Face-up card
    rank = card.rank
    suit_symbols = {
        'Hearts':   '♥',
        'Diamonds': '♦',
        'Clubs':    '♣',
        'Spades':   '♠'
    }
    suit = suit_symbols.get(card.suit, '?')

    if horizontal:
        rank_left = rank.ljust(2)
        rank_right = rank.rjust(2)
        return [
            "┌───────┐",
            f"│{rank_left} {suit} {rank_right}│",
            "└───────┘"
        ]
    else:
        rank_top = rank.ljust(2)
        rank_bottom = rank.rjust(2)
        return [
            "┌─────────┐",
            f"│{rank_top}       │",
            "│         │",
            f"│    {suit}    │",
            "│         │",
            f"│       {rank_bottom}│",
            "└─────────┘"
        ]

def render_multiple(cards):
    """
    Renders multiple cards side-by-side.

    Args:
        cards (list of (Card, face_up, horizontal) tuples)

    Returns:
        str: ASCII art representation of multiple cards
        
    Example:
        cards = [
            (card1, True, False),
            (card2, False, False),
            (card3, True, True),
        ]
    """
    card_lines = []
    for card, face_up, horizontal in cards:
        card_lines.append(render_card(card, face_up, horizontal))

    output = ""
    max_height = max(len(card) for card in card_lines)

    for i in range(max_height):
        line = ""
        for card in card_lines:
            if i < len(card):
                line += card[i] + "  "
            else:
                line += " " * (len(card[0]) + 2)  # space filler for short cards
        output += line.rstrip() + "\n"

    return output

def display_hand(hand, show_value=True):
    """
    Helper function to display a hand of cards with text representation.
    
    Args:
        hand (list): List of Card objects
        show_value (bool): Whether to show the hand value
        
    Returns:
        str: Text representation of the hand
    """
    if not hand:
        return "Empty hand"
        
    # Calculate hand value if needed
    value_text = ""
    if show_value:
        value = sum(card.value for card in hand)
        aces = sum(1 for card in hand if card.rank == 'A')
        
        while value > 21 and aces:
            value -= 10
            aces -= 1
            
        value_text = f" (Value: {value})"
    
    return ', '.join(str(card) for card in hand) + value_text
