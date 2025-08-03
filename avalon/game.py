"""Game logic for The Resistance: Avalon Discord Bot."""

import random
from enum import Enum
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from .config import PLAYER_COUNTS, MISSION_SIZES, TWO_FAIL_MISSIONS, ROLES


class GameState(Enum):
    LOBBY = "lobby"
    ROLE_ASSIGNMENT = "role_assignment"
    TEAM_PROPOSAL = "team_proposal" 
    TEAM_VOTING = "team_voting"
    MISSION = "mission"
    ASSASSINATION = "assassination"
    FINISHED = "finished"


class MissionResult(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAIL = "fail"


@dataclass
class Player:
    """Represents a player in the game."""
    user_id: int
    username: str
    role: Optional[str] = None
    team: Optional[str] = None
    
    def is_evil(self) -> bool:
        return self.team == "evil"
    
    def is_good(self) -> bool:
        return self.team == "good"


class AvalonGame:
    """Main game state management for Avalon."""
    
    def __init__(self, channel_id: int, host_id: int):
        self.channel_id = channel_id
        self.host_id = host_id
        self.players: List[Player] = []
        self.state = GameState.LOBBY
        
        # Game state
        self.current_round = 1
        self.current_leader_index = 0
        self.vote_track = 0  # Number of consecutive rejected proposals
        self.missions: List[MissionResult] = [MissionResult.PENDING] * 5
        
        # Current round state
        self.proposed_team: List[int] = []  # Player user_ids
        self.team_votes: Dict[int, bool] = {}  # user_id -> approve/reject
        self.mission_votes: Dict[int, bool] = {}  # user_id -> success/fail
        
        # Role information
        self.roles_assigned: Dict[int, str] = {}  # user_id -> role
        self.merlin_id: Optional[int] = None
        self.assassin_id: Optional[int] = None
        
    def add_player(self, user_id: int, username: str) -> bool:
        """Add a player to the game. Returns True if successful."""
        if len(self.players) >= 10:
            return False
        if user_id in [p.user_id for p in self.players]:
            return False
        
        self.players.append(Player(user_id, username))
        return True
    
    def remove_player(self, user_id: int) -> bool:
        """Remove a player from the game. Returns True if successful."""
        if self.state != GameState.LOBBY:
            return False
        
        self.players = [p for p in self.players if p.user_id != user_id]
        return True
    
    def can_start_game(self) -> bool:
        """Check if the game can start (5-10 players)."""
        return 5 <= len(self.players) <= 10
    
    def assign_roles(self) -> None:
        """Randomly assign roles to all players."""
        if not self.can_start_game():
            raise ValueError("Cannot assign roles: invalid player count")
        
        player_count = len(self.players)
        good_count = PLAYER_COUNTS[player_count]["good"]
        evil_count = PLAYER_COUNTS[player_count]["evil"]
        
        # Shuffle players for random role assignment
        shuffled_players = self.players.copy()
        random.shuffle(shuffled_players)
        
        # Assign core roles first
        roles_to_assign = []
        
        # Always include Merlin and Assassin
        roles_to_assign.extend(["MERLIN", "ASSASSIN"])
        
        # Add other special roles based on player count
        if player_count >= 7:
            roles_to_assign.extend(["PERCIVAL", "MORGANA"])
        if player_count >= 8:
            roles_to_assign.append("MORDRED")
        
        # Fill remaining slots
        remaining_good = good_count - len([r for r in roles_to_assign if ROLES[r]["team"] == "good"])
        remaining_evil = evil_count - len([r for r in roles_to_assign if ROLES[r]["team"] == "evil"])
        
        roles_to_assign.extend(["SERVANT"] * remaining_good)
        roles_to_assign.extend(["MINION"] * remaining_evil)
        
        # Assign roles to players
        for i, player in enumerate(shuffled_players):
            role = roles_to_assign[i]
            player.role = role
            player.team = ROLES[role]["team"]
            self.roles_assigned[player.user_id] = role
            
            if role == "MERLIN":
                self.merlin_id = player.user_id
            elif role == "ASSASSIN":
                self.assassin_id = player.user_id
        
        self.state = GameState.TEAM_PROPOSAL
    
    def get_current_leader(self) -> Player:
        """Get the current leader."""
        return self.players[self.current_leader_index]
    
    def get_mission_size(self) -> int:
        """Get the required team size for the current mission."""
        return MISSION_SIZES[len(self.players)][self.current_round - 1]
    
    def propose_team(self, leader_id: int, team_user_ids: List[int]) -> bool:
        """Propose a team for the current mission."""
        if self.state != GameState.TEAM_PROPOSAL:
            return False
        if self.get_current_leader().user_id != leader_id:
            return False
        if len(team_user_ids) != self.get_mission_size():
            return False
        if not all(uid in [p.user_id for p in self.players] for uid in team_user_ids):
            return False
        
        self.proposed_team = team_user_ids
        self.team_votes.clear()
        self.state = GameState.TEAM_VOTING
        return True
    
    def vote_team(self, user_id: int, approve: bool) -> bool:
        """Vote on the proposed team."""
        if self.state != GameState.TEAM_VOTING:
            return False
        if user_id not in [p.user_id for p in self.players]:
            return False
        
        self.team_votes[user_id] = approve
        
        # Check if all votes are in
        if len(self.team_votes) == len(self.players):
            self._process_team_vote()
        
        return True
    
    def _process_team_vote(self) -> None:
        """Process the team vote results."""
        approvals = sum(1 for vote in self.team_votes.values() if vote)
        majority = (len(self.players) // 2) + 1
        
        if approvals >= majority:
            # Team approved, start mission
            self.vote_track = 0
            self.mission_votes.clear()
            self.state = GameState.MISSION
        else:
            # Team rejected
            self.vote_track += 1
            self.proposed_team.clear()
            
            if self.vote_track >= 5:
                # Evil wins by vote track
                self.state = GameState.FINISHED
            else:
                # Move to next leader
                self.current_leader_index = (self.current_leader_index + 1) % len(self.players)
                self.state = GameState.TEAM_PROPOSAL
    
    def vote_mission(self, user_id: int, success: bool) -> bool:
        """Vote on the mission (success/fail)."""
        if self.state != GameState.MISSION:
            return False
        if user_id not in self.proposed_team:
            return False
        
        # Only evil players can vote fail
        player = next(p for p in self.players if p.user_id == user_id)
        if not success and player.is_good():
            return False
        
        self.mission_votes[user_id] = success
        
        # Check if all mission votes are in
        if len(self.mission_votes) == len(self.proposed_team):
            self._process_mission_vote()
        
        return True
    
    def _process_mission_vote(self) -> None:
        """Process the mission vote results."""
        fails = sum(1 for vote in self.mission_votes.values() if not vote)
        
        # Check if mission requires 2 fails
        requires_two_fails = (
            len(self.players) in TWO_FAIL_MISSIONS and 
            (self.current_round - 1) in TWO_FAIL_MISSIONS[len(self.players)]
        )
        
        mission_failed = fails >= (2 if requires_two_fails else 1)
        
        # Update mission results
        self.missions[self.current_round - 1] = (
            MissionResult.FAIL if mission_failed else MissionResult.SUCCESS
        )
        
        # Check win conditions
        good_wins = sum(1 for m in self.missions if m == MissionResult.SUCCESS) >= 3
        evil_wins = sum(1 for m in self.missions if m == MissionResult.FAIL) >= 3
        
        if good_wins:
            # Good team succeeded, move to assassination phase
            self.state = GameState.ASSASSINATION
        elif evil_wins:
            # Evil team wins
            self.state = GameState.FINISHED
        else:
            # Continue to next round
            self.current_round += 1
            self.current_leader_index = (self.current_leader_index + 1) % len(self.players)
            self.proposed_team.clear()
            self.state = GameState.TEAM_PROPOSAL
    
    def assassinate(self, assassin_id: int, target_id: int) -> bool:
        """Attempt to assassinate Merlin."""
        if self.state != GameState.ASSASSINATION:
            return False
        if assassin_id != self.assassin_id:
            return False
        if target_id not in [p.user_id for p in self.players]:
            return False
        
        # Check if the assassin correctly identified Merlin
        if target_id == self.merlin_id:
            # Evil wins by assassination
            pass
        else:
            # Good wins (assassination failed)
            pass
        
        self.state = GameState.FINISHED
        return True
    
    def get_role_info_for_player(self, user_id: int) -> Dict:
        """Get role information that should be sent to a specific player."""
        player = next((p for p in self.players if p.user_id == user_id), None)
        if not player or not player.role:
            return {}
        
        info = {
            "role": player.role,
            "description": ROLES[player.role]["description"],
            "team": player.team
        }
        
        # Add role-specific information
        if player.role == "MERLIN":
            # Merlin sees all evil players except Mordred
            evil_players = []
            for p in self.players:
                if p.is_evil() and p.role != "MORDRED":
                    evil_players.append(p.username)
            info["known_evil"] = evil_players
            
        elif player.role == "PERCIVAL":
            # Percival sees Merlin and Morgana
            merlin_morgana = []
            for p in self.players:
                if p.role in ["MERLIN", "MORGANA"]:
                    merlin_morgana.append(p.username)
            random.shuffle(merlin_morgana)  # Randomize order
            info["merlin_morgana"] = merlin_morgana
            
        elif player.is_evil():
            # Evil players see their fellow evil players
            evil_teammates = []
            for p in self.players:
                if p.is_evil() and p.user_id != user_id:
                    evil_teammates.append(f"{p.username} ({ROLES[p.role]['name']})")
            info["evil_teammates"] = evil_teammates
        
        return info
    
    def get_game_winner(self) -> Optional[str]:
        """Get the winning team, if any."""
        if self.state != GameState.FINISHED:
            return None
        
        # Check mission track
        good_missions = sum(1 for m in self.missions if m == MissionResult.SUCCESS)
        evil_missions = sum(1 for m in self.missions if m == MissionResult.FAIL)
        
        if evil_missions >= 3:
            return "evil"
        elif self.vote_track >= 5:
            return "evil"
        elif good_missions >= 3:
            # Need to check if assassination happened
            return "good"  # This will be overridden if Merlin was assassinated
        
        return None
    
    def is_assassination_successful(self, target_id: int) -> bool:
        """Check if the assassination was successful."""
        return target_id == self.merlin_id