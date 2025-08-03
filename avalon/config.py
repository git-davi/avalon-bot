"""Configuration settings for the Avalon Discord Bot."""

# Game configuration
PLAYER_COUNTS = {
    5: {"good": 3, "evil": 2},
    6: {"good": 4, "evil": 2},
    7: {"good": 4, "evil": 3},
    8: {"good": 5, "evil": 3},
    9: {"good": 6, "evil": 3},
    10: {"good": 6, "evil": 4}
}

# Mission team sizes by player count
MISSION_SIZES = {
    5: [2, 3, 2, 3, 3],
    6: [2, 3, 4, 3, 4],
    7: [2, 3, 3, 4, 4],
    8: [3, 4, 4, 5, 5],
    9: [3, 4, 4, 5, 5],
    10: [3, 4, 4, 5, 5]
}

# Missions that require 2 fails to fail (0-indexed)
TWO_FAIL_MISSIONS = {
    7: [3],  # Mission 4 for 7 players
    8: [3],  # Mission 4 for 8+ players
    9: [3],
    10: [3]
}

# Role definitions
ROLES = {
    "MERLIN": {
        "name": "Merlin",
        "team": "good",
        "description": "You are Merlin! You know who the Minions of Mordred are (except Mordred). Guide the Servants of Arthur to victory, but stay hidden from the Assassin!"
    },
    "PERCIVAL": {
        "name": "Percival",
        "team": "good", 
        "description": "You are Percival! You can see Merlin and Morgana, but you don't know which is which. Protect Merlin!"
    },
    "SERVANT": {
        "name": "Servant of Arthur",
        "team": "good",
        "description": "You are a loyal Servant of Arthur! Work with your fellow servants to complete 3 missions successfully."
    },
    "ASSASSIN": {
        "name": "Assassin",
        "team": "evil",
        "description": "You are the Assassin! Work with your fellow Minions to sabotage missions. If the good team completes 3 missions, you get one chance to assassinate Merlin and win!"
    },
    "MORGANA": {
        "name": "Morgana",
        "team": "evil",
        "description": "You are Morgana! You appear as Merlin to Percival. Work with your fellow Minions to sabotage missions and deceive the good team."
    },
    "MORDRED": {
        "name": "Mordred",
        "team": "evil",
        "description": "You are Mordred! You are hidden from Merlin's sight. Work with your fellow Minions to sabotage missions."
    },
    "MINION": {
        "name": "Minion of Mordred", 
        "team": "evil",
        "description": "You are a Minion of Mordred! Work with your fellow Minions to sabotage missions and prevent the good team from succeeding."
    }
}

# Emojis for UI
EMOJIS = {
    "crown": "👑",
    "success": "✅",
    "fail": "❌", 
    "pending": "⏳",
    "vote_approve": "👍",
    "vote_reject": "👎",
    "mission_success": "🔵",
    "mission_fail": "🔴"
}