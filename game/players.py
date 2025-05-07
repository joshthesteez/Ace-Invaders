# blackjack_game/players.py
# Consolidated from player.py, dealer.py, and strategy_helper.py

from blackjack_game.settings import SETTINGS, PLAYER_SETTINGS, DEALER_SETTINGS

#################################################
# Hand Class Definition
#################################################
class Hand:
    """
    Represents a blackjack hand.
    
    Attributes:
        cards (list): List of Card objects in the hand
        bet (float): Current bet amount for this hand
        is_split (bool): Whether this hand was created from a split
        is_doubled (bool): Whether this hand has been doubled down
        is_surrendered (bool): Whether this hand has been surrendered
    """
    
    def __init__(self, bet=0.0):
        self.cards = []
        self.bet = bet
        self.is_split = False
        self.is_doubled = False
        self.is_surrendered = False
    
    def add_card(self, card):
        """Add a card to the hand."""
        self.cards.append(card)
    
    def get_value(self):
        """
        Calculate the current value of the hand, handling aces optimally.
        
        Returns:
            int: The best possible hand value
        """
        value = 0
        aces = 0
        
        # First pass: count non-aces and track ace count
        for card in self.cards:
            if card.rank == 'A':
                aces += 1
            else:
                value += card.value
        
        # Handle aces optimally
        for _ in range(aces):
            # If adding 11 would bust or exceed 21, add 1 instead
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
        
        return value
    
    def is_busted(self):
        """Check if the hand value exceeds 21."""
        return self.get_value() > 21
    
    def is_blackjack(self):
        """
        Check if the hand is a natural blackjack (21 with exactly 2 cards).
        
        Returns:
            bool: True if the hand is a blackjack, False otherwise
        """
        return len(self.cards) == 2 and self.get_value() == 21
    
    def is_soft(self):
        """
        Check if the hand is a soft hand (contains an ace counted as 11).
        
        Returns:
            bool: True if the hand is soft, False otherwise
        """
        value = 0
        aces = 0
        
        # Count non-ace cards first
        for card in self.cards:
            if card.rank == 'A':
                aces += 1
            else:
                value += card.value
        
        # If we can add 11 for at least one ace without busting, it's a soft hand
        return aces > 0 and value + 11 <= 21
    
    def is_pair(self):
        """
        Check if the hand is a pair (exactly 2 cards of the same rank).
        
        Returns:
            bool: True if the hand is a pair, False otherwise
        """
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank
    
    def __str__(self):
        """String representation of the hand."""
        card_str = ', '.join(str(card) for card in self.cards)
        return f"Hand: {card_str} (Value: {self.get_value()})"


