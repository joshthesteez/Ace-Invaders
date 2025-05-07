# blackjack_game/game_session.py

import random
import time
import json
import os

from game.cards import Card, Deck, display_hand, render_multiple
from game.players import Player, Dealer, get_basic_strategy_move
from game.settings import SETTINGS, GAME_SETTINGS, PLAYER_SETTINGS

#################################################
# Table Class Definition
#################################################
class Table:
    """
    Represents a blackjack table with specific rules and requirements.
    
    Attributes:
        name (str): Table name
        rules (dict): Dictionary of game rule settings
        unlock_type (str): Type of requirement to unlock ('xp' or 'bankroll')
        unlock_value (int/float): Value needed to unlock the table
        description (str): Table description
        house_edge (float): House edge percentage
        show_house_edge (bool): Whether to display house edge
    """
    
    def __init__(self, name, rules, unlock_type=None, unlock_value=0, description="", house_edge=None, show_house_edge=True):
        self.name = name
        self.rules = rules  # Dictionary of game rule overrides
        self.unlock_type = unlock_type  # "xp" or "bankroll" or None
        self.unlock_value = unlock_value
        self.description = description
        self.show_house_edge = show_house_edge
        
        # Calculate house edge if not provided
        if house_edge is None:
            self.house_edge = self.calculate_house_edge()
        else:
            self.house_edge = house_edge

    def is_unlocked(self, profile):
        """Check if the player has unlocked this table."""
        if not self.unlock_type:
            return True
        if self.unlock_type == 'xp':
            return profile.xp >= self.unlock_value
        if self.unlock_type == 'bankroll':
            return profile.bankroll >= self.unlock_value
        return False

    def display_name(self):
        """Returns display name including optional house edge."""
        if self.show_house_edge and self.house_edge is not None:
            return f"{self.name} (House Edge: {self.house_edge:.2f}%)"
        return self.name
        
    def calculate_house_edge(self):
        """
        Calculate the house edge based on the table rules.
        
        Returns:
            float: The calculated house edge percentage
        """
        # Start with base house edge (standard blackjack with perfect basic strategy)
        house_edge = 0.5  # Base house edge of 0.5%
        
        # Adjust for number of decks
        decks = self.rules.get("number_of_decks", 6)
        if decks == 1:
            house_edge -= 0.25  # Single deck reduces house edge
        elif decks == 2:
            house_edge -= 0.2  # Double deck reduces house edge
        elif decks > 6:
            house_edge += 0.02 * (decks - 6)  # Each additional deck over 6 increases edge
        
        # Adjust for blackjack payout
        blackjack_payout = self.rules.get("blackjack_payout", "3:2")
        if blackjack_payout == "6:5":
            house_edge += 1.4  # 6:5 payouts significantly increase house edge
        elif blackjack_payout == "1:1":
            house_edge += 2.3  # Even money payouts dramatically increase house edge
        
        # Adjust for dealer rules
        if self.rules.get("dealer_hits_soft_17", False):
            house_edge += 0.2  # Dealer hitting on soft 17 increases house edge
        
        # Adjust for player options
        if not self.rules.get("allow_double_down", True):
            house_edge += 0.2  # Not allowing double down increases house edge
        if not self.rules.get("allow_double_after_split", True):
            house_edge += 0.14  # Not allowing double after split increases house edge
        if not self.rules.get("allow_split", True):
            house_edge += 0.4  # Not allowing splits increases house edge
        if not self.rules.get("resplit_aces", False):
            house_edge += 0.08  # Not allowing resplit of aces increases house edge
        if self.rules.get("allow_surrender", False):
            house_edge -= 0.08  # Allowing surrender decreases house edge
        
        # Adjust for deck penetration (how much of the deck is used before reshuffling)
        penetration = self.rules.get("deck_penetration", 0.75)  # Default to 75%
        if penetration > 0.8:
            house_edge -= 0.1  # Deep penetration reduces house edge (better for card counters)
        elif penetration < 0.5:
            house_edge += 0.1  # Shallow penetration increases house edge
        
        # Adjust for other rules
        if not self.rules.get("dealer_peek", True):
            house_edge += 0.1  # No dealer peek for blackjack increases house edge
        if self.rules.get("insurance_pays", "2:1") != "2:1":
            house_edge += 0.1  # Non-standard insurance payouts increase house edge
        
        # Edge limits
        return max(0.1, min(house_edge, 5.0))  # Realistically between 0.1% and 5%
    
    def get_house_edge_breakdown(self):
        """
        Get a detailed breakdown of house edge calculations.
        
        Returns:
            dict: Factors affecting house edge
        """
        breakdown = {
            "base_edge": 0.5,
            "factors": []
        }
        
        # Number of decks
        decks = self.rules.get("number_of_decks", 6)
        if decks == 1:
            breakdown["factors"].append({"name": "Single deck", "impact": -0.25})
        elif decks == 2:
            breakdown["factors"].append({"name": "Double deck", "impact": -0.2})
        elif decks > 6:
            impact = 0.02 * (decks - 6)
            breakdown["factors"].append({"name": f"{decks} decks", "impact": impact})
        
        # Blackjack payout
        blackjack_payout = self.rules.get("blackjack_payout", "3:2")
        if blackjack_payout == "6:5":
            breakdown["factors"].append({"name": "6:5 blackjack payout", "impact": 1.4})
        elif blackjack_payout == "1:1":
            breakdown["factors"].append({"name": "1:1 blackjack payout", "impact": 2.3})
        
        # Dealer rules
        if self.rules.get("dealer_hits_soft_17", False):
            breakdown["factors"].append({"name": "Dealer hits soft 17", "impact": 0.2})
        
        # Player options
        if not self.rules.get("allow_double_down", True):
            breakdown["factors"].append({"name": "No doubling down", "impact": 0.2})
        if not self.rules.get("allow_double_after_split", True):
            breakdown["factors"].append({"name": "No doubling after split", "impact": 0.14})
        if not self.rules.get("allow_split", True):
            breakdown["factors"].append({"name": "No splitting", "impact": 0.4})
        if not self.rules.get("resplit_aces", False):
            breakdown["factors"].append({"name": "No resplitting aces", "impact": 0.08})
        if self.rules.get("allow_surrender", False):
            breakdown["factors"].append({"name": "Surrender allowed", "impact": -0.08})
        
        # Deck penetration
        penetration = self.rules.get("deck_penetration", 0.75)
        if penetration > 0.8:
            breakdown["factors"].append({"name": "Deep deck penetration", "impact": -0.1})
        elif penetration < 0.5:
            breakdown["factors"].append({"name": "Shallow deck penetration", "impact": 0.1})
        
        # Other rules
        if not self.rules.get("dealer_peek", True):
            breakdown["factors"].append({"name": "No dealer peek", "impact": 0.1})
        if self.rules.get("insurance_pays", "2:1") != "2:1":
            breakdown["factors"].append({"name": "Non-standard insurance", "impact": 0.1})
            
        # Calculate total
        total = breakdown["base_edge"]
        for factor in breakdown["factors"]:
            total += factor["impact"]
            
        breakdown["total_edge"] = max(0.1, min(total, 5.0))
        
        return breakdown

