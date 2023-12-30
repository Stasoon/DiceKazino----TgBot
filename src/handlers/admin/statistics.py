import asyncio
from datetime import datetime, timedelta, date

import matplotlib.pyplot as plt
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from src.database.models import Withdraw, Deposit
from src.keyboards.admin import StatisticsKbs
from collections import defaultdict

from src.utils.text_utils import format_float_to_rub_string


class Messages:
    pass


async def f():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Например, данные за последнюю неделю

    # Получите пополнения и выводы из базы данных за указанный период
    deposit_transactions = await Deposit.filter(timestamp__gte=start_date, timestamp__lte=end_date).order_by('timestamp')

    # Создайте словари для агрегации сумм по датам
    deposit_amounts = {}

    # Агрегируйте суммы пополнений и выводов по датам
    for transaction in deposit_transactions:
        date = str(transaction.timestamp.date())
        deposit_amounts[date] = deposit_amounts.get(date, 0) + transaction.amount

    # Создайте списки дат и сумм для построения графика
    dates = list(str(date) for date in deposit_amounts.keys())
    deposit_amounts_list = [deposit_amounts[date] for date in dates]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, deposit_amounts_list, label='Сумма', marker='o')
    plt.xlabel('Дата')
    plt.ylabel('Сумма')
    plt.title('График пополнений')
    plt.legend()
    plt.grid(True)


async def get_stats(model: Deposit | Withdraw, days_back: int):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    transactions = (
        await model
        .filter(timestamp__gte=start_date, timestamp__lte=end_date)
        .order_by('timestamp')
    )

    global_sum = sum(t.amount for t in transactions)
    unique_count = len({t.user for t in transactions})

    return (
        f"{f'Пополнения' if isinstance(model, Deposit) else 'Выводы'} средств за {days_back} дней \n\n"
        f"Общая сумма: {format_float_to_rub_string(global_sum)} \n"
        f"Количество транзакций: {len(transactions)} \n"
        f"Уникальных транзакций: {unique_count}"
    )


async def __handle_show_transactions_stats(message: Message):

    s = (1, 7, 30)
    n = (Deposit, Withdraw)

    for j in n:
        for i in s:
            text = await get_stats(model=j, days_back=i)
            await message.answer(text=text)


async def __handle_show_game_transactions_stats(message: Messages):
    pass


def register_statistics_handlers(router: Router):
    router.message.register(__handle_show_transactions_stats, F.text == '📊 Статистика 📊')
    router.message.register(__handle_show_game_transactions_stats, F.text == '/gam')
