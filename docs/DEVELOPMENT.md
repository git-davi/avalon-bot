# Development Guide

This guide covers development workflows, architecture, and contribution guidelines for the Avalon Discord Bot.

## Project Structure

```
avalon/
├── avalon/              # Main package
│   ├── __init__.py     # Package initialization and exports
│   ├── __main__.py     # Entry point for python -m avalon
│   ├── bot.py          # Discord bot and command handlers
│   ├── views.py        # Discord UI components (Views, Embeds)
│   ├── game.py         # Core game logic and state management
│   └── config.py       # Game configuration and constants
├── tests/              # Test suite
│   ├── __init__.py     
│   └── test_game_logic.py
├── scripts/            # Development utilities
│   └── quick_test.py   # Environment verification and quick testing
├── docs/               # Documentation
│   ├── TESTING_GUIDE.md
│   └── DEVELOPMENT.md
└── Standard files (README.md, LICENSE, pyproject.toml, etc.)
```

## Architecture Overview

### Core Components

1. **Game Logic (`avalon/game.py`)**
   - `AvalonGame`: Main game state management
   - `Player`: Player data and role information
   - `GameState`: State machine for game phases
   - Role assignment and game rules enforcement

2. **Discord Interface (`avalon/bot.py`)**
   - Slash command handlers (`/avalon_start`, `/propose`, `/assassinate`)
   - Event handlers and error management
   - Game lifecycle management

3. **UI Components (`avalon/views.py`)**
   - Discord Views for interactive buttons
   - Embed creation functions
   - DM and channel messaging utilities

4. **Configuration (`avalon/config.py`)**
   - Game rules and player count mappings
   - Role definitions and descriptions
   - UI constants (emojis, colors)

### Design Principles

- **Separation of Concerns**: Game logic is independent of Discord API
- **Type Safety**: Proper type hints throughout the codebase
- **Error Handling**: Graceful failure and user feedback
- **Testability**: Core logic can be tested without Discord
- **Modularity**: Components can be developed and tested independently

## Development Setup

### Prerequisites

- Python 3.8+
- Discord bot token
- Git

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd avalon-discord-bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your bot token and set DEBUG_MODE=true
   ```

3. **Run tests**:
   ```bash
   python3 scripts/quick_test.py
   python3 tests/test_game_logic.py
   pytest tests/  # If you have pytest installed
   ```

4. **Run the bot**:
   ```bash
   python3 -m avalon
   ```

### Debug Mode

Enable debug mode by setting `DEBUG_MODE=true` in your `.env` file:

- Enhanced logging to console and `avalon_bot.log`
- Additional slash commands for testing:
  - `/debug_game_state` - Inspect game state
  - `/debug_add_bots` - Add AI players for solo testing
  - `/debug_force_start` - Skip lobby waiting

## Testing Strategy

### Unit Tests
- **Game Logic**: Test all game rules, state transitions, and edge cases
- **Role Assignment**: Verify correct distribution for all player counts
- **Win Conditions**: Test all victory/defeat scenarios

### Integration Tests
- **Discord Commands**: Test slash command handling
- **UI Interactions**: Test button clicks and view updates
- **DM Functionality**: Test private message delivery

### Manual Testing Scenarios
1. **Different Player Counts**: Test 5, 6, 7, 8, 9, 10 player games
2. **Role Combinations**: Verify all roles work correctly together
3. **Edge Cases**: Network issues, user leaving mid-game, etc.
4. **UI/UX**: Test button responsiveness and embed readability

## Code Style

### Python Standards
- Follow PEP 8 style guidelines
- Use Black for code formatting (`black avalon/`)
- Type hints for all functions and methods
- Docstrings for all public APIs

### Git Workflow
- Feature branches for new development
- Descriptive commit messages
- Pull requests for code review
- Squash commits before merging

### Naming Conventions
- Classes: `PascalCase` (e.g., `AvalonGame`)
- Functions/variables: `snake_case` (e.g., `assign_roles`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `PLAYER_COUNTS`)
- Files: `snake_case.py`

## Adding New Features

### New Game Roles
1. Add role definition to `config.py`
2. Update role assignment logic in `game.py`
3. Add role-specific information handling
4. Update tests for new combinations
5. Document the new role

### New Commands
1. Add slash command to `bot.py`
2. Create any necessary UI components in `views.py`
3. Add error handling and validation
4. Write tests for the new command
5. Update documentation

### UI Improvements
1. Modify or add View classes in `views.py`
2. Update embed creation functions
3. Test button interactions and timeouts
4. Ensure mobile compatibility
5. Validate accessibility

## Performance Considerations

- **Memory**: Game states are stored in memory - monitor usage
- **Discord Rate Limits**: Be aware of API limits for DMs and messages
- **Concurrent Games**: Test multiple simultaneous games
- **Error Recovery**: Handle network issues gracefully

## Debugging Common Issues

### Bot Not Responding
- Check bot permissions in Discord server
- Verify token is correct and bot is online
- Check console logs for connection errors

### Commands Not Appearing
- Ensure slash commands are synced (check startup logs)
- Wait 1-2 minutes for Discord to update commands
- Verify bot has `applications.commands` scope

### DMs Not Working
- Users must allow DMs from server members
- Handle `discord.Forbidden` exceptions gracefully
- Provide fallback notification in channel

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Error handling is comprehensive

## Release Process

1. Update version in `pyproject.toml` and `avalon/__init__.py`
2. Update `CHANGELOG.md` with new features and fixes
3. Create release tag and GitHub release
4. Update deployment documentation if needed

## Support

- GitHub Issues for bug reports and feature requests
- Discussions for general questions and ideas
- Contributing guidelines for code contributions