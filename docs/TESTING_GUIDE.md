# Testing Guide for Avalon Discord Bot

## 1. Discord Bot Setup

### Create a Discord Application & Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "Avalon Test Bot")
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot" if not already created
5. Under "Token", click "Copy" to get your bot token
6. **Important**: Keep this token secret!

### Bot Permissions
In the "Bot" section, enable these permissions:
- Send Messages
- Use Slash Commands  
- Send Messages in Threads
- Embed Links
- Read Message History
- Add Reactions
- Send DMs to Users

### Generate Invite URL
1. Go to "OAuth2" → "URL Generator"
2. Select scopes: `bot` and `applications.commands`
3. Select the permissions listed above
4. Copy the generated URL

## 2. Create a Test Discord Server

1. Create a new Discord server for testing (or use an existing one)
2. Use the invite URL from step 1 to add your bot to the server
3. The bot should appear offline until you run the code

## 3. Local Environment Setup

### Configure Environment
```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your bot token
echo "DISCORD_BOT_TOKEN=your_actual_bot_token_here" > .env
```

### Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Or if you prefer virtual environment (recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Running & Testing

### Start the Bot
```bash
python3 -m avalon
```

You should see:
```
Avalon Bot has connected to Discord!
Synced X command(s)
```

### Basic Testing Workflow

1. **Test Lobby Creation**:
   - In your test Discord server: `/avalon_start`
   - Click "Join Game" button
   - Invite friends or use alt accounts to test with multiple players

2. **Test with Multiple Accounts** (Recommended):
   - Use Discord in multiple browsers/devices
   - Create alt accounts for testing different player counts
   - Test with 5, 7, and 10 players to verify different game configurations

3. **Test Game Flow**:
   - Start a game with 5+ players
   - Check DMs for role information
   - Test team proposals: `/propose @player1 @player2`
   - Test team voting (approve/reject buttons)
   - Test mission voting via DMs
   - Test assassination phase

## 5. Debugging Tips

### Check Bot Logs
The bot prints useful information to console:
- Connection status
- Command sync results
- Any errors that occur

### Common Issues

**Bot doesn't respond to commands:**
- Check if bot is online in Discord
- Verify bot has proper permissions in the channel
- Check console for errors

**DMs not working:**
- Users must allow DMs from server members
- Check if users have DMs disabled

**Commands not showing up:**
- Wait a few minutes after starting bot (Discord can be slow)
- Try `/` in Discord to see if commands appear
- Check console for command sync errors

### Enable Debug Mode
Add to your `.env` file:
```
DEBUG_MODE=true
```

## 6. Testing Different Scenarios

### Player Counts
Test with different player counts to verify:
- Correct role distribution
- Proper mission team sizes
- Two-fail mission rules (7+ players)

### Edge Cases
- Players leaving mid-game
- Invalid team proposals
- Network disconnections
- Multiple games in different channels

### Role-Specific Testing
- **Merlin**: Can see evil players (except Mordred)
- **Percival**: Sees Merlin and Morgana
- **Evil players**: Can see each other
- **Assassin**: Can assassinate after 3 good missions

## 7. Testing Tools & Scripts

### Quick Environment Check
```bash
# Run this first to verify everything is set up correctly
python3 quick_test.py
```

This script will:
- Check Python version and dependencies
- Verify .env configuration
- Test core game logic
- Show setup instructions

### Game Logic Testing (No Discord Required)
```bash
# Test the game mechanics without Discord
python3 test_game_logic.py
```

This comprehensive test covers:
- Role assignment for all player counts
- Team proposal and voting mechanics
- Mission voting and results
- Full game simulation
- Edge cases and error handling

### Debug Mode Features
Enable debug mode by setting `DEBUG_MODE=true` in your `.env` file.

**Debug commands available in Discord:**
- `/debug_game_state` - Show internal game state
- `/debug_add_bots 4` - Add AI players for solo testing
- `/debug_force_start` - Skip lobby waiting period

**Enhanced logging:**
- Detailed logs saved to `avalon_bot.log`
- Real-time console output
- Error tracking and debugging info

## 8. Performance Testing

For testing with many games simultaneously:
```bash
# Monitor memory usage
python -m memory_profiler bot.py

# Check for memory leaks by running multiple games
```

## 9. Automated Testing Ideas

Consider adding unit tests for:
- Role assignment logic
- Mission voting rules
- Win condition detection
- Game state transitions

Happy testing! 🎮