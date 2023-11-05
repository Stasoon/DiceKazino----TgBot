from decimal import Decimal

from tortoise.functions import Sum

from settings import Config
from ..models import ReferralBonus
from ..users import get_referrer_id_of_user, get_user_or_none


async def accrue_referral_bonus(referred_user_id: int, game_winning_amount: Decimal):
    """Начислить реферальный бонус"""
    referral_bonus = game_winning_amount * Decimal(Config.Payments.percent_to_referrer)

    referrer_id = await get_referrer_id_of_user(user_id=referred_user_id)
    referrer = await get_user_or_none(referrer_id)

    if not referrer:
        return

    # Начисляем бонус тому, кто пригласил юзера
    referrer.balance += referral_bonus
    await referrer.save()

    # Создаем запись о начислении бонуса в таблице транзакций
    await ReferralBonus.create(
        recipient=referrer,
        referral_id=referred_user_id,
        amount=referral_bonus
    )


async def get_referral_earnings(user_telegram_id: int) -> float:
    """Получить сумму, полученную от рефералов"""
    deposit_amount = await ReferralBonus.filter(
        recipient_id=user_telegram_id
    ).annotate(total_amount=Sum('amount')).values_list('total_amount')

    deposits_sum = deposit_amount[0][0]
    return deposits_sum if deposits_sum else 0.0
