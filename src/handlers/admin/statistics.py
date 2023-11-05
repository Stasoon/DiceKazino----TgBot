import asyncio
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from aiogram import Router, F

from src.database.models import Withdraw, Deposit


class Messages:
    pass


async def get_transactions_for_day(model, target_date):
    # Выполняем запрос к базе данных для конкретной таблицы и даты
    transactions = await model.filter(timestamp__date=target_date.date())
    # Разделяем данные на депозиты и выводы
    deposit_amounts = [transaction.amount for transaction in transactions if transaction.amount > 0]
    withdraw_amounts = [transaction.amount for transaction in transactions if transaction.amount < 0]
    # Получаем даты из записей
    dates = [transaction.timestamp for transaction in transactions]

    return dates, deposit_amounts, withdraw_amounts


async def __handle_show_transactions_stats(message: Messages):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Например, данные за последнюю неделю
    print(start_date, end_date)

    # Получите пополнения и выводы из базы данных за указанный период
    deposit_transactions = await Deposit.filter(timestamp__gte=start_date, timestamp__lte=end_date)
    withdraw_transactions = await Withdraw.filter(timestamp__gte=start_date, timestamp__lte=end_date)

    # Создайте словари для агрегации сумм по датам
    deposit_amounts = {}
    withdraw_amounts = {}

    # Агрегируйте суммы пополнений и выводов по датам
    for transaction in deposit_transactions:
        date = transaction.timestamp.date()
        deposit_amounts[date] = deposit_amounts.get(date, 0) + transaction.amount

    for transaction in withdraw_transactions:
        date = transaction.timestamp.date()
        withdraw_amounts[date] = withdraw_amounts.get(date, 0) + transaction.amount

    # Создайте списки дат и сумм для построения графика
    dates = list(deposit_amounts.keys())
    deposit_amounts_list = [deposit_amounts[date] for date in dates]
    withdraw_amounts_list = [withdraw_amounts.get(date, 0) for date in dates]

    # Теперь у вас есть списки dates, deposit_amounts_list и withdraw_amounts_list,
    # которые вы можете использовать для построения графика.

    # Создайте график
    plt.figure(figsize=(10, 6))
    plt.plot(dates, [500, 1500, 186, 986], label='Пополнения', marker='o')
    plt.plot(dates, [90, 826, 456, 813], label='Выводы', marker='o')
    plt.xlabel('Дата')
    plt.ylabel('Сумма')
    plt.title('График пополнений и выводов')
    plt.legend()
    plt.grid(True)
    plt.show()


async def __handle_show_game_transactions_stats(message: Messages):
    pass


def register_statistics_handlers(router: Router):
    router.message.register(__handle_show_transactions_stats, F.text == '/tran')
    router.message.register(__handle_show_game_transactions_stats, F.text == '/gam')
