import os
from typing import Final
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class Config:
    class Bot:
        TOKEN: Final[str] = os.getenv('BOT_TOKEN', 'define me')
        OWNER_IDS: Final[tuple] = tuple(int(i) for i in str(os.getenv('BOT_OWNER_IDS')).split(','))

    class Payments:
        CRYPTO_BOT_TOKEN: Final[str] = os.getenv('CRYPTO_BOT_TOKEN')
        DEPOSITS_CHANNEL_ID: Final[int] = int(os.getenv('DEPOSITS_CHANNEL_ID'))
        WITHDRAWS_CHANNEL_ID: Final[int] = int(os.getenv('WITHDRAWS_CHANNEL_ID'))

        percent_to_referrer: Final[float] = float(0.05)
        winning_commission: Final[float] = float(0.05)

        min_withdraw_amount: Final[float] = float(50)
        min_deposit_amount: Final[float] = float(10)

    class Games:
        GAME_CHAT_ID: Final[int] = str(os.getenv('GAME_CHAT_ID'))
        CARD_IMAGES_PATH: str = 'cards'
        min_bet_amount: Final[float] = float(30)

    class Database:
        DB_URL: Final = os.getenv('DB_URL')

    DEBUG: Final = bool(os.getenv('DEBUG'))
