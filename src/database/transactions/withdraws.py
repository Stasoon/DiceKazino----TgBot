from decimal import Decimal

from tortoise.functions import Sum

from ..models import User, Withdraw


async def withdraw_balance(user_id: int, amount: float):
    """Списать средства с баланса перед выводом"""
    user = await User.get_or_none(telegram_id=user_id)
    if user.balance < amount:
        raise ValueError("Недостаточно средств на балансе для списания.")

    amount = Decimal(amount)

    user.balance -= amount
    await user.save()

    await Withdraw.create(user=user, amount=amount)


async def get_user_all_withdraws_sum(user: User) -> float:
    """Получение суммы выводов пользователя"""
    withdrawal_amount = await Withdraw.filter(
        user=user
    ).annotate(total_amount=Sum('amount')).values_list('total_amount')

    withdrawal_sum = withdrawal_amount[0][0]
    return abs(withdrawal_sum) if withdrawal_sum else 0.0