#################################################
# Player Class Definition
#################################################
class Player:
    """
    Represents a blackjack player.
    
    Attributes:
        name (str): Player name
        bankroll (float): Current money balance
        hands (list): List of Hand objects (for splits)
        current_hand_index (int): Index of the current hand being played
        stats (dict): Dictionary of player statistics
    """
    
    def __init__(self, name="Player", bankroll=None):
        self.name = name
        
        # Initialize bankroll from settings or use default
        if bankroll is None:
            self.bankroll = PLAYER_SETTINGS.get('INITIAL_BANKROLL', 1000.0)
        else:
            self.bankroll = bankroll
            
        self.hands = []
        self.current_hand_index = 0
        
        # Initialize player statistics
        self.stats = {
            'hands_played': 0,
            'hands_won': 0,
            'hands_lost': 0,
            'hands_pushed': 0,
            'blackjacks': 0,
            'busts': 0,
            'splits': 0,
            'doubles': 0,
            'surrenders': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'current_streak': 0,
            'longest_win_streak': 0,
            'longest_loss_streak': 0,
        }
    
    def place_bet(self, amount):
        """
        Place a bet and create a new hand.
        
        Args:
            amount (float): The bet amount
            
        Returns:
            Hand: The newly created hand
            
        Raises:
            ValueError: If bet amount is invalid or player doesn't have enough money
        """
        min_bet = PLAYER_SETTINGS.get('MIN_BET', 1)
        max_bet = PLAYER_SETTINGS.get('MAX_BET', 1000)
        
        # Validate bet amount
        if amount < min_bet:
            raise ValueError(f"Bet must be at least {min_bet}")
        if amount > max_bet:
            raise ValueError(f"Bet cannot exceed {max_bet}")
        if amount > self.bankroll:
            raise ValueError(f"Not enough funds. Current bankroll: {self.bankroll}")
        
        # Create a new hand with the bet
        hand = Hand(bet=amount)
        self.hands.append(hand)
        
        # Deduct bet from bankroll
        self.bankroll -= amount
        
        return hand
    
    def hit(self, hand_index=None):
        """
        Prepare to receive a card for the specified hand.
        
        Args:
            hand_index (int, optional): Index of the hand to hit. Defaults to current hand.
            
        Returns:
            Hand: The hand that will receive the card
        """
        if hand_index is None:
            hand_index = self.current_hand_index
            
        if hand_index < 0 or hand_index >= len(self.hands):
            raise ValueError(f"Invalid hand index: {hand_index}")
            
        return self.hands[hand_index]
    
    def stand(self, hand_index=None):
        """
        Stand on the specified hand.
        
        Args:
            hand_index (int, optional): Index of the hand to stand. Defaults to current hand.
            
        Returns:
            bool: True if there are more hands to play, False otherwise
        """
        if hand_index is None:
            hand_index = self.current_hand_index
            
        if hand_index < 0 or hand_index >= len(self.hands):
            raise ValueError(f"Invalid hand index: {hand_index}")
        
        # If this is the current hand, move to the next one
        if hand_index == self.current_hand_index:
            self.current_hand_index += 1
            
        # Return whether there are more hands to play
        return self.current_hand_index < len(self.hands)
    
    def double_down(self, hand_index=None):
        """
        Double down on the specified hand.
        
        Args:
            hand_index (int, optional): Index of the hand to double down. Defaults to current hand.
            
        Returns:
            Hand: The hand that was doubled down
            
        Raises:
            ValueError: If double down is not allowed or player doesn't have enough money
        """
        if hand_index is None:
            hand_index = self.current_hand_index
            
        if hand_index < 0 or hand_index >= len(self.hands):
            raise ValueError(f"Invalid hand index: {hand_index}")
            
        hand = self.hands[hand_index]
        
        # Check if hand is eligible for doubling down (only allowed on first two cards)
        if len(hand.cards) != 2:
            raise ValueError("Double down only allowed on initial two cards")
            
        # Check if player has enough money
        if hand.bet > self.bankroll:
            raise ValueError(f"Not enough funds to double down. Current bankroll: {self.bankroll}")
            
        # Double the bet
        self.bankroll -= hand.bet
        hand.bet *= 2
        hand.is_doubled = True
        
        # Update stats
        self.stats['doubles'] += 1
        
        return hand
    
    def split(self, hand_index=None):
        """
        Split the specified hand.
        
        Args:
            hand_index (int, optional): Index of the hand to split. Defaults to current hand.
            
        Returns:
            list: The two hands created from the split
            
        Raises:
            ValueError: If split is not allowed or player doesn't have enough money
        """
        if hand_index is None:
            hand_index = self.current_hand_index
            
        if hand_index < 0 or hand_index >= len(self.hands):
            raise ValueError(f"Invalid hand index: {hand_index}")
            
        hand = self.hands[hand_index]
        
        # Check if hand is eligible for splitting
        if not hand.is_pair():
            raise ValueError("Can only split a pair")
            
        # Check if player has enough money
        if hand.bet > self.bankroll:
            raise ValueError(f"Not enough funds to split. Current bankroll: {self.bankroll}")
            
        # Create new hand with the second card
        new_hand = Hand(bet=hand.bet)
        new_hand.is_split = True
        new_hand.add_card(hand.cards.pop())
        
        # Update the original hand
        hand.is_split = True
        
        # Deduct additional bet
        self.bankroll -= hand.bet
        
        # Add new hand to the player's hands
        self.hands.insert(hand_index + 1, new_hand)
        
        # Update stats
        self.stats['splits'] += 1
        
        return [hand, new_hand]
    
    def get_current_hand(self):
        """
        Get the current hand being played.
        
        Returns:
            Hand: The current hand or None if no hands
        """
        if not self.hands or self.current_hand_index >= len(self.hands):
            return None
        return self.hands[self.current_hand_index]
    
    def clear_hands(self):
        """Clear all hands and reset current hand index."""
        self.hands = []
        self.current_hand_index = 0
    
    def __str__(self):
        """String representation of the player."""
        return f"{self.name} (Bankroll: ${self.bankroll:.2f})"


