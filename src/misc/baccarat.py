from enum import Enum
from typing import Collection
from dataclasses import dataclass

from src.utils.cards import Card


class BettingOption(Enum):
    PLAYER = 1
    TIE = 2
    BANKER = 3


@dataclass
class BaccaratResult:
    player_points: int
    player_cards: Collection[Card]

    banker_points: int
    banker_cards: Collection[Card]

    winner: BettingOption = None
