"""Main Discord bot for The Resistance: Avalon."""

import os
import logging
import asyncio
import random
from typing import Dict
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from .ai_player import AIPlayer
from .game import AvalonGame, GameState
from .config import TWO_FAIL_MISSIONS
from .views import (
    JoinGameView, TeamVoteView, GameView, MissionVoteView,
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
intents.message_content = True  # Required for proper interaction handling
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
    await interaction.response.defer()  # Acknowledge the interaction immediately
    
    channel_id = interaction.channel_id
    logger.info(f"Game start requested by {interaction.user.display_name} in channel {channel_id}")
    
    if channel_id in active_games:
        logger.warning(f"Game start failed - already active game in channel {channel_id}")
        await interaction.followup.send("There's already an active game in this channel!", ephemeral=True)
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
    
    await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="propose", description="Propose a team for the current mission")
async def propose_team(interaction: discord.Interaction, 
                      player1: discord.Member,
                      player2: discord.Member = None,
                      player3: discord.Member = None,
                      player4: discord.Member = None,
                      player5: discord.Member = None):
    """Propose a team for the mission."""
    await interaction.response.defer()
    
    channel_id = interaction.channel_id
    
    if channel_id not in active_games:
        await interaction.followup.send("No active game in this channel!", ephemeral=True)
        return
    
    game = active_games[channel_id]
    
    if game.state != GameState.TEAM_PROPOSAL:
        await interaction.followup.send("It's not time for team proposals!", ephemeral=True)
        return
    
    if game.get_current_leader().user_id != interaction.user.id:
        await interaction.followup.send("You are not the current leader!", ephemeral=True)
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
        await interaction.followup.send(embed=embed, view=view)
        
        await run_ai_players(game)
    else:
        await interaction.followup.send("Invalid team proposal!", ephemeral=True)


@bot.tree.command(name="assassinate", description="Attempt to assassinate Merlin (Assassin only)")
async def assassinate(interaction: discord.Interaction, target: discord.Member):
    """Assassinate a player (Assassin only)."""
    await interaction.response.defer()
    
    channel_id = interaction.channel_id
    
    if channel_id not in active_games:
        await interaction.followup.send("No active game in this channel!", ephemeral=True)
        return
    
    game = active_games[channel_id]
    
    if game.state != GameState.ASSASSINATION:
        await interaction.followup.send("It's not time for assassination!", ephemeral=True)
        return
    
    if game.assassin_id != interaction.user.id:
        await interaction.followup.send("Only the Assassin can use this command!", ephemeral=True)
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
        
        await interaction.followup.send(embed=embed)
        
        # Send final game over message and clean up
        await send_game_over_message(game, bot)
        if game.channel_id in active_games:
            del active_games[game.channel_id]
        if game.channel_id in active_ai_players:
            del active_ai_players[game.channel_id]
    else:
        await interaction.followup.send("Invalid assassination attempt!", ephemeral=True)


