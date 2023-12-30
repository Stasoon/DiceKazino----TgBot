from datetime import datetime
from typing import Literal

from aiogram import html

from src.misc import WithdrawMethod, DepositMethod


class AdminMessages:

    @staticmethod
    def get_deposit_request(
            transaction_type: Literal['deposit', 'withdraw'],
            user_id: int,
            amount: float,
            user_name: str = 'Пользователь',
            user_requisites: str = None,
            method: DepositMethod | WithdrawMethod = None
    ):

        if transaction_type == 'deposit':
            transaction_str = f'➕ Пополнение баланса ➕'
        else:
            transaction_str = f'➖ Вывод средств ➖'
        user_requisites_str = f'💳 Реквизиты: \n{user_requisites} \n' if user_requisites else ''

        return f'{html.bold(transaction_str)} \n\n' \
               f'👤 {html.link(f"{user_name}", f"tg://user?id={user_id}")} \n' \
               f'🆔 {html.code(user_id)} \n\n' \
               f'📆 {html.italic(datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M"))} \n' \
               f'🏦 Метод: {method.value} \n' \
               f'{user_requisites_str}' \
               f'💵 Сумма: {html.code(amount)} ₽'
