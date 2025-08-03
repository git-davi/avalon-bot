#!/usr/bin/env python3
"""
Quick test script to verify everything is working before running the Discord bot.
"""

import os
import sys

def check_environment():
    """Check if environment is properly configured."""
    print("🏰 Avalon Bot - Quick Test & Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Check dependencies
    try:
        import discord
        print(f"✅ discord.py {discord.__version__}")
    except ImportError:
        print("❌ discord.py not installed. Run: pip install -r requirements.txt")
        return False
    
    try:
        import dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not installed. Run: pip install -r requirements.txt")
        return False
    
    # Check .env file
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        print("   Creating .env file with template...")
        with open('.env', 'w') as f:
            f.write("# Discord Bot Token\n")
            f.write("DISCORD_BOT_TOKEN=your_bot_token_here\n")
            f.write("# Debug Mode\n")
            f.write("DEBUG_MODE=true\n")
        print("✅ Created .env file - please add your bot token")
        return False
    
    # Check bot token
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token or token == 'your_bot_token_here':
        print("❌ DISCORD_BOT_TOKEN not set in .env file")
        return False
    print("✅ Bot token configured")
    
    return True

def test_game_logic():
    """Test the core game logic without Discord."""
    print("\n🎮 Testing Game Logic...")
    
    try:
        import sys
        import os
        # Add the parent directory to the path to import avalon package
        parent_dir = os.path.join(os.path.dirname(__file__), '..')
        sys.path.insert(0, parent_dir)
        
        from avalon.game import AvalonGame, GameState
        from avalon.config import PLAYER_COUNTS
        
        # Test basic game creation
        game = AvalonGame(12345, 67890)
        assert len(game.players) == 0
        
        # Test adding players
        for i in range(7):
            added = game.add_player(100 + i, f"TestPlayer{i+1}")
            assert added == True
        
        assert len(game.players) == 7
        assert game.can_start_game() == True
        
        # Test role assignment
        game.assign_roles()
        assert game.state == GameState.TEAM_PROPOSAL
        
        good_players = [p for p in game.players if p.team == "good"]
        evil_players = [p for p in game.players if p.team == "evil"]
        
        expected_good = PLAYER_COUNTS[7]["good"]
        expected_evil = PLAYER_COUNTS[7]["evil"]
        
        assert len(good_players) == expected_good
        assert len(evil_players) == expected_evil
        
        print(f"✅ Role assignment: {len(good_players)} good, {len(evil_players)} evil")
        
        # Test team proposal
        leader = game.get_current_leader()
        team_size = game.get_mission_size()
        proposed_team = [p.user_id for p in game.players[:team_size]]
        
        success = game.propose_team(leader.user_id, proposed_team)
        assert success == True
        assert game.state == GameState.TEAM_VOTING
        
        print(f"✅ Team proposal: {team_size} players proposed")
        
        print("✅ All game logic tests passed!")
        
    except Exception as e:
        print(f"❌ Game logic test failed: {e}")
        return False
    
    return True

def setup_instructions():
    """Show setup instructions."""
    print("\n📋 Next Steps:")
    print("=" * 40)
    print("1. Create a Discord bot at https://discord.com/developers/applications")
    print("2. Copy the bot token to your .env file")
    print("3. Invite the bot to your test server with these permissions:")
    print("   - Send Messages")
    print("   - Use Slash Commands")
    print("   - Embed Links")
    print("   - Send DMs")
    print("4. Run: python3 -m avalon")
    print("5. In Discord, use: /avalon_start")
    print("\n🐛 Debug Mode Features:")
    print("- Set DEBUG_MODE=true in .env for extra commands:")
    print("  /debug_add_bots - Add AI players for solo testing")
    print("  /debug_force_start - Skip waiting for players")
    print("  /debug_game_state - Show internal game state")
    print("\n📁 Test Files:")
    print("- Run 'python3 tests/test_game_logic.py' to test without Discord")
    print("- Check 'avalon_bot.log' for detailed logging")

def main():
    """Main function."""
    env_ok = check_environment()
    logic_ok = test_game_logic()
    
    if env_ok and logic_ok:
        print("\n🎉 Everything looks good! Ready to run the bot.")
    else:
        print("\n⚠️  Please fix the issues above before running the bot.")
    
    setup_instructions()

if __name__ == "__main__":
    main()