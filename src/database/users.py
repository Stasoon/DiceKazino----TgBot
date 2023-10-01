from typing import AsyncGenerator

from .models import User


# Create
async def create_user_if_not_exists(first_name: str, username: str, telegram_id: int) -> bool:
    defaults = {'name': first_name, 'username': username, 'balance': 0}
    user, created = await User.get_or_create(telegram_id=telegram_id, defaults=defaults)
    return True if created else False


# Read

async def get_user_or_none(telegram_id: int) -> User | None:
    return await User.get_or_none(telegram_id=telegram_id)


async def get_user_balance(telegram_id: int) -> float:
    user = await get_user_or_none(telegram_id)
    return user.balance


async def get_all_user_ids() -> AsyncGenerator[int, None]:
    async for user_id in User.all().values_list('telegram_id', flat=True):
        yield user_id


async def get_total_users_count() -> int:
    return await User.all().count()
