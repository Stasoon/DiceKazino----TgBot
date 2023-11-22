from typing import AsyncGenerator

from tortoise.exceptions import DoesNotExist

from .models import User


# Create
async def create_user_if_not_exists(
    telegram_id: int,
    first_name: str, username: str,
    referrer_telegram_id: int = None,
    balance: int = 0
) -> bool:
    defaults = {'name': first_name, 'username': username, 'balance': balance, 'referred_by_id': referrer_telegram_id}
    user, created = await User.get_or_create(telegram_id=telegram_id, defaults=defaults)

    # Если юзер существует, а name или username не заданы, указываем
    if not created:
        if not user.name: user.name = first_name
        if not user.username: user.username = username
        await user.save()

    return True if created else False


# Read

async def get_user_or_none(telegram_id: int) -> User | None:
    return await User.get_or_none(telegram_id=telegram_id)


async def get_user_balance(telegram_id: int) -> float:
    user = await get_user_or_none(telegram_id)
    return user.balance


async def add_referral(user_telegram_id: int, referrer_id: int):
    try:
        user = await User.get(telegram_id=user_telegram_id)
        referrer = await User.get(telegram_id=referrer_id)
    except DoesNotExist:
        return

    if user.referred_by:
        return

    user.referred_by = referrer
    await user.save()


async def get_referrer_id_of_user(user_id: int):
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return

    return user.referred_by_id


async def get_referrals_count_by_telegram_id(user_id: int):
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return None

    # Если пользователь найден, то получаем количество его рефералов
    if user:
        referrals_count = await user.referrals.all().count()
        return referrals_count
    else:
        return None


async def get_all_user_ids() -> AsyncGenerator[int, None]:
    async for user_id in User.all().values_list('telegram_id', flat=True):
        yield user_id


async def get_total_users_count() -> int:
    return await User.all().count()
