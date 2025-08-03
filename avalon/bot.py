"""Main Discord bot for The Resistance: Avalon."""

import os
import logging
from typing import Dict
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from .game import AvalonGame, GameState
from .views import (
    JoinGameView, TeamVoteView, GameView, 
    create_lobby_embed, create_game_embed,
    send_role_dms, send_assassination_message, send_game_over_message
)

# Load environment variables
load_dotenv()

# Setup logging
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('avalon_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Store active games by channel ID
active_games: Dict[int, AvalonGame] = {}


@bot.event
async def on_ready():
    """Bot startup event."""
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} command(s)')
        if DEBUG_MODE:
            logger.debug(f'Available commands: {[cmd.name for cmd in synced]}')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    logger.error(f'Command error in {ctx.command}: {error}')


@bot.event  
async def on_application_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle slash command errors."""
    logger.error(f'Slash command error: {error}')
    if not interaction.response.is_done():
        await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)


@bot.tree.command(name="avalon_start", description="Start a new game of The Resistance: Avalon")
async def avalon_start(interaction: discord.Interaction):
    """Start a new Avalon game."""
    channel_id = interaction.channel_id
    logger.info(f"Game start requested by {interaction.user.display_name} in channel {channel_id}")
    
    if channel_id in active_games:
        logger.warning(f"Game start failed - already active game in channel {channel_id}")
        await interaction.response.send_message("There's already an active game in this channel!", ephemeral=True)
        return
    
    # Create new game
    game = AvalonGame(channel_id, interaction.user.id)
    active_games[channel_id] = game
    
    # Add the host as the first player
    game.add_player(interaction.user.id, interaction.user.display_name)
    logger.info(f"New game created in channel {channel_id}, host: {interaction.user.display_name}")
    
    # Create and send lobby embed
    embed = create_lobby_embed(game)
    view = JoinGameView(game, active_games)
    
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="propose", description="Propose a team for the current mission")
async def propose_team(interaction: discord.Interaction, 
                      player1: discord.Member,
                      player2: discord.Member = None,
                      player3: discord.Member = None,
                      player4: discord.Member = None,
                      player5: discord.Member = None):
    """Propose a team for the mission."""
    channel_id = interaction.channel_id
    
    if channel_id not in active_games:
        await interaction.response.send_message("No active game in this channel!", ephemeral=True)
        return
    
    game = active_games[channel_id]
    
    if game.state != GameState.TEAM_PROPOSAL:
        await interaction.response.send_message("It's not time for team proposals!", ephemeral=True)
        return
    
    if game.get_current_leader().user_id != interaction.user.id:
        await interaction.response.send_message("You are not the current leader!", ephemeral=True)
        return
    
    # Collect proposed team
    proposed_members = [player1]
    if player2: proposed_members.append(player2)
    if player3: proposed_members.append(player3)
    if player4: proposed_members.append(player4)
    if player5: proposed_members.append(player5)
    
    team_user_ids = [member.id for member in proposed_members]
    
    if game.propose_team(interaction.user.id, team_user_ids):
        # Create team voting embed
        team_names = [member.display_name for member in proposed_members]
        embed = discord.Embed(
            title=f"Round {game.current_round} - Team Proposal",
            description=f"**{interaction.user.display_name}** proposes:\n{', '.join(team_names)}",
            color=discord.Color.gold()
        )
        
        view = TeamVoteView(game, bot)
        await interaction.response.send_message(embed=embed, view=view)
    else:
        await interaction.response.send_message("Invalid team proposal!", ephemeral=True)


@bot.tree.command(name="assassinate", description="Attempt to assassinate Merlin (Assassin only)")
async def assassinate(interaction: discord.Interaction, target: discord.Member):
    """Assassinate a player (Assassin only)."""
    channel_id = interaction.channel_id
    
    if channel_id not in active_games:
        await interaction.response.send_message("No active game in this channel!", ephemeral=True)
        return
    
    game = active_games[channel_id]
    
    if game.state != GameState.ASSASSINATION:
        await interaction.response.send_message("It's not time for assassination!", ephemeral=True)
        return
    
    if game.assassin_id != interaction.user.id:
        await interaction.response.send_message("Only the Assassin can use this command!", ephemeral=True)
        return
    
    if game.assassinate(interaction.user.id, target.id):
        # Determine the outcome
        if game.is_assassination_successful(target.id):
            result = f"🗡️ **{target.display_name}** was Merlin! The Minions of Mordred win!"
            game.state = GameState.FINISHED
        else:
            result = f"🛡️ **{target.display_name}** was not Merlin! The Servants of Arthur win!"
            game.state = GameState.FINISHED
        
        embed = discord.Embed(
            title="Assassination Result",
            description=result,
            color=discord.Color.red() if game.is_assassination_successful(target.id) else discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Send final game over message and clean up
        await send_game_over_message(game, bot)
        if game.channel_id in active_games:
            del active_games[game.channel_id]
    else:
        await interaction.response.send_message("Invalid assassination attempt!", ephemeral=True)


# Debug commands (only available in debug mode)
if DEBUG_MODE:
    @bot.tree.command(name="debug_game_state", description="[DEBUG] Show current game state")
    async def debug_game_state(interaction: discord.Interaction):
        """Debug command to show game state."""
        channel_id = interaction.channel_id
        if channel_id not in active_games:
            await interaction.response.send_message("No active game in this channel.", ephemeral=True)
            return
        
        game = active_games[channel_id]
        debug_info = f"""
