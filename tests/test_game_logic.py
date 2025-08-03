#!/usr/bin/env python3
"""
Test script for Avalon game logic without Discord.
This allows you to test the core game mechanics quickly.
"""

import random
import sys
import os

# Add the parent directory to the path to import avalon package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from avalon.game import AvalonGame, GameState
from avalon.config import ROLES

def print_separator(title=""):
    """Print a nice separator for test output."""
    print("=" * 60)
    if title:
        print(f" {title} ".center(60, "="))
        print("=" * 60)

def test_role_assignment():
    """Test role assignment for different player counts."""
    print_separator("TESTING ROLE ASSIGNMENT")
    
    for player_count in [5, 6, 7, 8, 9, 10]:
        print(f"\n--- Testing with {player_count} players ---")
        
        # Create game and add players
        game = AvalonGame(12345, 1)
        for i in range(player_count):
            game.add_player(100 + i, f"Player{i+1}")
        
        # Assign roles
        game.assign_roles()
        
        # Display results
        good_players = [p for p in game.players if p.team == "good"]
        evil_players = [p for p in game.players if p.team == "evil"]
        
        print(f"Good players ({len(good_players)}): {[f'{p.username}({ROLES[p.role]['name']})' for p in good_players]}")
        print(f"Evil players ({len(evil_players)}): {[f'{p.username}({ROLES[p.role]['name']})' for p in evil_players]}")
        
        # Test role information
        merlin_player = next((p for p in game.players if p.role == "MERLIN"), None)
        if merlin_player:
            merlin_info = game.get_role_info_for_player(merlin_player.user_id)
            print(f"Merlin sees: {merlin_info.get('known_evil', [])}")

def test_team_proposal_and_voting():
    """Test team proposal and voting mechanics."""
    print_separator("TESTING TEAM PROPOSAL & VOTING")
    
    # Create a 7-player game
    game = AvalonGame(12345, 1)
    for i in range(7):
        game.add_player(100 + i, f"Player{i+1}")
    
    game.assign_roles()
    print(f"Game state: {game.state}")
    print(f"Current leader: {game.get_current_leader().username}")
    print(f"Required team size: {game.get_mission_size()}")
    
    # Test team proposal
    leader_id = game.get_current_leader().user_id
    team_size = game.get_mission_size()
    proposed_team = [p.user_id for p in game.players[:team_size]]
    
    success = game.propose_team(leader_id, proposed_team)
    print(f"Team proposal success: {success}")
    print(f"Proposed team: {[next(p.username for p in game.players if p.user_id == uid) for uid in proposed_team]}")
    
    # Test voting (simulate all players voting)
    votes = [True, True, True, False, False, True, True]  # 5 approve, 2 reject
    for i, player in enumerate(game.players):
        game.vote_team(player.user_id, votes[i])
    
    print(f"Game state after voting: {game.state}")
    print(f"Vote track: {game.vote_track}")

def test_mission_voting():
    """Test mission voting mechanics."""
    print_separator("TESTING MISSION VOTING")
    
    # Set up a game in mission phase
    game = AvalonGame(12345, 1)
    for i in range(7):
        game.add_player(100 + i, f"Player{i+1}")
    
    game.assign_roles()
    
    # Force game to mission state
    leader_id = game.get_current_leader().user_id
    team_size = game.get_mission_size()
    proposed_team = [p.user_id for p in game.players[:team_size]]
    game.propose_team(leader_id, proposed_team)
    
    # Approve the team
    for player in game.players:
        game.vote_team(player.user_id, True)
    
    print(f"Game state: {game.state}")
    print(f"Mission team: {[next(p.username for p in game.players if p.user_id == uid) for uid in game.proposed_team]}")
    
    # Test mission voting
    for user_id in game.proposed_team:
        player = next(p for p in game.players if p.user_id == user_id)
        # Evil players might vote fail (50% chance), good players always vote success
        vote_success = True if player.team == "good" else random.choice([True, False])
        game.vote_mission(user_id, vote_success)
        print(f"{player.username} ({player.team}) votes: {'Success' if vote_success else 'Fail'}")
    
    print(f"Mission {game.current_round} result: {game.missions[game.current_round - 1]}")
    print(f"Game state after mission: {game.state}")

