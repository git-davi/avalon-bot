"""Discord UI components for The Resistance: Avalon bot."""

import discord
from typing import Dict

from .game import AvalonGame, GameState, MissionResult
from .config import EMOJIS, ROLES


class JoinGameView(discord.ui.View):
    """View for joining/leaving the game lobby."""
    
    def __init__(self, game: AvalonGame, active_games: Dict[int, AvalonGame]):
        super().__init__(timeout=300)
        self.game = game
        self.active_games = active_games
    
    @discord.ui.button(label='Join Game', style=discord.ButtonStyle.primary, emoji='➕')
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.add_player(interaction.user.id, interaction.user.display_name):
            await interaction.response.edit_message(embed=create_lobby_embed(self.game), view=self)
        else:
            await interaction.response.send_message("Could not join the game (already in game or game is full).", ephemeral=True)
    
    @discord.ui.button(label='Leave Game', style=discord.ButtonStyle.secondary, emoji='➖')
    async def leave_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.remove_player(interaction.user.id):
            await interaction.response.edit_message(embed=create_lobby_embed(self.game), view=self)
        else:
            await interaction.response.send_message("Could not leave the game.", ephemeral=True)
    
    @discord.ui.button(label='Start Game', style=discord.ButtonStyle.success, emoji='🎮')
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host_id:
            await interaction.response.send_message("Only the host can start the game.", ephemeral=True)
            return
        
        if not self.game.can_start_game():
            await interaction.response.send_message("Need 5-10 players to start the game.", ephemeral=True)
            return
        
        # Assign roles and start the game
        self.game.assign_roles()
        
        # Send role information via DMs
        await send_role_dms(self.game, interaction.client)
        
        # Update the main message
        await interaction.response.edit_message(embed=create_game_embed(self.game), view=GameView(self.game))
    
    @discord.ui.button(label='Cancel Game', style=discord.ButtonStyle.danger, emoji='❌')
    async def cancel_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host_id:
            await interaction.response.send_message("Only the host can cancel the game.", ephemeral=True)
            return
        
        del self.active_games[self.game.channel_id]
        await interaction.response.edit_message(content="Game cancelled.", embed=None, view=None)


class TeamVoteView(discord.ui.View):
    """View for voting on team proposals."""
    
    def __init__(self, game: AvalonGame, bot):
        super().__init__(timeout=120)
        self.game = game
        self.bot = bot
    
    @discord.ui.button(label='Approve', style=discord.ButtonStyle.success, emoji='👍')
    async def approve_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.vote_team(interaction.user.id, True):
            await interaction.response.send_message("You approved the team.", ephemeral=True)
            
            # Check if voting is complete
            if len(self.game.team_votes) == len(self.game.players):
                await self.finish_voting(interaction)
        else:
            await interaction.response.send_message("Could not record your vote.", ephemeral=True)
    
    @discord.ui.button(label='Reject', style=discord.ButtonStyle.danger, emoji='👎')
    async def reject_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.vote_team(interaction.user.id, False):
            await interaction.response.send_message("You rejected the team.", ephemeral=True)
            
            # Check if voting is complete
            if len(self.game.team_votes) == len(self.game.players):
                await self.finish_voting(interaction)
        else:
            await interaction.response.send_message("Could not record your vote.", ephemeral=True)
    
    async def finish_voting(self, interaction: discord.Interaction):
        """Handle the completion of team voting."""
        approvals = sum(1 for vote in self.game.team_votes.values() if vote)
        rejections = len(self.game.team_votes) - approvals
        
        # Create vote results embed
        vote_embed = discord.Embed(
            title="Team Vote Results",
            description=f"**{approvals} Approve, {rejections} Reject**",
            color=discord.Color.green() if approvals > rejections else discord.Color.red()
        )
        
        if self.game.state == GameState.MISSION:
            vote_embed.add_field(name="Result", value="Team Approved! Starting mission...", inline=False)
            # Send mission votes to team members
            await send_mission_votes(self.game, self.bot)
        elif self.game.state == GameState.TEAM_PROPOSAL:
            vote_embed.add_field(name="Result", value="Team Rejected! Moving to next leader...", inline=False)
        elif self.game.state == GameState.FINISHED:
            vote_embed.add_field(name="Result", value="Too many rejections! Evil team wins!", inline=False)
        
        # Update the main game message
        channel = self.bot.get_channel(self.game.channel_id)
        if channel:
            await channel.send(embed=vote_embed)
            
            if self.game.state != GameState.FINISHED:
                # Update game state
                game_message = await channel.send(embed=create_game_embed(self.game), view=GameView(self.game))


