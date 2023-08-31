from enum import IntEnum, Enum


class TransactionType(str, Enum):
    WITHDRAW = 'withdraw'
    DEPOSIT = 'deposit'
    TRANSFER = 'transfer'
    REFERRAL = 'referral'
    WINNING = 'winning'
    LOOSE = 'loose'
    BET = 'bet'
    REFUND = 'refund'


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
            case GameType.DICE:
                return "Кости"
            case GameType.CASINO:
                return "Слоты"
            case GameType.DARTS:
                return "Дартс"
            case GameType.BOWLING:
                return "Боулинг"
            case GameType.BASKETBALL:
                return "Баскетбол"
            case GameType.FOOTBALL:
                return "Футбол"
            case GameType.BJ:
                return 'BlackJack'
            case GameType.BACCARAT:
                return 'Баккарат'
            case _:
                return "Игра"


class GameStatus(IntEnum):
    CANCELED = -1
    WAIT_FOR_PLAYERS = 0
    ACTIVE = 1
    FINISHED = 2

    def __str__(self):
        return '0 - Wait for players' \
               '1 - Active' \
               '2 - Finished' \
               '-1 - Canceled'


class PaymentMethod(Enum):
    CRYPTO_BOT = 'КриптоБот'
    SBP = 'СБП'
    U_MONEY = 'ЮMoney'
