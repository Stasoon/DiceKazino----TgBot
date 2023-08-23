from aiogram.types import BotCommandScopeAllGroupChats, BotCommand

from src import bot, dp
from src.handlers import register_all_handlers
from src.database.database_connection import start_database, stop_database
from settings import Config
from src.utils import logger


async def set_bot_commands():
    await bot.set_my_commands(commands=[BotCommand(command='start', description='Запуск бота')])

    await bot.set_my_commands(
        scope=BotCommandScopeAllGroupChats(),
        commands=[
            BotCommand(command='profile', description='Информация о профиле'),
            BotCommand(command='mygames', description='Незавершённые игры'),
        ]
    )


async def on_startup():
    # Запуск базы данных
    await start_database()

    # Установка команд в боте
    await set_bot_commands()

    # Регистрация хэндлеров
    register_all_handlers(dp)

    logger.info('Бот запущен!')


async def on_shutdown(_):
    await stop_database()
    if not Config.DEBUG:
        for admin_id in Config.Bot.OWNER_IDS:
            await bot.send_message(chat_id=admin_id, text='<b>Бот остановлен!</b>')


async def start_bot():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await bot.delete_webhook(drop_pending_updates=False)

    try:
        await dp.start_polling(bot, close_bot_session=True)
    except Exception as e:
        logger.exception(e)