#################################################
# Dealer Class Definition
#################################################
class Dealer:
    """
    Represents the dealer in blackjack.
    
    Attributes:
        hand (list): The dealer's hand of cards
        hit_on_soft_17 (bool): Whether the dealer hits on soft 17
        stand_on_hard_17 (bool): Whether the dealer stands on hard 17
        hide_hole_card (bool): Whether the dealer's second card is hidden
    """
    
    def __init__(self):
        self.hand = []
        self.hit_on_soft_17 = DEALER_SETTINGS.get('DEALER_HIT_ON_SOFT_17', False)
        self.stand_on_hard_17 = DEALER_SETTINGS.get('DEALER_STAND_ON_HARD_17', True) 
        self.hide_hole_card = True
    
    def receive_card(self, card):
        """Add a card to the dealer's hand."""
        self.hand.append(card)
    
    def reset_hand(self):
        """Clear the dealer's hand and reset hole card visibility."""
        self.hand = []
        self.hide_hole_card = True
    
    def reveal_hand(self):
        """Show the dealer's hole card."""
        self.hide_hole_card = False
    
    def get_visible_card(self):
        """Get the dealer's face-up card (first card)."""
        return self.hand[0] if self.hand else None
    
    def get_hand_value(self):
        """Calculate the value of the dealer's hand."""
        total = 0
        aces = 0
        
        for card in self.hand:
            if card.rank == 'A':
                aces += 1
            total += card.value
            
        # Adjust for aces if needed
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
            
        return total
    
    def should_hit(self):
        """Determine if the dealer should hit based on rules."""
        value = self.get_hand_value()
        
        # Always hit if less than 17
        if value < 17:
            return True
        
        # Soft 17 logic
        if value == 17 and self.hit_on_soft_17:
            # Check if it's a soft 17 (contains an ace counted as 11)
            return self._is_soft_hand()
            
        return False
    
    def _is_soft_hand(self):
        """Check if the dealer's hand is soft (contains an ace counted as 11)."""
        # Make sure we have an ace
        has_ace = any(card.rank == 'A' for card in self.hand)
        if not has_ace:
            return False
            
        # Calculate value without any aces being 11
        non_ace_value = sum(card.value for card in self.hand if card.rank != 'A')
        ace_count = sum(1 for card in self.hand if card.rank == 'A')
        
        # If we can add 11 for at least one ace and still be ≤ 21, it's a soft hand
        return non_ace_value + ace_count + 10 <= 21
    
    def play(self, deck):
        """
        Automatically play the dealer's hand according to house rules.
        
        Args:
            deck (Deck): The deck to draw cards from
        """
        self.reveal_hand()
        
        while self.should_hit():
            self.receive_card(deck.deal_card())
            
        # Return final hand value for convenience
        return self.get_hand_value()
        
    def __str__(self):
        """String representation of the dealer's hand."""
        if self.hide_hole_card and len(self.hand) > 1:
            return f"Dealer shows: {self.hand[0]}"
        else:
            card_str = ', '.join(str(card) for card in self.hand)
            return f"Dealer's hand: {card_str} (Value: {self.get_hand_value()})"


#################################################
# Strategy Helper Functions
#################################################

