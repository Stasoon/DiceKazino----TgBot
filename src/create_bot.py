from aiogram import Dispatcher, Bot

from settings import Config


bot = Bot(Config.TOKEN)
dp = Dispatcher()