**Game State**: {game.state.value}
**Players**: {len(game.players)}
**Current Round**: {game.current_round}
**Leader Index**: {game.current_leader_index}
**Vote Track**: {game.vote_track}
**Proposed Team**: {game.proposed_team}
**Team Votes**: {len(game.team_votes)}/{len(game.players)}
**Mission Votes**: {len(game.mission_votes)}/{len(game.proposed_team)}
        """
        
        await interaction.response.send_message(f"```{debug_info}```", ephemeral=True)
    
    @bot.tree.command(name="debug_add_bots", description="[DEBUG] Add AI players to test game")
    async def debug_add_bots(interaction: discord.Interaction, count: int = 4):
        """Debug command to add bot players for testing."""
        channel_id = interaction.channel_id
        if channel_id not in active_games:
            await interaction.response.send_message("No active game in this channel.", ephemeral=True)
            return
        
        game = active_games[channel_id]
        if game.state != GameState.LOBBY:
            await interaction.response.send_message("Can only add bots during lobby phase.", ephemeral=True)
            return
        
        added = 0
        for i in range(count):
            fake_id = 999900 + i  # Use fake IDs for test players
            if game.add_player(fake_id, f"TestBot{i+1}"):
                added += 1
        
        logger.debug(f"Added {added} test bots to game in channel {channel_id}")
        await interaction.response.send_message(f"Added {added} test players!", ephemeral=True)
    
    @bot.tree.command(name="debug_force_start", description="[DEBUG] Force start game with current players")
    async def debug_force_start(interaction: discord.Interaction):
        """Debug command to force start a game."""
        channel_id = interaction.channel_id
        if channel_id not in active_games:
            await interaction.response.send_message("No active game in this channel.", ephemeral=True)
            return
        
        game = active_games[channel_id]
        if len(game.players) < 5:
            await interaction.response.send_message("Need at least 5 players to start.", ephemeral=True)
            return
        
        game.assign_roles()
        logger.debug(f"Force started game in channel {channel_id}")
        
        # Send role information via DMs (skip for test bots)
        await send_role_dms(game, bot)
        
        await interaction.response.send_message("Game force started!", ephemeral=True)


def run_bot():
    """Entry point to run the bot."""
    # Get bot token from environment variable
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token:
        logger.error("Please set DISCORD_BOT_TOKEN environment variable")
        exit(1)
    
    logger.info(f"Starting Avalon bot in {'DEBUG' if DEBUG_MODE else 'NORMAL'} mode")
    bot.run(bot_token)


if __name__ == "__main__":
    run_bot()