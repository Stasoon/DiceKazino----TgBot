from abc import ABC, abstractmethod
from typing import Literal

from aiogram.utils.keyboard import InlineKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardMarkup, InlineKeyboardBuilder, ReplyKeyboardBuilder

from src.misc import AdminValidatePaymentCallback


class AdminKeyboardBase(ABC):
    @staticmethod
    @abstractmethod
    def get_button_for_admin_menu() -> KeyboardButton:
        pass


class AdminKeyboards:
    @classmethod
    def get_admin_menu(cls) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()

        for keyboard in AdminKeyboardBase.__subclasses__():
            builder.add(keyboard.get_button_for_admin_menu())

        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def get_accept_or_reject_transaction(transaction_type: Literal['deposit', 'withdraw'],
                                         user_id: int, amount: float) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='✅', callback_data=AdminValidatePaymentCallback(
            user_id=user_id, amount=amount, transaction_type=transaction_type, confirm=True))
        builder.button(text='❌', callback_data=AdminValidatePaymentCallback(
            user_id=user_id, amount=amount, transaction_type=transaction_type, confirm=False))
        return builder.as_markup()
