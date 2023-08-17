from decimal import Decimal

from tortoise.exceptions import DoesNotExist

from .models import User
from settings import percent_to_referrer


# Create
async def create_user_if_not_exists(first_name: str, username: str, telegram_id: int) -> bool:
    defaults = {'name': first_name, 'username': username, 'balance': 0}
    user, created = await User.get_or_create(telegram_id=telegram_id, defaults=defaults)
    return True if created else False


# Read

async def is_user_exists(telegram_id):
    telegram_id = int(telegram_id)
    user = await User.get_or_none(telegram_id=telegram_id)
    return user


async def get_user_obj(telegram_id: int) -> User | None:
    return await User.get_or_none(telegram_id=telegram_id)


async def get_user_balance(telegram_id: int) -> float:
    user = await get_user_obj(telegram_id)
    return user.balance


async def get_total_users_count() -> int:
    return await User.all().count()


# Update
async def increase_user_balance(telegram_id: int, value: float):
    value = Decimal(value)
    user = await User.get(telegram_id=telegram_id)
    user.balance += value
    await user.save()

    # увеличиваем баланс того, кто пригласил
    referrer = await user.referrals.all().first()
    if referrer:
        referrer.balance += value * percent_to_referrer
        await referrer.save()


async def reduce_user_balance(telegram_id: int, value: float) -> bool:
    value = Decimal(value)
    user = await User.get(telegram_id=telegram_id)

    if user.balance - value > 0:
        user.balance -= value
        await user.save()
        return True
    else:
        return False
