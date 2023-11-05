from decimal import Decimal

from tortoise.functions import Sum

from ..models import User, Deposit


async def deposit_to_user(user_id: int, amount: float):
    """Начислить депозит юзеру"""
    amount = Decimal(amount)
    user = await User.get_or_none(telegram_id=user_id)

    if not user:
        return

    user.balance += amount
    await user.save()
    await Deposit.create(user=user, amount=amount)


async def get_user_all_deposits_sum(user: User) -> float:
    """Получение суммы пополнений пользователя"""
    deposit_amount = await Deposit.filter(
        user=user
    ).annotate(total_amount=Sum('amount')).values_list('total_amount')

    deposits_sum = deposit_amount[0][0]
    return deposits_sum if deposits_sum else 0.0
