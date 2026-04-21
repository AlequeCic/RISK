from dataclasses import field, dataclass
from typing import List, Optional
from enum import Enum
import random

class CardSymbol(Enum):
    INFANTRY = 1
    CAVALRY = 2
    ARTILLERY = 3
    WILDCARD = 4

@dataclass
class Card:
    symbol: CardSymbol #enum type
    description: str
    territory: Optional[str]


@dataclass
class Territory:
    id: int
    name: str
    neighbors: List[str]
    continent: str
    troops: int
    owner: Optional[str] = None

@dataclass
class Player:
    id: int
    name: str
    color: str
    troops: int
    cards: List[Card] = field(default_factory=list)
    
class Dice:
    def __init__(self, color):
        self.color = color
        self.face = 1

    def roll(self) -> int:
        self.face = random.randint(1,6)
        return self.face

