# The Resistance: Avalon Discord Bot

A Discord bot that facilitates games of The Resistance: Avalon for 5-10 players.

## Features

- **Complete game management**: From lobby creation to role assignment to mission voting
- **Interactive Discord UI**: Uses buttons and embeds for smooth gameplay
- **Private role information**: Sends role details via DMs with proper information for each role
- **Automated game flow**: Handles team proposals, voting, missions, and win conditions
- **Full Avalon experience**: Includes all core roles (Merlin, Assassin, Percival, Morgana, Mordred)

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a Discord Bot**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and bot
   - Copy the bot token
   - In the "Bot" tab, under "Privileged Gateway Intents", enable both **Server Members Intent** and **Message Content Intent**.
   - Go to "OAuth2" → "URL Generator":
     - **Scopes**: check `bot` and `applications.commands`
     - **Bot Permissions**:
       - Send Messages
       - Send Messages in Threads
       - Embed Links
       - Read Message History
       - Add Reactions
       - Use Application Commands (slash commands)

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your bot token
   ```

4. **Run the bot**:
   ```bash
   python3 -m avalon
   ```

## How to Play

### Starting a Game
1. Use `/avalon_start` in any Discord channel
2. Players click "Join Game" to join the lobby (5-10 players needed)
3. Host clicks "Start Game" when ready

### Game Flow
1. **Role Assignment**: Each player receives their role via DM
2. **Team Proposal**: The leader proposes a team using `/propose @player1 @player2...`
3. **Team Voting**: All players vote to approve/reject the team
4. **Mission**: Approved team members vote on mission success/failure via DM
5. **Repeat**: Continue until 3 missions succeed (good wins) or 3 fail (evil wins)
6. **Assassination**: If good wins 3 missions, the Assassin tries to identify Merlin with `/assassinate @player`

### Roles

**Good Team (Servants of Arthur)**:
- **Merlin**: Knows all evil players (except Mordred)
- **Percival**: Sees both Merlin and Morgana (doesn't know which is which)
- **Servant of Arthur**: Regular good player

**Evil Team (Minions of Mordred)**:
- **Assassin**: Can assassinate Merlin if good team wins
- **Morgana**: Appears as Merlin to Percival
- **Mordred**: Hidden from Merlin's sight
- **Minion of Mordred**: Regular evil player

## Commands

- `/avalon_start` - Create a new game lobby
- `/propose @player1 @player2...` - Propose a mission team (leader only)
- `/assassinate @player` - Attempt to assassinate Merlin (assassin only)

## Game Rules

- **Players**: 5-10 players
- **Objective**: 
  - Good: Complete 3 out of 5 missions
  - Evil: Fail 3 missions OR assassinate Merlin
- **Mission Sizes**: Vary by player count
- **Special Rules**: Some missions require 2 fail votes to fail
- **Vote Track**: 5 consecutive team rejections = evil wins

Enjoy your game of Avalon! 🏰