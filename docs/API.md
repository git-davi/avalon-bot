# Avalon Discord Bot API Reference

## Package Structure

```
avalon/
├── __init__.py          # Package exports and version info
├── __main__.py          # Entry point for python -m avalon
├── bot.py               # Discord bot commands and event handlers
├── views.py             # Discord UI components and embeds
├── game.py              # Core game logic and state management
└── config.py            # Game configuration and constants
```

## Core Classes

### AvalonGame

Main game state management class.

```python
from avalon import AvalonGame, GameState

game = AvalonGame(channel_id=12345, host_id=67890)
```

#### Methods

- `add_player(user_id: int, username: str) -> bool`
- `remove_player(user_id: int) -> bool`
- `can_start_game() -> bool`
- `assign_roles() -> None`
- `propose_team(leader_id: int, team_user_ids: List[int]) -> bool`
- `vote_team(user_id: int, approve: bool) -> bool`
- `vote_mission(user_id: int, success: bool) -> bool`
- `assassinate(assassin_id: int, target_id: int) -> bool`

#### Properties

- `state: GameState` - Current game phase
- `players: List[Player]` - All players in the game
- `current_round: int` - Current mission round (1-5)
- `current_leader_index: int` - Index of current leader
- `missions: List[MissionResult]` - Results of completed missions

### Player

Represents a player in the game.

```python
@dataclass
class Player:
    user_id: int
    username: str
    role: Optional[str] = None
    team: Optional[str] = None
```

#### Methods

- `is_evil() -> bool`
- `is_good() -> bool`

### GameState

Enum representing game phases.

```python
class GameState(Enum):
    LOBBY = "lobby"
    ROLE_ASSIGNMENT = "role_assignment"
    TEAM_PROPOSAL = "team_proposal"
    TEAM_VOTING = "team_voting"
    MISSION = "mission"
    ASSASSINATION = "assassination"
    FINISHED = "finished"
```

## Discord Commands

### Slash Commands

- `/avalon_start` - Create a new game lobby
- `/propose @player1 @player2 ...` - Propose a mission team (leader only)
- `/assassinate @player` - Attempt to assassinate Merlin (assassin only)

### Debug Commands (DEBUG_MODE=true only)

- `/debug_game_state` - Show internal game state
- `/debug_add_bots [count]` - Add AI players for testing
- `/debug_force_start` - Force start game with current players

## Discord UI Components

### Views

All UI components are in `avalon.views`:

- `JoinGameView` - Lobby interface (Join/Leave/Start/Cancel buttons)
- `TeamVoteView` - Team approval voting (Approve/Reject buttons)
- `MissionVoteView` - Mission outcome voting (Success/Fail buttons)
- `GameView` - Main game display (read-only)

### Embeds

Embed creation functions:

- `create_lobby_embed(game)` - Lobby display
- `create_game_embed(game)` - Main game state display
- `create_role_embed(role_info)` - Role information for DMs

### Helper Functions

- `send_role_dms(game, bot)` - Send role info to all players
- `send_mission_votes(game, bot)` - Send mission voting to team
- `send_assassination_message(game, bot)` - Notify assassin
- `send_game_over_message(game, bot)` - Final game results

## Configuration

### Game Rules

From `avalon.config`:

```python
# Player count to team distribution
PLAYER_COUNTS = {
    5: {"good": 3, "evil": 2},
    6: {"good": 4, "evil": 2},
    # ... etc
}

# Mission team sizes by player count
MISSION_SIZES = {
    5: [2, 3, 2, 3, 3],
    6: [2, 3, 4, 3, 4],
    # ... etc
}

# Missions requiring 2 fails (by player count and mission index)
TWO_FAIL_MISSIONS = {
    7: [3],  # Mission 4 for 7+ players
    8: [3],
    # ... etc
}
```

### Roles

```python
ROLES = {
    "MERLIN": {
        "name": "Merlin",
        "team": "good",
        "description": "You are Merlin! You know who the Minions of Mordred are..."
    },
    # ... all other roles
}
```

### UI Constants

```python
EMOJIS = {
    "crown": "👑",
    "success": "✅",
    "fail": "❌",
    # ... etc
}
```

## Entry Points

### Command Line

```bash
# Run the bot
python3 -m avalon

# Or if installed as package
avalon-bot
```

### Programmatic

```python
from avalon.bot import run_bot

# Run the bot
run_bot()
```

## Error Handling

The bot includes comprehensive error handling:

- Discord permission errors (graceful DM failures)
- Invalid game state transitions
- User input validation
- Network timeout handling
- Game state corruption recovery

## Logging

Set `DEBUG_MODE=true` in environment for detailed logging:

- All game actions logged
- Discord API interactions
- Error stack traces
- Performance metrics

Logs are written to `avalon_bot.log` and console.

## Testing

### Unit Tests

```python
from avalon import AvalonGame, GameState

# Test game creation
game = AvalonGame(12345, 67890)
assert game.state == GameState.LOBBY

# Test player addition
success = game.add_player(100, "TestPlayer")
assert success == True
assert len(game.players) == 1
```

### Integration Tests

Run the full test suite:

```bash
python3 tests/test_game_logic.py
python3 scripts/quick_test.py
```

## Extension Points

### Adding New Roles

1. Add role definition to `config.ROLES`
2. Update role assignment logic in `game.assign_roles()`
3. Add role-specific info in `game.get_role_info_for_player()`
4. Update tests

### Adding New Commands

1. Add slash command handler to `bot.py`
2. Create UI components in `views.py` if needed
3. Add game logic methods to `game.py`
4. Write tests and documentation

### Custom Game Modes

Extend `AvalonGame` class with custom rules:

```python
class CustomAvalonGame(AvalonGame):
    def assign_roles(self):
        # Custom role assignment logic
        super().assign_roles()
        # Additional custom logic
```