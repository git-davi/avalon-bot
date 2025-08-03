"""Setup script for The Resistance: Avalon Discord Bot."""

import os
import sys

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def check_env_file():
    """Check if .env file exists and has the required token."""
    if not os.path.exists('.env'):
        print("⚠ .env file not found. Please copy .env.example to .env and add your bot token.")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
        if 'DISCORD_BOT_TOKEN=' not in content or 'your_bot_token_here' in content:
            print("⚠ Please set your DISCORD_BOT_TOKEN in the .env file.")
            return False
    
    print("✓ .env file configured")
    return True

def install_dependencies():
    """Install required dependencies."""
    try:
        import discord
        import dotenv
        print("✓ Dependencies already installed")
    except ImportError:
        print("Installing dependencies...")
        os.system("pip install -r requirements.txt")
        print("✓ Dependencies installed")

def main():
    """Main setup function."""
    print("🏰 The Resistance: Avalon Discord Bot Setup")
    print("=" * 45)
    
    check_python_version()
    install_dependencies()
    
    if not check_env_file():
        print("\n❌ Setup incomplete. Please configure your .env file.")
        return
    
    print("\n✅ Setup complete!")
    print("\nTo start the bot, run:")
    print("  python bot.py")
    print("\nTo add the bot to your Discord server:")
    print("  1. Go to Discord Developer Portal")
    print("  2. Navigate to your bot's OAuth2 > URL Generator")
    print("  3. Select 'bot' and 'applications.commands' scopes")
    print("  4. Select required permissions (see README.md)")
    print("  5. Use the generated URL to invite the bot")

if __name__ == "__main__":
    main()