class MissionVoteView(discord.ui.View):
    """View for mission voting (sent via DM)."""
    
    def __init__(self, game: AvalonGame, user_id: int, bot):
        super().__init__(timeout=120)
        self.game = game
        self.user_id = user_id
        self.bot = bot
        
        # Only show Fail button to evil players
        player = next((p for p in game.players if p.user_id == user_id), None)
        if not player or player.is_good():
            self.remove_item(self.fail_mission)
    
    @discord.ui.button(label='Success', style=discord.ButtonStyle.success, emoji='✅')
    async def success_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.vote_mission(self.user_id, True):
            await interaction.response.edit_message(content="You voted for the mission to **succeed**.", view=None)
            
            # Check if all mission votes are in
            if len(self.game.mission_votes) == len(self.game.proposed_team):
                await self.finish_mission_voting()
        else:
            await interaction.response.send_message("Could not record your vote.", ephemeral=True)
    
    @discord.ui.button(label='Fail', style=discord.ButtonStyle.danger, emoji='❌')
    async def fail_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.vote_mission(self.user_id, False):
            await interaction.response.edit_message(content="You voted for the mission to **fail**.", view=None)
            
            # Check if all mission votes are in
            if len(self.game.mission_votes) == len(self.game.proposed_team):
                await self.finish_mission_voting()
        else:
            await interaction.response.send_message("Could not record your vote.", ephemeral=True)
    
    async def finish_mission_voting(self):
        """Handle the completion of mission voting."""
        fails = sum(1 for vote in self.game.mission_votes.values() if not vote)
        
        # Create mission results embed
        channel = self.bot.get_channel(self.game.channel_id)
        if channel:
            mission_embed = discord.Embed(
                title=f"Mission {self.game.current_round} Results",
                color=discord.Color.red() if fails > 0 else discord.Color.green()
            )
            
            if self.game.missions[self.game.current_round - 1] == MissionResult.SUCCESS:
                mission_embed.description = f"**Mission Successful!** {fails} Fail votes."
            else:
                mission_embed.description = f"**Mission Failed!** {fails} Fail votes."
            
            await channel.send(embed=mission_embed)
            
            # Check if game is over
            if self.game.state == GameState.FINISHED:
                await send_game_over_message(self.game, self.bot)
            elif self.game.state == GameState.ASSASSINATION:
                await send_assassination_message(self.game, self.bot)
            else:
                # Continue to next round
                await channel.send(embed=create_game_embed(self.game), view=GameView(self.game))


class GameView(discord.ui.View):
    """Main game view (mostly displays current state)."""
    
    def __init__(self, game: AvalonGame):
        super().__init__(timeout=None)
        self.game = game


def create_lobby_embed(game: AvalonGame) -> discord.Embed:
    """Create the lobby embed."""
    embed = discord.Embed(
        title="🏰 The Resistance: Avalon",
        description="A new game of Avalon is starting!",
        color=discord.Color.blue()
    )
    
    player_list = "\n".join([f"{i+1}. {p.username}" for i, p in enumerate(game.players)])
    if not player_list:
        player_list = "*No players yet*"
    
    embed.add_field(
        name=f"Players ({len(game.players)}/10)",
        value=player_list,
        inline=False
    )
    
    embed.add_field(
        name="How to Play",
        value="• 5-10 players needed\n• Good team must complete 3 missions\n• Evil team tries to sabotage missions\n• If good team succeeds, Assassin gets to guess Merlin",
        inline=False
    )
    
    if game.can_start_game():
        embed.color = discord.Color.green()
        embed.set_footer(text="Ready to start! Host can begin the game.")
    else:
        embed.set_footer(text=f"Need {5 - len(game.players)} more players to start.")
    
    return embed


