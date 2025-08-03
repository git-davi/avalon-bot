"""The Resistance: Avalon Discord Bot Package."""

__version__ = "1.0.0"
__author__ = "Avalon Bot Team"
__description__ = "A Discord bot for playing The Resistance: Avalon"

from .game import AvalonGame, GameState, MissionResult, Player
from .config import PLAYER_COUNTS, MISSION_SIZES, ROLES, EMOJIS

__all__ = [
    "AvalonGame",
    "GameState", 
    "MissionResult",
    "Player",
    "PLAYER_COUNTS",
    "MISSION_SIZES",
    "ROLES",
    "EMOJIS",
]