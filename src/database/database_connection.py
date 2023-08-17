from tortoise import Tortoise

from settings import Config
from src.utils import logger


async def start_database():
    await Tortoise.init(
        db_url=Config.DB_URL,
        modules={"models": ["src.database.models"]},
    )

    try:
        await Tortoise.generate_schemas()
    except Exception as e:
        logger.error(f'Ошибка при подключении к БД: {e}')


async def stop_database():
    await Tortoise.close_connections()