def create_game_embed(game: AvalonGame) -> discord.Embed:
    """Create the main game state embed."""
    embed = discord.Embed(
        title="🏰 The Resistance: Avalon",
        color=discord.Color.blue()
    )
    
    # Players list
    player_list = []
    for i, player in enumerate(game.players):
        crown = EMOJIS["crown"] if i == game.current_leader_index else ""
        player_list.append(f"{crown} {player.username}")
    
    embed.add_field(
        name=f"Players ({len(game.players)})",
        value="\n".join(player_list),
        inline=True
    )
    
    # Mission track
    mission_track = []
    for i, mission in enumerate(game.missions):
        if mission == MissionResult.SUCCESS:
            mission_track.append(f"{i+1}: {EMOJIS['mission_success']}")
        elif mission == MissionResult.FAIL:
            mission_track.append(f"{i+1}: {EMOJIS['mission_fail']}")
        else:
            mission_track.append(f"{i+1}: {EMOJIS['pending']}")
    
    embed.add_field(
        name="Mission Track",
        value="\n".join(mission_track),
        inline=True
    )
    
    # Vote track
    vote_track_display = "🔴" * game.vote_track + "⚪" * (5 - game.vote_track)
    embed.add_field(
        name="Vote Track",
        value=vote_track_display,
        inline=True
    )
    
    # Current phase
    if game.state == GameState.TEAM_PROPOSAL:
        leader = game.get_current_leader()
        team_size = game.get_mission_size()
        embed.add_field(
            name=f"Round {game.current_round} - Team Proposal",
            value=f"{EMOJIS['crown']} **{leader.username}** must propose a team of **{team_size}** players.\nUse `/propose @player1 @player2 ...`",
            inline=False
        )
    elif game.state == GameState.TEAM_VOTING:
        team_names = [next(p.username for p in game.players if p.user_id == uid) for uid in game.proposed_team]
        embed.add_field(
            name=f"Round {game.current_round} - Team Vote",
            value=f"**Proposed Team:** {', '.join(team_names)}\nAll players vote to approve or reject this team.",
            inline=False
        )
    elif game.state == GameState.MISSION:
        team_names = [next(p.username for p in game.players if p.user_id == uid) for uid in game.proposed_team]
        embed.add_field(
            name=f"Round {game.current_round} - Mission",
            value=f"**Mission Team:** {', '.join(team_names)}\nTeam members are voting on the mission outcome via DM.",
            inline=False
        )
    elif game.state == GameState.ASSASSINATION:
        embed.add_field(
            name="Assassination Phase",
            value="The good team completed 3 missions! The Assassin must now guess who Merlin is.\nAssassin, use `/assassinate @player`",
            inline=False
        )
    
    return embed


def create_role_embed(role_info: dict) -> discord.Embed:
    """Create a role information embed."""
    role_name = ROLES[role_info["role"]]["name"]
    team_color = discord.Color.blue() if role_info["team"] == "good" else discord.Color.red()
    
    embed = discord.Embed(
        title=f"Your Role: {role_name}",
        description=role_info["description"],
        color=team_color
    )
    
    if "known_evil" in role_info:
        embed.add_field(
            name="Known Minions of Mordred",
            value="\n".join(role_info["known_evil"]) if role_info["known_evil"] else "*None visible*",
            inline=False
        )
    
    if "merlin_morgana" in role_info:
        embed.add_field(
            name="Merlin and Morgana",
            value="\n".join(role_info["merlin_morgana"]),
            inline=False
        )
    
    if "evil_teammates" in role_info:
        embed.add_field(
            name="Your Fellow Minions",
            value="\n".join(role_info["evil_teammates"]) if role_info["evil_teammates"] else "*You are alone*",
            inline=False
        )
    
    return embed


async def send_role_dms(game: AvalonGame, bot):
    """Send role information to all players via DM."""
    for player in game.players:
        try:
            user = bot.get_user(player.user_id)
            if user:
                role_info = game.get_role_info_for_player(player.user_id)
                embed = create_role_embed(role_info)
                await user.send(embed=embed)
        except discord.Forbidden:
            # User has DMs disabled
            pass


async def send_mission_votes(game: AvalonGame, bot):
    """Send mission voting options to team members via DM."""
    for user_id in game.proposed_team:
        try:
            user = bot.get_user(user_id)
            if user:
                embed = discord.Embed(
                    title=f"Mission {game.current_round} Vote",
                    description="You are on the mission team! Vote for the mission outcome:",
                    color=discord.Color.gold()
                )
                
                view = MissionVoteView(game, user_id, bot)
                await user.send(embed=embed, view=view)
        except discord.Forbidden:
            # User has DMs disabled
            pass


async def send_assassination_message(game: AvalonGame, bot):
    """Send assassination prompt to the Assassin."""
    try:
        assassin_user = bot.get_user(game.assassin_id)
        if assassin_user:
            embed = discord.Embed(
                title="🗡️ Assassination Phase",
                description="The good team has completed 3 missions! You must now guess who Merlin is to win the game for evil.\n\nUse `/assassinate @player` in the game channel.",
                color=discord.Color.red()
            )
            await assassin_user.send(embed=embed)
    except discord.Forbidden:
        pass


async def send_game_over_message(game: AvalonGame, bot):
    """Send the game over message."""
    channel = bot.get_channel(game.channel_id)
    if not channel:
        return
    
    winner = game.get_game_winner()
    
    embed = discord.Embed(title="🏰 Game Over!")
    
    if winner == "good":
        embed.color = discord.Color.blue()
        embed.description = "**The Servants of Arthur have won!**"
    else:
        embed.color = discord.Color.red()
        embed.description = "**The Minions of Mordred have won!**"
    
    # Show all roles
    role_reveal = []
    for player in game.players:
        role_name = ROLES[player.role]["name"]
        team_emoji = "🔵" if player.team == "good" else "🔴"
        role_reveal.append(f"{team_emoji} **{player.username}**: {role_name}")
    
    embed.add_field(
        name="Role Reveal",
        value="\n".join(role_reveal),
        inline=False
    )
    
    await channel.send(embed=embed)