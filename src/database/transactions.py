from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterable

from tortoise.exceptions import DoesNotExist
from tortoise.functions import Sum

from .models import Transaction, TransactionType, User, Game, Referral
from .referrals import get_referrer_of_user
from src.misc import GameCategory
from settings import Config


# Create

async def accrue_winnings(game: Game, winner_telegram_id: int, amount: float) -> float:
    """Начисление выигрыша победителю и процента пригласившему"""
    if amount <= 0:
        return 0

    winning_commission = Decimal(1 - Config.Payments.winning_commission)
    amount_with_commission = Decimal(amount) * winning_commission

    user = await User.get(telegram_id=winner_telegram_id)
    user.balance += amount_with_commission
    await user.save()
    await Transaction.create(game=game, recipient=user, amount=amount_with_commission, type=TransactionType.WINNING)

    # увеличиваем баланс того, кто пригласил
    await accrue_referral_bonus(game, user, amount_with_commission)

    return float(amount_with_commission)


async def accrue_referral_bonus(game: Game, referred_user: User, winning_amount: Decimal):
    referral_bonus = winning_amount * Decimal(Config.Payments.percent_to_referrer)
    referrer = await get_referrer_of_user(referred_user.telegram_id)

    if referrer:
        # Начисляем бонус тому, кто пригласил юзера
        referrer.balance += referral_bonus
        await referrer.save()

        # Создаем запись о начислении бонуса в таблице транзакций
        await Transaction.create(
            recipient=referrer,
            sender=referred_user,
            amount=referral_bonus,
            type=TransactionType.REFERRAL,
            game=game
        )


async def debit_bet(game: Game, user_telegram_id: int, amount: float):
    """Списание ставки с баланса"""
    amount = Decimal(amount)
    user = await User.get(telegram_id=user_telegram_id)

    if 0 < amount <= user.balance:
        user.balance -= amount
        await user.save()

        transaction = await Transaction.create(game=game, recipient=user, amount=-amount, type=TransactionType.BET)
        return transaction
    else:
        return None


async def refund(players_telegram_ids: Iterable, amount: float, game: Game = None):
    """Возврат денег игрокам"""
    amount = Decimal(amount)
    for player_id in players_telegram_ids:
        try:
            player = await User.get(telegram_id=player_id)
            await Transaction.create(game=game, recipient=player, amount=amount, type=TransactionType.REFUND)
            player.balance += amount
            await player.save()
        except DoesNotExist:
            pass


async def deposit_to_user(user_id: int, amount: float):
    """Начислить депозит юзеру"""
    amount = Decimal(amount)
    user = await User.get_or_none(telegram_id=user_id)

    if user:
        user.balance += amount
        await user.save()

        await Transaction.create(recipient=user, amount=amount, type=TransactionType.DEPOSIT)


async def withdraw(user_id: int, amount: float):
    """Списать средства с баланса перед выводом"""
    user = await User.get_or_none(telegram_id=user_id)
    if user.balance < amount:
        raise ValueError("Недостаточно средств на балансе для списания.")

    amount = Decimal(amount)

    await Transaction.create(
        recipient=user,
        amount=- amount,
        type=TransactionType.WITHDRAW
    )

    user.balance -= amount
    await user.save()


# Read

async def get_user_all_withdraws_sum(user: User) -> float:
    """Получение суммы выводов пользователя"""
    withdrawal_amount = await Transaction.filter(
        recipient=user,
        type=TransactionType.WITHDRAW
    ).annotate(total_amount=Sum('amount')).values_list('total_amount')

    withdrawal_sum = withdrawal_amount[0][0]
    return abs(withdrawal_sum) if withdrawal_sum else 0.0


async def get_user_all_deposits_sum(user: User) -> float:
    """Получение суммы пополнений пользователя"""
    deposit_amount = await Transaction.filter(
        recipient=user,
        type=TransactionType.DEPOSIT
    ).annotate(total_amount=Sum('amount')).values_list('total_amount')

    deposits_sum = deposit_amount[0][0]
    return deposits_sum if deposits_sum else 0.0


async def get_referral_earnings(user_telegram_id: int) -> float:
    """Получить сумму, полученную от рефералов"""
    deposit_amount = await Transaction.filter(
        recipient=user_telegram_id, type=TransactionType.REFERRAL
    ).annotate(total_amount=Sum('amount')).values_list('total_amount')

    deposits_sum = deposit_amount[0][0]
    return deposits_sum if deposits_sum else 0.0


async def get_users_with_top_winnings(category: GameCategory, days_back: int = None, limit: int = 3):
    """Возвращает юзеров с наибольшими суммами выигрыша в конкретной категории игр"""
    query = User.filter(
        # тип транзакции - выигрыш, категория игр - запрашиваемая
        received_transactions__type=TransactionType.WINNING, received_transactions__game__category=category
    )

    if days_back:
        start_date = datetime.now() - timedelta(days=days_back)
        query = query.filter(received_transactions__timestamp__gte=start_date)

    users = await query.annotate(
        total_bet=Sum('received_transactions__amount')
    ).order_by('-total_bet').limit(limit)  # сортируем по количеству и получаем первые несколько

    return users