# Debug commands (only available in debug mode)
if DEBUG_MODE:
    @bot.tree.command(name="debug_game_state", description="[DEBUG] Show current game state")
    async def debug_game_state(interaction: discord.Interaction):
        """Debug command to show game state."""
        await interaction.response.defer(ephemeral=True)
        channel_id = interaction.channel_id
        if channel_id not in active_games:
            await interaction.followup.send("No active game in this channel.", ephemeral=True)
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
        
        await interaction.followup.send(f"```{debug_info}```", ephemeral=True)
    
    @bot.tree.command(name="debug_add_bots", description="[DEBUG] Add AI players to test game")
    async def debug_add_bots(interaction: discord.Interaction, count: int = 4):
        """Debug command to add bot players for testing."""
        await interaction.response.defer(ephemeral=True)
        channel_id = interaction.channel_id
        if channel_id not in active_games:
            await interaction.followup.send("No active game in this channel.")
            return
        
        game = active_games[channel_id]
        if game.state != GameState.LOBBY:
            await interaction.followup.send("Can only add bots during lobby phase.")
            return
        
        if channel_id not in active_ai_players:
            active_ai_players[channel_id] = {}
        
        added = 0
        for i in range(count):
            fake_id = 999900 + i  # Use fake IDs for test players
            if game.add_player(fake_id, f"TestBot{i+1}", is_ai=True):
                player = next(p for p in game.players if p.user_id == fake_id)
                active_ai_players[channel_id][fake_id] = AIPlayer(game, player)
                added += 1
        
        logger.debug(f"Added {added} test bots to game in channel {channel_id}")
        await interaction.followup.send(f"Added {added} test players!")
    
    @bot.tree.command(name="debug_force_start", description="[DEBUG] Force start game with current players")
    async def debug_force_start(interaction: discord.Interaction):
        """Debug command to force start a game."""
        await interaction.response.defer(ephemeral=True)
        channel_id = interaction.channel_id
        if channel_id not in active_games:
            await interaction.followup.send("No active game in this channel.", ephemeral=True)
            return
        
        game = active_games[channel_id]
        if len(game.players) < 5:
            await interaction.followup.send("Need at least 5 players to start.", ephemeral=True)
            return
        
        game.assign_roles()
        logger.debug(f"Force started game in channel {channel_id}")
        
        # Send role information via DMs (skip for test bots)
        await send_role_dms(game, bot)
        
        await interaction.followup.send("Game force started!", ephemeral=True)
        
        await run_ai_players(game)
    
    @bot.tree.command(name="debug_propose", description="[DEBUG] Propose a team using player names")
    async def debug_propose_team(interaction: discord.Interaction, 
                                players: str):
        """Debug command to propose a team using player names."""
        await interaction.response.defer(ephemeral=True)
        channel_id = interaction.channel_id
        
        if channel_id not in active_games:
            await interaction.followup.send("No active game in this channel!")
            return
        
        game = active_games[channel_id]
        
        if game.state != GameState.TEAM_PROPOSAL:
            await interaction.followup.send("It's not time for team proposals!")
            return
        
        if game.get_current_leader().user_id != interaction.user.id:
            await interaction.followup.send("You are not the current leader!")
            return
        
        # Parse player names from the input string
        player_names = [name.strip() for name in players.split(',')]
        
        # Find matching players
        team_user_ids = []
        team_names = []
        for name in player_names:
            player = next((p for p in game.players if p.username.lower() == name.lower()), None)
            if player:
                team_user_ids.append(player.user_id)
                team_names.append(player.username)
            else:
                await interaction.followup.send(f"Player '{name}' not found!")
                return
        
        if game.propose_team(interaction.user.id, team_user_ids):
            # Create team voting embed
            embed = discord.Embed(
                title=f"Round {game.current_round} - Team Proposal",
                description=f"**{interaction.user.display_name}** proposes:\n{', '.join(team_names)}",
                color=discord.Color.gold()
            )
            
            await interaction.followup.send("Team proposed successfully.")

            view = TeamVoteView(game, bot)
            await interaction.followup.send(embed=embed, view=view)
            
            await run_ai_players(game)
        else:
            await interaction.followup.send("Invalid team proposal! Check team size or if players are in the game.")
    
    @bot.tree.command(name="debug_show_players", description="[DEBUG] Show all players in the game")
    async def debug_show_players(interaction: discord.Interaction):
        """Debug command to show all players and their numbers."""
        await interaction.response.defer(ephemeral=True)
        channel_id = interaction.channel_id
        
        if channel_id not in active_games:
            await interaction.followup.send("No active game in this channel!", ephemeral=True)
            return
        
        game = active_games[channel_id]
        
        player_list = []
        for i, player in enumerate(game.players, 1):
            leader_indicator = "👑 " if i - 1 == game.current_leader_index else ""
            player_list.append(f"{i}. {leader_indicator}{player.username}")
        
        embed = discord.Embed(
            title="Players in Game",
            description="\n".join(player_list),
            color=discord.Color.blue()
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)



# Store active AI players by channel ID
active_ai_players: Dict[int, Dict[int, 'AIPlayer']] = {}


async def send_mission_votes(game: AvalonGame):
    """Send mission vote buttons to all players on the team."""
    for user_id in game.proposed_team:
        try:
            member = await bot.fetch_user(user_id)
            if member:
                view = MissionVoteView(game, user_id, bot)
                await member.send(f"**Round {game.current_round}** - You are on the mission team. Please vote:", view=view)
        except discord.NotFound:
            pass
        except discord.Forbidden:
            channel = bot.get_channel(game.channel_id)
            if channel:
                await channel.send(f"<@{user_id}>, I could not send you your mission vote. Please enable DMs from server members.")
    
    await run_ai_players(game)


async def process_team_vote_results(game: AvalonGame):
    """Process and announce team vote results."""
    approvals = sum(1 for vote in game.team_votes.values() if vote)
    rejections = len(game.team_votes) - approvals
    
    # Create vote results embed
    vote_embed = discord.Embed(
        title="Team Vote Results",
        description=f"**{approvals} Approve, {rejections} Reject**",
        color=discord.Color.green() if approvals > rejections else discord.Color.red()
    )
    
    if game.state == GameState.MISSION:
        vote_embed.add_field(name="Result", value="Team Approved! Starting mission...", inline=False)
        await send_mission_votes(game)
    elif game.state == GameState.TEAM_PROPOSAL:
        vote_embed.add_field(name="Result", value="Team Rejected! Moving to next leader...", inline=False)
    elif game.state == GameState.FINISHED:
        vote_embed.add_field(name="Result", value="Too many rejections! Evil team wins!", inline=False)
    
    # Send the results
    channel = bot.get_channel(game.channel_id)
    if channel:
        await channel.send(embed=vote_embed)
        
        if game.state != GameState.FINISHED:
            await channel.send(embed=create_game_embed(game), view=GameView(game))
        else:
            await send_game_over_message(game, bot)
    
    # Trigger AI for the next phase
    await run_ai_players(game)