def test_full_game_simulation():
    """Simulate a complete game."""
    print_separator("FULL GAME SIMULATION")
    
    game = AvalonGame(12345, 1)
    for i in range(7):
        game.add_player(100 + i, f"Player{i+1}")
    
    game.assign_roles()
    
    # Show initial setup
    print(f"Players: {[f'{p.username}({ROLES[p.role]['name']})' for p in game.players]}")
    print(f"Evil players: {[p.username for p in game.players if p.team == 'evil']}")
    
    round_num = 1
    while game.state not in [GameState.FINISHED, GameState.ASSASSINATION] and round_num <= 5:
        print(f"\n--- ROUND {round_num} ---")
        print(f"Leader: {game.get_current_leader().username}")
        print(f"Required team size: {game.get_mission_size()}")
        
        # Propose team (random selection)
        leader_id = game.get_current_leader().user_id
        team_size = game.get_mission_size()
        proposed_team = random.sample([p.user_id for p in game.players], team_size)
        
        game.propose_team(leader_id, proposed_team)
        team_names = [next(p.username for p in game.players if p.user_id == uid) for uid in proposed_team]
        print(f"Proposed team: {team_names}")
        
        # Vote on team (random approval, but bias towards approval)
        for player in game.players:
            approve = random.random() > 0.3  # 70% chance to approve
            game.vote_team(player.user_id, approve)
        
        if game.state == GameState.MISSION:
            print("Team approved! Starting mission...")
            
            # Mission voting
            for user_id in game.proposed_team:
                player = next(p for p in game.players if p.user_id == user_id)
                # Evil players have 60% chance to fail, good always succeed
                vote_success = True if player.team == "good" else random.random() > 0.6
                game.vote_mission(user_id, vote_success)
            
            mission_result = game.missions[round_num - 1]
            print(f"Mission result: {mission_result.value}")
            
            # Check if game continues
            if game.state == GameState.TEAM_PROPOSAL:
                round_num += 1
            elif game.state == GameState.ASSASSINATION:
                print("\nGood team won 3 missions! Assassination phase...")
                # Simulate assassination (random guess)
                assassin_id = game.assassin_id
                target_id = random.choice([p.user_id for p in game.players if p.team == "good"])
                game.assassinate(assassin_id, target_id)
                
                target_name = next(p.username for p in game.players if p.user_id == target_id)
                was_merlin = game.is_assassination_successful(target_id)
                print(f"Assassin targets {target_name}: {'SUCCESS' if was_merlin else 'FAILED'}")
                break
            elif game.state == GameState.FINISHED:
                break
        else:
            print("Team rejected!")
            if game.vote_track >= 5:
                print("Too many rejections! Evil wins!")
                break
    
    # Final results
    winner = game.get_game_winner()
    print(f"\nFINAL RESULT: {winner.upper()} TEAM WINS!")

def test_edge_cases():
    """Test edge cases and error conditions."""
    print_separator("TESTING EDGE CASES")
    
    # Test invalid player counts
    game = AvalonGame(12345, 1)
    print(f"Can start with 0 players: {game.can_start_game()}")
    
    # Add too many players
    for i in range(12):
        added = game.add_player(100 + i, f"Player{i+1}")
        if not added:
            print(f"Failed to add player {i+1} (expected at 11+)")
            break
    
    # Test invalid team proposals
    game = AvalonGame(12345, 1)
    for i in range(5):
        game.add_player(100 + i, f"Player{i+1}")
    game.assign_roles()
    
    leader_id = game.get_current_leader().user_id
    
    # Test wrong team size
    success = game.propose_team(leader_id, [100, 101, 102])  # Too many players
    print(f"Wrong team size proposal: {success}")
    
    # Test non-leader proposing
    non_leader_id = next(p.user_id for p in game.players if p.user_id != leader_id)
    success = game.propose_team(non_leader_id, [100, 101])
    print(f"Non-leader proposal: {success}")

def main():
    """Run all tests."""
    print("🏰 AVALON GAME LOGIC TESTING 🏰")
    
    test_role_assignment()
    test_team_proposal_and_voting()
    test_mission_voting()
    test_full_game_simulation()
    test_edge_cases()
    
    print_separator("TESTING COMPLETE")
    print("All tests finished! Check the output above for any issues.")

if __name__ == "__main__":
    main()