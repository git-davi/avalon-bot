"""AI player logic for The Resistance: Avalon Discord Bot."""

import random
from .game import AvalonGame, Player

class AIPlayer:
    """Represents an AI player that can make decisions."""

    def __init__(self, game: AvalonGame, player: Player):
        self.game = game
        self.player = player

    def decide_team_proposal(self) -> bool:
        """Decide whether to approve or reject a team proposal."""
        # Good players generally approve teams unless they have reason to suspect evil
        # Evil players try to get on teams or block good teams
        if self.player.is_good():
            # Good players: mostly approve, but sometimes reject randomly to add uncertainty
            return random.choice([True, True, True, False])  # 75% approve
        else:
            # Evil players: approve if they're on the team, otherwise 50/50
            if self.player.user_id in self.game.proposed_team:
                return True  # Always approve if on the team
            else:
                return random.choice([True, False])  # 50/50 otherwise

    def decide_mission_vote(self) -> bool:
        """Decide whether to succeed or fail a mission."""
        # Evil players will always fail the mission, good players will always succeed.
        return self.player.is_good()

    def decide_assassination_target(self) -> int:
        """Decide who to assassinate."""
        # Randomly select a good player to assassinate.
        good_players = [p for p in self.game.players if p.is_good()]
        return random.choice(good_players).user_id