async def process_mission_vote_results(game: AvalonGame):
    """Process and announce mission vote results."""
    fails = sum(1 for vote in game.mission_votes.values() if not vote)
    
    # Create mission results embed
    mission_embed = discord.Embed(
        title=f"Round {game.current_round} - Mission Results",
        description=f"**{fails} Fail{'s' if fails != 1 else ''}, {len(game.mission_votes) - fails} Success{'es' if len(game.mission_votes) - fails != 1 else ''}**",
        color=discord.Color.red() if fails > 0 else discord.Color.green()
    )
    
    # Determine mission outcome
    game._process_mission_vote()
    
    if game.state == GameState.FINISHED:
        winner = game.get_game_winner()
        mission_embed.add_field(name="Game Over!", value=f"The **{winner.upper()}** team wins!", inline=False)
    elif game.state == GameState.ASSASSINATION:
        mission_embed.add_field(name="Result", value="Mission Succeeded! The Assassin has a chance to win...", inline=False)
    else:
        mission_embed.add_field(name="Result", value="Mission Succeeded! Moving to the next round.", inline=False)
        
    # Send the results
    channel = bot.get_channel(game.channel_id)
    if channel:
        await channel.send(embed=mission_embed)
        
        if game.state != GameState.FINISHED:
            await channel.send(embed=create_game_embed(game), view=GameView(game))
        else:
            await send_game_over_message(game, bot)
            
    # Trigger AI for the next phase
    await run_ai_players(game)


async def run_ai_players(game: AvalonGame):
    """Run the AI players' decisions."""
    if game.channel_id not in active_ai_players:
        return

    ai_players = active_ai_players[game.channel_id]
    
    if game.state == GameState.TEAM_PROPOSAL:
        leader = game.get_current_leader()
        if leader.user_id in ai_players:
            await asyncio.sleep(1)  # Delay for realism
            # AI leader proposes a team
            team_size = game.get_mission_size()
            other_players = [p.user_id for p in game.players if p.user_id != leader.user_id]
            if len(other_players) >= team_size - 1:
                proposed_team = random.sample(other_players, team_size - 1)
                proposed_team.append(leader.user_id)
                logger.debug(f"AI leader {leader.username} proposing team for round {game.current_round}")
                if game.propose_team(leader.user_id, proposed_team):
                    team_names = [next(p.username for p in game.players if p.user_id == uid) for uid in proposed_team]
                    embed = discord.Embed(
                        title=f"Round {game.current_round} - Team Proposal",
                        description=f"**{leader.username}** proposes:\n{', '.join(team_names)}",
                        color=discord.Color.gold()
                    )
                    
                    channel = bot.get_channel(game.channel_id)
                    if channel:
                        view = TeamVoteView(game, bot)
                        await channel.send(embed=embed, view=view)
                        # Now trigger AI voting
                        await run_ai_players(game)

    elif game.state == GameState.TEAM_VOTING:
        await asyncio.sleep(1)
        
        logger.debug(f"AI players voting on team. Current votes: {len(game.team_votes)}/{len(game.players)}")
        
        for player in game.players:
            if player.user_id in ai_players and player.user_id not in game.team_votes:
                decision = ai_players[player.user_id].decide_team_proposal()
                game.vote_team(player.user_id, decision)
                vote_text = "approve" if decision else "reject"
                logger.debug(f"AI player {player.username} voted: {vote_text}")
        
        if len(game.team_votes) == len(game.players):
            await process_team_vote_results(game)

    elif game.state == GameState.MISSION:
        await asyncio.sleep(2)
        
        logger.debug(f"AI players voting on mission. Current votes: {len(game.mission_votes)}/{len(game.proposed_team)}")
        
        for player_id in game.proposed_team:
            if player_id in ai_players and player_id not in game.mission_votes:
                player = next(p for p in game.players if p.user_id == player_id)
                decision = ai_players[player_id].decide_mission_vote()
                game.vote_mission(player_id, decision)
                vote_text = "success" if decision else "fail"
                logger.debug(f"AI player {player.username} voted: {vote_text}")
        
        if len(game.mission_votes) == len(game.proposed_team):
            await process_mission_vote_results(game)

    elif game.state == GameState.ASSASSINATION:
        assassin_id = game.assassin_id
        if assassin_id in ai_players:
            await asyncio.sleep(1)
            target_id = ai_players[assassin_id].decide_assassination_target()
            if game.assassinate(assassin_id, target_id):
                # Announce the game over
                await send_game_over_message(game, bot)
                if game.channel_id in active_games:
                    del active_games[game.channel_id]
                if game.channel_id in active_ai_players:
                    del active_ai_players[game.channel_id]


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