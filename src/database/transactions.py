from decimal import Decimal

from .models import Transaction, TransactionType, User
from settings import Config


async def accrue_winnings(user_telegram_id: int, amount: float):
    """Начисление выигрыша победителю и процента пригласившему"""
    amount = Decimal(amount)
    user = await User.get(telegram_id=user_telegram_id)

    if amount > 0:
        user.balance += amount
        await user.save()

        transaction = await Transaction.create(user=user, amount=amount, type=TransactionType.WINNING)

        # увеличиваем баланс того, кто пригласил
        referrer = await user.referrals.all().first()
        if referrer:
            amount_to_referrer = amount * Decimal(Config.Payments.percent_to_referrer)
            referrer.balance += amount_to_referrer
            await referrer.save()
            await Transaction.create(user=referrer, amount=amount_to_referrer, type=TransactionType.REFERRAL)
        return transaction
    else:
        return None


async def debit_bet(user_telegram_id: int, amount: float):
    """Списание ставки с баланса"""
    amount = Decimal(amount)
    user = await User.get(telegram_id=user_telegram_id)

    if 0 < amount <= user.balance:
        user.balance -= amount
        await user.save()

        transaction = await Transaction.create(user=user, amount=-amount, type=TransactionType.BET)
        return transaction
    else:
        return None


async def deposit_to_user(user_id: int, amount: float):
    """Начислить депозит юзеру"""
    amount = Decimal(amount)
    user = await User.get_or_none(telegram_id=user_id)

    if user:
        user.balance += amount
        await user.save()

        await Transaction.create(user=user, amount=amount, type=TransactionType.DEPOSIT)


async def withdraw(user_id: int, amount: float):
    """Списать средства с баланса перед выводом"""
    user = await User.get_or_none(telegram_id=user_id)
    if user.balance < amount:
        raise ValueError("Недостаточно средств на балансе для списания.")

    amount = Decimal(amount)

    await Transaction.create(
        user=user,
        amount=-amount,
        type=TransactionType.WITHDRAW
    )

    user.balance -= amount
    await user.save()


async def get_user_all_withdraws_sum(user: User) -> float:
    """Получение суммы выводов пользователя"""
    withdrawals = await Transaction.filter(
        user=user,
        type=TransactionType.WITHDRAW
    ).all()

    withdrawal_amount = abs(sum([withdrawal.amount for withdrawal in withdrawals]))
    return withdrawal_amount


async def get_user_all_deposits_sum(user: User) -> float:
    """Получение суммы пополнений пользователя"""
    deposits = await Transaction.filter(
        user=user,
        type=TransactionType.DEPOSIT
    ).all()

    deposit_amount = sum([deposit.amount for deposit in deposits])
    return deposit_amount


async def get_referral_earnings(user_telegram_id: int) -> float:
    """Получить сумму, полученную от рефералов"""
    user = await User.get_or_none(telegram_id=user_telegram_id)

    if user is None:
        return 0

    await user.fetch_related('referrals')
    referrals = await user.referrals.all()

    referral_earnings = 0
    for referral in referrals:
        referral_transactions = await Transaction.filter(
            user=referral.referred_user_id,
            type=TransactionType.REFERRAL
        ).all()

        referral_earnings += sum([transaction.amount for transaction in referral_transactions])

    return referral_earnings

