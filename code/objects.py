from dataclasses import field, dataclass
from typing import List, Optional
import random

@dataclass
class Card:
    symbol: str
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
    cards: List[Card] = field(default_factory=list)
    troops: int

class Dice:
    def __init__(self, color):
        self.color = color
        self.face = 1

    def roll(self) -> int:
        self.face = random.randint(1,6)
        return self.face

