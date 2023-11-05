from enum import Enum


class PaymentMethod(str, Enum):
    CRYPTO_BOT = 'КриптоБот'
    SBP = 'СБП'
    U_MONEY = 'ЮMoney'


class BonusType(Enum):
    ON_BALANCE = 'on_balance'
