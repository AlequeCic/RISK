from enum import Enum

MAP = {
    # North Kingdom (3 territories)
    "Snowpeak": {
        "continent": "North Kingdom",
        "neighbors": ["Frostwind", "Ravenshold", "Evermoor"],
        "color": "cyan",
    },
    "Frostwind": {
        "continent": "North Kingdom", 
        "neighbors": ["Snowpeak", "Ravenshold", "Greystone"],
        "color": "cyan",
    },
    "Ravenshold": {
        "continent": "North Kingdom",
        "neighbors": ["Snowpeak", "Frostwind", "Greystone", "Evermoor"],
        "color": "cyan",
    },
    
    # Central Kingdom (3 territories)
    "Greystone": {
        "continent": "Central Kingdom",
        "neighbors": ["Frostwind", "Ravenshold", "Evermoor", "Willowdale", "Ironridge"],
        "color": "red",
    },
    "Evermoor": {
        "continent": "Central Kingdom",
        "neighbors": ["Ravenshold", "Greystone", "Willowdale", "Shadowmere", "Snowpeak"],
        "color": "red",
    },
    "Willowdale": {
        "continent": "Central Kingdom",
        "neighbors": ["Greystone", "Evermoor", "Ironridge", "Shadowmere", "Sunhaven"],
        "color": "red",
    },
    
    # South Kingdom (3 territories)
    "Ironridge": {
        "continent": "South Kingdom",
        "neighbors": ["Greystone", "Willowdale", "Sunhaven"],
        "color": "green",
    },
    "Sunhaven": {
        "continent": "South Kingdom",
        "neighbors": ["Willowdale", "Ironridge", "Shadowmere"],
        "color": "green",
    },
    "Shadowmere": {
        "continent": "South Kingdom",
        "neighbors": ["Evermoor", "Willowdale", "Sunhaven"],
        "color": "green",
    },
}

# Continent bonuses (troops per turn if you control entire continent)
CONTINENT_BONUS = {
    "North Kingdom": 2,
    "Central Kingdom": 3,
    "South Kingdom": 2,
}

# Initial troop count by player count
INITIAL_ARMIES = {
    2: 12,  # Per player
    3: 9,
    4: 6
}

# Card values for trading
CARD_VALUES = [4, 6, 8, 10, 12, 15]  # Progressive bonus per trade

# Enums for game phases
class GameState(str,Enum):
    WAITING_PLAYERS = "waiting"
    SETUP = "setup"
    DRAFT = "draft"
    ATTACK = "attack"
    MANEUVER = "maneuver"
    FINISHED = "finished"