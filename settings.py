import os
from typing import Final
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class Config:
    TOKEN: Final = os.getenv('BOT_TOKEN', 'define me')
    OWNER_IDS: Final = tuple(int(i) for i in str(os.getenv('BOT_OWNER_IDS')).split(','))
    CHAT_USERNAME: Final = os.getenv('GAME_CHAT_USERNAME')

    DB_URL: Final = os.getenv('DB_URL')
    SQLITE_STORAGE_PATH = 'game_storage.db'

    DEBUG: Final = bool(os.getenv('DEBUG'))


percent_to_referrer = 0.05
