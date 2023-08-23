from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from settings import Config


bot = Bot(token=Config.Bot.TOKEN)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
