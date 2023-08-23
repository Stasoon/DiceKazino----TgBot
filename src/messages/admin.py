from datetime import datetime

from aiogram import html

from src.misc import TransactionType, PaymentMethod


class AdminMessages:
    @staticmethod
    def get_deposit_request(transaction_type: TransactionType,
                            user_id: int, amount: float,
                            method: PaymentMethod = None,
                            user_requisites: str = None):

        transaction_str = f'➕ Пополнение баланса ➕' \
            if transaction_type == TransactionType.DEPOSIT \
            else f'➖ Вывод средств ➖'
        user_requisites_str = f'💳 Реквизиты: \n{user_requisites} \n' if user_requisites else ''

        return f'{html.bold(transaction_str)} \n\n' \
               f'{html.link("Пользователь", f"tg://user?id=5056957097")}' \
               f'👤 {html.link("Пользователь", f"tg://user?id={user_id}")} \n' \
               f'🆔 {html.code(user_id)} \n\n' \
               f'📆 {html.italic(datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M"))} \n' \
               f'🏦 Метод: {method.value} \n' \
               f'{user_requisites_str}' \
               f'💵 Сумма: {html.code(amount)} ₽'
