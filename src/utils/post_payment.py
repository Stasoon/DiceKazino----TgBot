from typing import Optional

from aiogram import Bot

from settings import Config
from src.messages.admin import AdminMessages
from src.keyboards.admin import AdminKeyboards
from src.misc import TransactionType, PaymentMethod


async def send_payment_request_to_admin(
        bot: Bot,
        user_id: int,
        amount: float,
        transaction_type: TransactionType,
        method: PaymentMethod,
        requisites: str = None,
        photo_file_id: Optional[str] = None):

    if transaction_type not in (TransactionType.DEPOSIT, TransactionType.WITHDRAW):
        raise ValueError

    reply_markup = AdminKeyboards.get_accept_or_reject_transaction(transaction_type, user_id, amount)

    if photo_file_id:
        await bot.send_photo(
            chat_id=Config.Payments.PAYMENTS_CHANNEL_ID,
            caption=AdminMessages.get_deposit_request(transaction_type, user_id, amount, method, requisites),
            photo=photo_file_id,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await bot.send_message(
            chat_id=Config.Payments.PAYMENTS_CHANNEL_ID,
            text=AdminMessages.get_deposit_request(transaction_type, user_id, amount, method, requisites),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
