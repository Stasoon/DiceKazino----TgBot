from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import (InlineKeyboardMarkup, InlineKeyboardBuilder)

from src.misc import (NavigationCallback, PaymentCheckCallback, TransactionType,
                      BalanceTransactionCallback, PaymentMethod, ConfirmWithdrawRequisitesCallback)
from src.utils import cryptobot


class UserPaymentKeyboards:
    @staticmethod
    def get_cancel_payment() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
            is_persistent=True
        )

    @staticmethod
    def get_payment_methods(transaction_type: TransactionType) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру с методами пополнения"""
        builder = InlineKeyboardBuilder()

        builder.button(
            text='💳 СБП',
            callback_data=BalanceTransactionCallback(
                transaction_type=transaction_type, method=PaymentMethod.SBP
            )
        )
        builder.button(
            text='🤖 КриптоБот',
            callback_data=BalanceTransactionCallback(
                transaction_type=transaction_type, method=PaymentMethod.CRYPTO_BOT
            )
        )
        builder.button(
            text='💜 ЮMoney',
            callback_data=BalanceTransactionCallback(
                transaction_type=transaction_type, method=PaymentMethod.U_MONEY
            )
        )

        builder.adjust(2)
        back_builder = InlineKeyboardBuilder()
        back_builder.button(text='🔙 Назад', callback_data=NavigationCallback(branch='profile'))
        return builder.attach(back_builder).as_markup()

    @staticmethod
    def get_confirm_withdraw_requisites() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='✅ Отправить', callback_data=ConfirmWithdrawRequisitesCallback(requisites_correct=True))
        builder.button(text='✏ Изменить реквизиты',
                       callback_data=ConfirmWithdrawRequisitesCallback(requisites_correct=False))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def get_cryptobot_choose_currency(transaction_type: TransactionType) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться после нажатия на метод оплаты Крипто Ботом"""
        currency_builder = InlineKeyboardBuilder()

        currencies = await cryptobot.get_currencies()
        for code in currencies:
            currency_builder.button(
                text=code, callback_data=BalanceTransactionCallback(
                    transaction_type=transaction_type,
                    method=PaymentMethod.CRYPTO_BOT, currency=code)
            )
        currency_builder.adjust(4)

        back_builder = InlineKeyboardBuilder()
        back_builder.button(text='🔙 Отмена', callback_data=NavigationCallback(branch='profile', option='deposit'))
        back_builder.adjust(1)

        currency_builder.attach(back_builder)
        return currency_builder.as_markup()

    @staticmethod
    def get_invoice(method: PaymentMethod, pay_url: str, invoice_id: int) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для оплаты и её проверки"""
        builder = InlineKeyboardBuilder()
        builder.button(text='Оплатить', url=pay_url)
        builder.button(text='Проверить', callback_data=PaymentCheckCallback(method=method, invoice_id=invoice_id))
        builder.adjust(1)
        return builder.as_markup()