# Utility function to load tables from JSON files
def load_table_from_json(filepath):
    """
    Load a table configuration from a JSON file.
    
    Args:
        filepath (str): Path to the JSON file
        
    Returns:
        Table: The table object
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
            # Convert legacy format if needed
            rules = data.get("rules", {})
            if "settings" in data:
                rules.update(data["settings"])
                
            return Table(
                name=data.get("table_name", data.get("name", "Default Table")),
                description=data.get("description", ""),
                rules=rules,
                unlock_type=data.get("unlock_type"),
                unlock_value=data.get("unlock_value", 0),
                house_edge=data.get("house_edge"),
                show_house_edge=data.get("show_house_edge", True)
            )
    except Exception as e:
        print(f"Error loading table: {e}")
        return Table("Default Table", {})


def load_tables_from_folder(folder_path):
    """
    Load all table configurations from a folder.
    
    Args:
        folder_path (str): Path to the folder containing JSON files
        
    Returns:
        list: List of Table objects
    """
    tables = []
    if not os.path.exists(folder_path):
        return tables
        
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            filepath = os.path.join(folder_path, filename)
            table = load_table_from_json(filepath)
            tables.append(table)
            
    return tables


#################################################
# Game Session Class
#################################################
class GameSession:
    """
    Manages a blackjack game session.
    
    Attributes:
        profile (Profile): The player's profile
        table (Table): The table being played at
        deck (Deck): The deck of cards
        player (Player): The player
        dealer (Dealer): The dealer
        show_hints (bool): Whether to show basic strategy hints
    """
    
    def __init__(self, profile, table):
        self.profile = profile
        self.table = table
        
        # Get settings from table rules or fallback to defaults
        self.number_of_decks = table.rules.get("number_of_decks", GAME_SETTINGS.get('MAX_DECKS', 6))
        self.min_bet = table.rules.get("min_bet", PLAYER_SETTINGS.get('MIN_BET', 5))
        self.max_bet = table.rules.get("max_bet", PLAYER_SETTINGS.get('MAX_BET', 500))
        self.blackjack_payout = table.rules.get("blackjack_payout", "3:2")
        self.dealer_hits_soft_17 = table.rules.get("dealer_hits_soft_17", False)
        
        # Initialize deck
        self.deck = Deck(number_of_decks=self.number_of_decks)
        self.deck.shuffle()
        
        # Initialize dealer
        self.dealer = Dealer()
        
        # Flag to track whether to display hints
        self.show_hints = GAME_SETTINGS.get('SHOW_HINTS', False)
        
        # For tracking split hands
        self.hands_to_compare = []
        
        # Track statistics for this session
        self.session_stats = {
            'hands_played': 0,
            'hands_won': 0,
            'hands_lost': 0,
            'pushes': 0,
            'blackjacks': 0,
            'busts': 0,
            'dealer_busts': 0
        }

    def display_player_hand(self, hand):
        """Display the player's hand with ASCII art."""
        print("\nYour Hand:")
        
        # Prepare cards for rendering - all face up and vertical
        cards_to_render = [(card, True, False) for card in hand]
        
        # Render and display
        card_display = render_multiple(cards_to_render)
        print(card_display)
        
        # Show value
        value = self.hand_value(hand)
        print(f"Total Value: {value}")
        
        # Show if soft
        if self.is_soft_hand(hand):
            print("(Soft Hand)")

    def display_dealer_hand(self, hand, hide_hole_card=False):
        """Display the dealer's hand with ASCII art."""
        if hide_hole_card:
            print("\nDealer Shows:")
            # Only show first card
            cards_to_render = [(hand[0], True, False)]
        else:
            print("\nDealer's Hand:")
            # Show all cards
            cards_to_render = [(card, True, False) for card in hand]
        
        # Render and display
        card_display = render_multiple(cards_to_render)
        print(card_display)
        
        # Show value if all cards visible
        if not hide_hole_card:
            value = self.hand_value(hand)
            print(f"Total Value: {value}")
            
            if self.is_soft_hand(hand):
                print("(Soft Hand)")

    def display_hint(self, hand, dealer_upcard):
        """
        Display a hint based on basic strategy.
        
        Args:
            hand (list): The player's hand
            dealer_upcard (Card): The dealer's visible card
        """
        if not self.show_hints:
            return
            
        # Get the recommended move
        hint = get_basic_strategy_move(hand, dealer_upcard)
        
        # Display the hint with color and explanation
        print("\n💡 Basic Strategy Hint 💡")
        
        # Explanation based on the move
        if hint == 'hit':
            print("Recommended move: HIT")
            print("Reason: Your hand is weak and has a good chance to improve.")
        elif hint == 'stand':
            print("Recommended move: STAND")
            print("Reason: Your hand is strong enough, or the dealer is likely to bust.")
        elif hint == 'double':
            if len(hand) > 2:
                print("Recommended move: HIT (would be DOUBLE if first two cards)")
                print("Reason: This hand would be worth doubling on the initial deal.")
            else:
                print("Recommended move: DOUBLE DOWN")
                print("Reason: Good chance to improve and win with a higher bet.")
        elif hint == 'split':
            print("Recommended move: SPLIT")
            print("Reason: These cards are better played as separate hands.")
        elif hint == 'surrender':
            print("Recommended move: SURRENDER (if available)")
            print("Reason: This hand has a low chance of winning.")
        
        # Ask if the player wants more information
        if random.random() < 0.3:  # Only show this prompt occasionally
            more_info = input("Want to know more about this recommendation? (y/n): ").lower()
            if more_info == 'y':
                self.display_strategy_details(hand, dealer_upcard)

    def display_strategy_details(self, hand, dealer_upcard):
        """Display more detailed strategy information."""
        player_value = self.hand_value(hand)
        dealer_value = dealer_upcard.value
        
        print("\n📊 Strategy Details 📊")
        
        # Information based on hand type
        if self.is_soft_hand(hand):
            print("You have a soft hand (includes Ace counted as 11).")
            print("Soft hands are flexible because the Ace can be counted as 1 if needed.")
            print("This gives you more protection against busting when hitting.")
        elif len(hand) == 2 and hand[0].rank == hand[1].rank:
            print(f"You have a pair of {hand[0].rank}s.")
            print("With pairs, consider whether they're better together or as separate hands.")
            
            # Specific pair advice
            if hand[0].rank == 'A':
                print("Pairs of Aces are usually split to get two strong starting hands.")
            elif hand[0].rank in ['10', 'J', 'Q', 'K']:
                print("10-value pairs total 20, which is already a strong hand.")
            elif hand[0].rank in ['5', '4']:
                print("Low-mid pairs are often better played together than split.")
            elif hand[0].rank in ['8']:
                print("Pairs of 8s are usually split to avoid a stiff 16.")
        else:
            print(f"You have a hard hand totaling {player_value}.")
            if player_value >= 17:
                print("High-value hard hands usually stand to avoid busting.")
            elif 12 <= player_value <= 16:
                print("Values 12-16 are 'stiff hands' with high bust risk.")
                if dealer_value >= 7:
                    print("Against high dealer cards, these hands often hit despite the risk.")
                else:
                    print("Against low dealer cards (2-6), often stand and hope dealer busts.")
            elif player_value == 11:
                print("11 is ideal for doubling - you can't bust and might hit 21.")
        
        # Information based on dealer upcard
        print(f"\nDealer shows: {dealer_upcard} (Value: {dealer_value})")
        if dealer_value >= 7:
            print("High dealer cards (7-A) are strong and less likely to bust.")
            print("You often need stronger hands to beat these cards.")
        elif dealer_value >= 2 and dealer_value <= 6:
            print("Dealer cards 2-6 are weaker, with 5-6 being the weakest.")
            print("With these upcards, the dealer has a higher chance of busting.")
            if dealer_value == 6:
                print("Dealer showing 6 is their weakest position.")
        
        print("\nRemember: Basic strategy is mathematically calculated to minimize the house edge.")

    def play(self):
        """Run the main game loop with enhanced card display."""
        print(f"\nWelcome to {self.table.display_name()}!")
        # Offer table information at the start of a new session
        show_info = input("\nWould you like to see detailed table information before playing? (y/n): ").lower()
        if show_info == 'y':
            self.display_table_info()

        while True:
            print(f"\nBankroll: ${self.profile.bankroll}")
            
            # Check if player has enough money
            if self.profile.bankroll < self.min_bet:
                print("You don't have enough money to play at this table!")
                return
            
            # Place bet
            bet = self.get_bet()
            if bet is None:  # User wants to exit
                return
                
            # Initial deal
            player_hand = [self.deck.deal_card(), self.deck.deal_card()]
            dealer_hand = [self.deck.deal_card(), self.deck.deal_card(face_up=False)]

            # Display hands with ASCII art
            self.display_player_hand(player_hand)
            self.display_dealer_hand([dealer_hand[0]], hide_hole_card=False)  # Just show first card
            
            # Check for blackjacks
            player_blackjack = self.check_blackjack(player_hand)
            dealer_upcard = dealer_hand[0]
            
            # If dealer has an Ace or 10-value card showing, check for blackjack
            if dealer_upcard.value in [10, 11]:
                print("\nDealer checks for blackjack...")
                dealer_blackjack = self.check_blackjack(dealer_hand)
                if dealer_blackjack:
                    print("\n🎴 Dealer has blackjack! 🎴")
                    dealer_hand[1] = self.flip_card(dealer_hand[1])  # Reveal hole card
                    self.display_dealer_hand(dealer_hand)
                    
                    self.session_stats['hands_played'] += 1
                    
                    if player_blackjack:
                        print("\n🎯 You also have blackjack - it's a push! 🎯")
                        self.profile.bankroll += bet  # Return bet
                        self.session_stats['pushes'] += 1
                    else:
                        print("\n❌ You lose. ❌")
                        # Bet already deducted
                        self.session_stats['hands_lost'] += 1
                    
                    # Continue to next round
                    if not self.play_again():
                        return
                    continue
            
            # If player has blackjack, handle it
            if player_blackjack:
                print("\n🎉 Blackjack! You win! 🎉")
                dealer_hand[1] = self.flip_card(dealer_hand[1])  # Reveal hole card
                self.display_dealer_hand(dealer_hand)
                
                # Pay according to specified payout
                if self.blackjack_payout == "3:2":
                    payout = bet * 1.5
                else:  # Assume 6:5
                    payout = bet * 1.2
                    
                print(f"Payout: ${payout:.2f}")
                self.profile.bankroll += (bet + payout)
                
                # Update stats
                self.session_stats['hands_played'] += 1
                self.session_stats['hands_won'] += 1
                self.session_stats['blackjacks'] += 1
                
                # Continue to next round
                if not self.play_again():
                    return
                continue
            
            # Offer basic strategy hint if enabled
            self.display_hint(player_hand, dealer_upcard)
            
            # Regular gameplay
            self.hands_to_compare = []  # Reset split hands tracking
            
            # Player turn
            result = self.player_turn(player_hand, bet, dealer_upcard)
            if result:
                player_hand, bet = result
            
            # Process the hand(s)
            if self.hands_to_compare:
                # Player split their hand
                print("\nDealer's turn...")
                dealer_hand[1] = self.flip_card(dealer_hand[1])  # Reveal hole card
                dealer_total = self.dealer_turn(dealer_hand)
                
                # Compare each split hand to dealer
                for hand, hand_bet in self.hands_to_compare:
                    self.compare_hands(hand, dealer_hand, hand_bet)
            elif player_hand and not self.hand_value(player_hand) > 21:
                # Regular play - player didn't bust
                print("\nDealer's turn...")
                dealer_hand[1] = self.flip_card(dealer_hand[1])  # Reveal hole card
                dealer_total = self.dealer_turn(dealer_hand)
                self.compare_hands(player_hand, dealer_hand, bet)
            elif player_hand:
                # Player busted
                print("\n💥 You bust! 💥")
                dealer_hand[1] = self.flip_card(dealer_hand[1])  # Reveal hole card
                self.display_dealer_hand(dealer_hand)
                print("You lose this hand.")
                
                # Update stats
                self.session_stats['hands_played'] += 1
                self.session_stats['hands_lost'] += 1
                self.session_stats['busts'] += 1
                
                # Bet already deducted
            
            # Check if deck needs reshuffling
            if self.deck.is_cut_card():
                print("\n🔄 Reshuffling the deck... 🔄")
                self.deck.shuffle()
            
            # Ask to play again
            if not self.play_again():
                return

    def get_bet(self):
        """Get a valid bet from the player."""
        while True:
            try:
                bet_input = input(f"Enter your bet (${self.min_bet}-${self.max_bet}) or 'q' to quit: ")
                if bet_input.lower() == 'q':
                    return None
                    
                bet = int(bet_input)
                if self.min_bet <= bet <= self.max_bet and bet <= self.profile.bankroll:
                    self.profile.bankroll -= bet
                    return bet
                else:
                    if bet > self.profile.bankroll:
                        print(f"You only have ${self.profile.bankroll}.")
                    else:
                        print(f"Please enter a bet between ${self.min_bet} and ${self.max_bet}.")
            except ValueError:
                print("Please enter a valid number.")

    def hand_value(self, hand):
        """Calculate the best value of a hand, accounting for aces."""
        value = sum(card.value for card in hand)
        aces = sum(1 for card in hand if card.rank == 'A')
        
        # Adjust for aces if needed
        while value > 21 and aces:
            value -= 10
            aces -= 1
            
        return value

    def check_blackjack(self, hand):
        """Check if a hand is a natural blackjack."""
        return len(hand) == 2 and self.hand_value(hand) == 21

    def player_turn(self, hand, bet, dealer_upcard):
        """
        Process the player's turn with improved display.
        
        Args:
            hand (list): The player's hand
            bet (float): The current bet
            dealer_upcard (Card): The dealer's visible card
            
        Returns:
            tuple: (hand, bet) or None if split
        """
        can_double = True  # Only allow double on first move
        can_split = self.can_split(hand)

        while self.hand_value(hand) < 21:
            # Build available options
            options = "(H)it, (S)tand"
            if can_double:
                options += ", (D)ouble"
            if can_split:
                options += ", S(p)lit"
                
            # Show hints if enabled
            self.display_hint(hand, dealer_upcard)

            move = input(f"\n{options}: ").lower()

            if move == 'h':
                # Hit: receive one more card
                hand.append(self.deck.deal_card())
                print("\nYou hit!")
                self.display_player_hand(hand)
                can_double = False  # Can't double after hitting
                can_split = False   # Can't split after hitting

            elif move == 's':
                # Stand: end turn
                print("\nYou stand.")
                break

            elif move == 'd' and can_double:
                # Double Down: double bet, get one card, then stand
                if self.profile.bankroll >= bet:
                    self.profile.bankroll -= bet
                    bet *= 2
                    hand.append(self.deck.deal_card())
                    print("\n💰 You doubled down! 💰")
                    self.display_player_hand(hand)
                    break
                else:
                    print("Not enough bankroll to double down.")

            elif move == 'p' and can_split:
                # Split: create two hands from a pair
                return self.handle_split(hand, bet, dealer_upcard)

            else:
                print("Invalid option.")

        return hand, bet

    def can_split(self, hand):
        """Check if the player can split (two cards of the same rank)."""
        return len(hand) == 2 and hand[0].rank == hand[1].rank

    def handle_split(self, hand, bet, dealer_upcard):
        """Handle splitting a hand with improved display."""
        if self.profile.bankroll < bet:
            print("Not enough bankroll to split.")
            return hand, bet
            
        print("\n✂️ Splitting your hand! ✂️")

        # Create two new hands
        hand1 = [hand[0], self.deck.deal_card()]
        hand2 = [hand[1], self.deck.deal_card()]

        # Deduct additional bet for second hand
        self.profile.bankroll -= bet
        
        # Initialize hands_to_compare if it's the first split
        if not self.hands_to_compare:
            self.hands_to_compare = []

        # Play each split hand
        for idx, split_hand in enumerate([hand1, hand2], 1):
            print(f"\n🎮 Playing Hand {idx}: 🎮")
            self.display_player_hand(split_hand)
            
            # Play this split hand
            result = self.player_turn(split_hand, bet, dealer_upcard)
            if result:  # If not None (could be None if split again)
                final_hand, final_bet = result
                self.hands_to_compare.append((final_hand, final_bet))

        return None, None  # Split hands will be processed separately

    def dealer_turn(self, hand):
        """Process the dealer's turn with improved display."""
        self.display_dealer_hand(hand)
        
        # Dealer must hit until 17 or higher
        # If dealer_hits_soft_17 is True, dealer must hit on soft 17
        while self.hand_value(hand) < 17 or (self.dealer_hits_soft_17 and self.hand_value(hand) == 17 and self.is_soft_hand(hand)):
            time.sleep(0.8)  # Dramatic pause
            hand.append(self.deck.deal_card())
            print("\nDealer hits:")
            self.display_dealer_hand(hand)
            
        if self.hand_value(hand) <= 21:
            print("\nDealer stands.")
        else:
            print("\n💥 Dealer busts! 💥")
            self.session_stats['dealer_busts'] += 1
            
        return self.hand_value(hand)
        
    def is_soft_hand(self, hand):
        """Check if a hand is soft (contains an ace counted as 11)."""
        value = sum(card.value for card in hand)
        aces = sum(1 for card in hand if card.rank == 'A')
        
        # Calculate value if one ace is counted as 11
        # First count all aces as 1
        alt_value = value - (aces * 10)
        
        # Check if adding back 10 (to make one ace worth 11) keeps us at or below 21
        return aces > 0 and alt_value + 10 <= 21

    def compare_hands(self, player_hand, dealer_hand, bet):
        """Compare hands with improved display."""
        player_value = self.hand_value(player_hand)
        dealer_value = self.hand_value(dealer_hand)

        print("\n🎲 Final Results: 🎲")
        self.display_player_hand(player_hand)
        self.display_dealer_hand(dealer_hand)
        
        # Update hands played stat
        self.session_stats['hands_played'] += 1

        # Player already busted
        if player_value > 21:
            print("\n💥 You bust! You lose. 💥")
            self.session_stats['hands_lost'] += 1
            self.session_stats['busts'] += 1
            # Bet is already deducted
            return
            
        # Dealer busted
        if dealer_value > 21:
            print("\n🎉 Dealer busts! You win! 🎉")
            self.profile.bankroll += (bet * 2)  # Return bet plus winnings
            self.session_stats['hands_won'] += 1
            return
            
        # Compare hands
        if player_value > dealer_value:
            print("\n🏆 You win! 🏆")
            self.profile.bankroll += (bet * 2)  # Return bet plus winnings
            self.session_stats['hands_won'] += 1
        elif dealer_value > player_value:
            print("\n❌ Dealer wins. You lose. ❌")
            self.session_stats['hands_lost'] += 1
            # Bet is already deducted
        else:
            print("\n🔄 Push! It's a tie. 🔄")
            self.profile.bankroll += bet  # Return the bet
            self.session_stats['pushes'] += 1

    def flip_card(self, card):
        """
        Flip a face-down card to face-up and update the running count.
        
        Args:
            card (Card): The card to flip
            
        Returns:
            Card: The same card, now counted
        """
        # Update the running count
        self.deck.running_count += card.get_count_value()
        return card
        
    def play_again(self):
        """Ask if the player wants to play another hand."""
        # Occasionally show session stats
        if random.random() < 0.2 and self.session_stats['hands_played'] > 0:
            self.display_session_stats()
            
        again = input("\nPlay another hand? (y/n): ").lower()
        return again == 'y'
        
    def display_session_stats(self):
        """Display statistics for the current session."""
        if self.session_stats['hands_played'] == 0:
            return
            
        print("\n📊 Session Statistics 📊")
        print(f"Hands Played: {self.session_stats['hands_played']}")
        
        # Calculate win percentage
        if self.session_stats['hands_played'] > 0:
            win_rate = (self.session_stats['hands_won'] / self.session_stats['hands_played']) * 100
            print(f"Win Rate: {win_rate:.1f}%")
        
        print(f"Wins: {self.session_stats['hands_won']}")
        print(f"Losses: {self.session_stats['hands_lost']}")
        print(f"Pushes: {self.session_stats['pushes']}")
        
        # Show specialized stats
        if self.session_stats['blackjacks'] > 0:
            print(f"Blackjacks: {self.session_stats['blackjacks']}")
        if self.session_stats['busts'] > 0:
            print(f"Times Busted: {self.session_stats['busts']}")
        if self.session_stats['dealer_busts'] > 0:
            print(f"Dealer Busts: {self.session_stats['dealer_busts']}")

    def display_table_info(self):
        """Display detailed information about the current table including house edge."""
        print(f"\n{'=' * 50}")
        print(f"🎲 {self.table.display_name()} 🎲")
        print(f"{'=' * 50}")
        
        print(f"\n{self.table.description}\n")
        
        # Display key rules
        print("📋 Table Rules:")
        print(f"• Decks: {self.table.rules.get('number_of_decks', 6)}")
        print(f"• Blackjack payout: {self.table.rules.get('blackjack_payout', '3:2')}")
        print(f"• Dealer hits soft 17: {'Yes' if self.table.rules.get('dealer_hits_soft_17', False) else 'No'}")
        print(f"• Doubling down allowed: {'Yes' if self.table.rules.get('allow_double_down', True) else 'No'}")
        print(f"• Splitting allowed: {'Yes' if self.table.rules.get('allow_split', True) else 'No'}")
        print(f"• Double after split: {'Yes' if self.table.rules.get('allow_double_after_split', True) else 'No'}")
        print(f"• Surrender allowed: {'Yes' if self.table.rules.get('allow_surrender', False) else 'No'}")
        
        # Display house edge if enabled
        if self.table.show_house_edge and self.table.house_edge is not None:
            print(f"\n📊 House Edge: {self.table.house_edge:.2f}%")
            
            # Ask if player wants detailed breakdown
            show_breakdown = input("\nWould you like to see a detailed house edge breakdown? (y/n): ").lower()
            
            if show_breakdown == 'y':
                self.display_house_edge_breakdown()
        
        print(f"\n{'=' * 50}")

    def display_house_edge_breakdown(self):
        """Display a detailed breakdown of how the house edge is calculated."""
        breakdown = self.table.get_house_edge_breakdown()
        
        print("\n📈 House Edge Breakdown 📉")
        print(f"Starting baseline: +{breakdown['base_edge']:.2f}% (Perfect basic strategy)")
        
        # Group factors by whether they increase or decrease house edge
        favorable = []
        unfavorable = []
        
        for factor in breakdown['factors']:
            if factor['impact'] < 0:
                favorable.append(factor)
            else:
                unfavorable.append(factor)
        
        # Display favorable rules
        if favorable:
            print("\n✅ Rules in your favor:")
            for factor in favorable:
                print(f"• {factor['name']}: {factor['impact']:.2f}%")
        
        # Display unfavorable rules
        if unfavorable:
            print("\n❌ Rules against you:")
            for factor in unfavorable:
                print(f"• {factor['name']}: +{factor['impact']:.2f}%")
        
        # Display total
        print(f"\nTotal house edge: {breakdown['total_edge']:.2f}%")
        
        # Display interpretation
        if breakdown['total_edge'] < 0.5:
            print("This is an excellent table with very favorable rules!")
        elif breakdown['total_edge'] < 1.0:
            print("This is a good table with player-friendly rules.")
        elif breakdown['total_edge'] < 2.0:
            print("This is an average table with standard casino rules.")
        else:
            print("This table has a high house edge. Consider finding better rules.")
        
        # Add strategy advice
        print("\n💡 Remember: Using perfect basic strategy is essential to achieve this house edge!")
