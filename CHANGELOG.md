# Changelog

All notable changes to The Resistance: Avalon Discord Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-08-03

### Added
- Initial release of The Resistance: Avalon Discord Bot
- Complete game implementation for 5-10 players
- All core roles: Merlin, Percival, Assassin, Morgana, Mordred, Servants, Minions
- Interactive Discord UI with buttons and embeds
- Private role distribution via DMs
- Team proposal and voting system
- Mission voting mechanics
- Assassination phase
- Debug mode with testing features
- Comprehensive logging system
- Professional Python package structure
- Complete test suite
- Documentation and setup guides

### Features
- `/avalon_start` - Create game lobby
- `/propose` - Propose mission teams
- `/assassinate` - Assassinate Merlin attempt
- Debug commands for development and testing
- Automatic game state management
- Vote tracking and win condition detection
- Role-specific information and abilities
- Error handling and user feedback

### Technical
- Proper Python package structure with avalon/ module
- Separation of concerns (game logic, UI components, configuration)
- Comprehensive test coverage
- Standard project files (.gitignore, LICENSE, pyproject.toml)
- Development and deployment documentation