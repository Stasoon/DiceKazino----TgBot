import asyncio
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from src.database.models import Withdraw, Deposit
from src.keyboards.admin import StatisticsKbs


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


async def __handle_show_transactions_stats(message: Message):
    await message.answer(
        text='За какой период отобразить статистику?',
        reply_markup=StatisticsKbs.get_()
    )
    print(message)
    await f()


async def __handle_show_game_transactions_stats(message: Messages):
    pass


def register_statistics_handlers(router: Router):
    router.message.register(__handle_show_transactions_stats, F.text == '📊 Статистика 📊')
    router.message.register(__handle_show_game_transactions_stats, F.text == '/gam')
