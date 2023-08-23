from enum import IntEnum, Enum


class TransactionType(Enum):
    WITHDRAW = 'withdraw'
    DEPOSIT = 'deposit'
    TRANSFER = 'transfer'
    REFERRAL = 'referral'
    WINNING = 'winning'
    LOOSE = 'loose'
    BET = 'bet'


class GameType(Enum):
    """Эмодзи с типом игры"""

    DICE = '🎲'
    CASINO = '🎰'
    DARTS = '🎯'
    BOWLING = '🎳'
    BASKETBALL = '🏀'
    FOOTBALL = '⚽'


class GameStatus(IntEnum):
    WAIT_FOR_PLAYERS = 0
    ACTIVE = 1
    FINISHED = 2
    CANCELED = 3

    def __str__(self):
        return '0 - Wait for players' \
               '1 - Active' \
               '2 - Finished' \
               '3 - Canceled'


class PaymentMethod(Enum):
    CRYPTO_BOT = 'КриптоБот'
    SBP = 'СБП'
    U_MONEY = 'ЮMoney'
