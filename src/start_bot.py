import asyncio

from aiogram.types import BotCommandScopeAllGroupChats, BotCommand

from src import bot, dp
from src.handlers import register_all_handlers
from src.database.database_connection import start_database, stop_database
from src.database.models import Band
from src.database import bands
from src.handlers.user.chat.games_process.even_uneven_loop import start_even_uneven_loop
from settings import Config
from src.utils import logger


async def set_bot_commands():
    await bot.set_my_commands(commands=[BotCommand(command='start', description='Запуск бота')])

    await bot.set_my_commands(
        scope=BotCommandScopeAllGroupChats(),
        commands=[
            BotCommand(command='profile', description='Информация о профиле'),
            BotCommand(command='mygames', description='Мои незавершённые игры'),
            BotCommand(command='allgames', description='Незавершённые игры чата'),
        ]
    )


async def send_league_updated(band: Band, *args, **kwargs):
    for member in await bands.get_band_members(band_id=band.id):
        await bot.send_message(
            chat_id=member.telegram_id,
            text=f'Поздравляю! Твоя банда перешла в новую лигу: {band.league}'
        )


async def on_startup():
    # Запуск базы данных
    await start_database(db_url=Config.Database.DATABASE_URL)

    # Установка команд бота
    await set_bot_commands()

    # Функция, вызываемая при переходе банды в новую лигу
    Band.on_league_changed = send_league_updated

    # Регистрация хэндлеров
    register_all_handlers(dp)

    # Запускаем бесконечное обновление even uneven
    asyncio.create_task(start_even_uneven_loop(bot, Config.Games.EVEN_UNEVEN_CHAT_ID))

    logger.info('Бот запущен!')


async def on_shutdown():
    await stop_database()
    logger.info('Бот остановлен')

    # if not Config.DEBUG:
    #     for admin_id in Config.Bot.OWNER_IDS:
    #         await bot.send_message(chat_id=admin_id, text='<b>Бот остановлен!</b>')


async def start_bot():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await bot.delete_webhook(drop_pending_updates=False)

    try:
        # Запускаем поллинг
        await dp.start_polling(bot, close_bot_session=True)
    except Exception as e:
        logger.exception(e)

