from enum import Enum

MAP = {
    # North Kingdom (3 territories)
    "Snowpeak": {
        "id": 1,
        "continent": "North Kingdom",
        "neighbors": ["Frostwind", "Ravenshold", "Evermoor"],
        "color": "cyan",
    },
    "Frostwind": {
        "id": 2,
        "continent": "North Kingdom", 
        "neighbors": ["Snowpeak", "Ravenshold", "Greystone"],
        "color": "cyan",
    },
    "Ravenshold": {
        "id": 3,
        "continent": "North Kingdom",
        "neighbors": ["Snowpeak", "Frostwind", "Greystone", "Evermoor"],
        "color": "cyan",
    },
    
    # Central Kingdom (3 territories)
    "Greystone": {
        "id": 4,
        "continent": "Central Kingdom",
        "neighbors": ["Frostwind", "Ravenshold", "Evermoor", "Willowdale", "Ironridge"],
        "color": "red",
    },
    "Evermoor": {
        "id": 5,
        "continent": "Central Kingdom",
        "neighbors": ["Ravenshold", "Greystone", "Willowdale", "Shadowmere", "Snowpeak"],
        "color": "red",
    },
    "Willowdale": {
        "id": 6,
        "continent": "Central Kingdom",
        "neighbors": ["Greystone", "Evermoor", "Ironridge", "Shadowmere", "Sunhaven"],
        "color": "red",
    },
    
    # South Kingdom (3 territories)
    "Ironridge": {
        "id": 7,
        "continent": "South Kingdom",
        "neighbors": ["Greystone", "Willowdale", "Sunhaven"],
        "color": "green",
    },
    "Sunhaven": {
        "id": 8,
        "continent": "South Kingdom",
        "neighbors": ["Willowdale", "Ironridge", "Shadowmere"],
        "color": "green",
    },
    "Shadowmere": {
        "id": 9,
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