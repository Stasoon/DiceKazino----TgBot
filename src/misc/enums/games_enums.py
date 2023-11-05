from enum import IntEnum, Enum
from typing import Final


EvenUnevenCoefficients: Final = {
    "A": 1.5,
    "B": 1.5,
    "C": 1.5,
    "D": 1.5,
    "E": 2.5,
    "F": 2.5,
    "G": 5,
    "H": 5
}


class BaccaratBettingOption(IntEnum):
    PLAYER = 1
    TIE = 2
    BANKER = 3


class GameCategory(str, Enum):
    BASIC = 'Игры'
    BLACKJACK = 'BlackJack'
    BACCARAT = 'Baccarat'


class GameType(str, Enum):
    """Эмодзи с типом игры"""
    DICE = '🎲'
    CASINO = '🎰'
    DARTS = '🎯'
    BOWLING = '🎳'
    BASKETBALL = '🏀'
    FOOTBALL = '⚽'
    BJ = '♠'
    BACCARAT = '🎴'

    def get_full_name(self) -> str:
        """Возвращает строку с полным именем игры"""
        match self:
            case GameType.DICE: return "Кости"
            case GameType.CASINO: return "Слоты"
            case GameType.DARTS: return "Дартс"
            case GameType.BOWLING: return "Боулинг"
            case GameType.BASKETBALL: return "Баскетбол"
            case GameType.FOOTBALL: return "Футбол"
            case GameType.BJ: return 'BlackJack'
            case GameType.BACCARAT: return 'Баккарат'
            case _: return "Игра"


class GameStatus(IntEnum):
    CANCELED = -1
    WAIT_FOR_PLAYERS = 0
    ACTIVE = 1
    FINISHED = 2
