# blackjack_game/profile_manager.py
# Profile management functionality moved from the profiles/ directory

import json
import os

class PlayerProfile:
    """
    Player profile containing game progress and statistics.
    
    Attributes:
        name (str): Player name
        bankroll (float): Player's current money
        xp (int): Experience points
        stats (dict): Game statistics
    """
    def __init__(self, name, bankroll=1000, xp=0, stats=None):
        self.name = name
        self.bankroll = bankroll
        self.xp = xp
        self.stats = stats if stats is not None else {
            "hands_played": 0,
            "wins": 0,
            "losses": 0,
            "blackjacks": 0,
            "splits": 0,
            "doubles": 0
        }

    def to_dict(self):
        """Convert profile to dictionary for saving."""
        return {
            "name": self.name,
            "bankroll": self.bankroll,
            "xp": self.xp,
            "stats": self.stats
        }

    @staticmethod
    def from_dict(data):
        """Create profile from dictionary data."""
        return PlayerProfile(
            name=data["name"],
            bankroll=data.get("bankroll", 1000),
            xp=data.get("xp", 0),
            stats=data.get("stats", {})
        )


class ProfileManager:
    """
    Manages saving and loading player profiles.
    """
    def __init__(self, save_folder="profiles/saves"):
        self.save_folder = save_folder
        os.makedirs(self.save_folder, exist_ok=True)

    def save_profile(self, profile):
        """Save a profile to disk."""
        filepath = os.path.join(self.save_folder, f"{profile.name}.json")
        with open(filepath, 'w') as f:
            json.dump(profile.to_dict(), f, indent=4)

    def load_profile(self, name):
        """Load a profile from disk."""
        filepath = os.path.join(self.save_folder, f"{name}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                return PlayerProfile.from_dict(data)
        return None

    def list_profiles(self):
        """List all available profiles."""
        return [f[:-5] for f in os.listdir(self.save_folder) if f.endswith('.json')]

    def create_profile(self, name, starting_bankroll=1000):
        """Create a new profile."""
        profile = PlayerProfile(name=name, bankroll=starting_bankroll)
        self.save_profile(profile)
        return profile