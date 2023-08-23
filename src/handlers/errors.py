from aiogram import Dispatcher
from aiogram.types import Update
from src.utils import logger


async def handle_errors(update: Update, exception: Exception):
    logger.error(f'Ошибка при обработке запроса {update}: {exception}')


def register_errors_handler(dp: Dispatcher):
    dp.error(handle_errors)