def get_basic_strategy_move(player_hand, dealer_upcard):
    """
    Returns the optimal basic strategy move for the given hand and dealer upcard.
    
    Args:
        player_hand (list): The player's hand
        dealer_upcard (Card): The dealer's visible card
        
    Returns:
        str: One of 'hit', 'stand', 'double', 'split', 'surrender'
    """
    # Get hand value and check if it's a soft hand (contains an ace counted as 11)
    hand_value = sum(card.value for card in player_hand)
    aces = sum(1 for card in player_hand if card.rank == 'A')
    
    # Adjust for aces if needed
    while hand_value > 21 and aces > 0:
        hand_value -= 10
        aces -= 1
        
    is_soft = aces > 0 and hand_value <= 21
    
    # Check if it's a pair (two cards of the same rank)
    is_pair = len(player_hand) == 2 and player_hand[0].rank == player_hand[1].rank
    
    # Get dealer upcard value
    dealer_value = dealer_upcard.value
    
    # Handle pairs first
    if is_pair:
        pair_rank = player_hand[0].rank
        
        # Pairs strategy
        if pair_rank == 'A' or pair_rank == '8':
            return 'split'  # Always split aces and 8s
        elif pair_rank == '10' or pair_rank == 'J' or pair_rank == 'Q' or pair_rank == 'K':
            return 'stand'  # Never split 10s
        elif pair_rank == '9':
            # Split 9s against 2-6, 8-9, stand against 7, 10, A
            if dealer_value in [2, 3, 4, 5, 6, 8, 9]:
                return 'split'
            else:
                return 'stand'
        elif pair_rank == '7':
            # Split 7s against 2-7, hit against 8-A
            if dealer_value in [2, 3, 4, 5, 6, 7]:
                return 'split'
            else:
                return 'hit'
        elif pair_rank == '6':
            # Split 6s against 2-6, hit against 7-A
            if dealer_value in [2, 3, 4, 5, 6]:
                return 'split'
            else:
                return 'hit'
        elif pair_rank == '5':
            # Double 5s against 2-9, hit against 10-A
            if dealer_value in [2, 3, 4, 5, 6, 7, 8, 9] and len(player_hand) == 2:
                return 'double'
            else:
                return 'hit'
        elif pair_rank == '4':
            # Split 4s against 5-6, hit against everything else
            if dealer_value in [5, 6]:
                return 'split'
            else:
                return 'hit'
        elif pair_rank == '3' or pair_rank == '2':
            # Split 2s and 3s against 2-7, hit against 8-A
            if dealer_value in [2, 3, 4, 5, 6, 7]:
                return 'split'
            else:
                return 'hit'
    
    # Handle soft hands (contains an ace counted as 11)
    if is_soft:
        if hand_value >= 19:
            return 'stand'  # Always stand on soft 19 or higher
        elif hand_value == 18:
            # Stand on soft 18 against 2-8, hit against 9-A
            if dealer_value in [2, 3, 4, 5, 6, 7, 8]:
                return 'stand'
            else:
                return 'hit'
        elif hand_value == 17:
            # Double on soft 17 against 3-6, hit against everything else
            if dealer_value in [3, 4, 5, 6] and len(player_hand) == 2:
                return 'double'
            else:
                return 'hit'
        elif hand_value == 16 or hand_value == 15:
            # Double on soft 15-16 against 4-6, hit against everything else
            if dealer_value in [4, 5, 6] and len(player_hand) == 2:
                return 'double'
            else:
                return 'hit'
        elif hand_value == 14 or hand_value == 13:
            # Double on soft 13-14 against 5-6, hit against everything else
            if dealer_value in [5, 6] and len(player_hand) == 2:
                return 'double'
            else:
                return 'hit'
        else:
            return 'hit'  # Always hit on soft 12 or lower
    
    # Handle hard hands
    if hand_value >= 17:
        return 'stand'  # Always stand on hard 17 or higher
    elif hand_value >= 13 and hand_value <= 16:
        # Stand on hard 13-16 against 2-6, hit against 7-A
        if dealer_value in [2, 3, 4, 5, 6]:
            return 'stand'
        else:
            return 'hit'
    elif hand_value == 12:
        # Stand on hard 12 against 4-6, hit against everything else
        if dealer_value in [4, 5, 6]:
            return 'stand'
        else:
            return 'hit'
    elif hand_value == 11:
        # Always double on hard 11 if possible, otherwise hit
        if len(player_hand) == 2:
            return 'double'
        else:
            return 'hit'
    elif hand_value == 10:
        # Double on hard 10 against 2-9, hit against 10-A
        if dealer_value in [2, 3, 4, 5, 6, 7, 8, 9] and len(player_hand) == 2:
            return 'double'
        else:
            return 'hit'
    elif hand_value == 9:
        # Double on hard 9 against 3-6, hit against everything else
        if dealer_value in [3, 4, 5, 6] and len(player_hand) == 2:
            return 'double'
        else:
            return 'hit'
    else:
        return 'hit'  # Always hit on hard 8 or lower