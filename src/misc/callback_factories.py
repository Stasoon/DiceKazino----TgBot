from typing import Optional

from aiogram.filters.callback_data import CallbackData

from .enums import TransactionType, PaymentMethod


class GamesCallback(CallbackData, prefix="games"):
    """number: int, action: str"""
    game_number: int
    action: str  # join / show / refresh / create


class NavigationCallback(CallbackData, prefix="nav"):
    """Отвечает за навигацию в основных ветках меню. Если option не задана, возврат в ветку"""
    branch: str  # play / profile / info
    option: Optional[str] = None


class BalanceTransactionCallback(CallbackData, prefix='balance_transaction'):
    """Отвечает за выбор метода пополнения/депозита"""
    transaction_type: TransactionType
    method: PaymentMethod
    currency: Optional[str] = None


class PaymentCheckCallback(CallbackData, prefix='check_payment'):
    """Отвечает за кнопку проверки платежа при автооплате"""
    method: PaymentMethod
    invoice_id: int


class ConfirmWithdrawRequisitesCallback(CallbackData, prefix='confirm_withdraw_requisites'):
    """Отвечает за подтверждение отправки запроса на вывод средств \n
    Параметры: requisites_correct: bool"""
    requisites_correct: bool


class AdminValidatePaymentCallback(CallbackData, prefix='confirm_payment'):
    """
    Отвечает за отклонение или подтверждение оплаты у админа \n
    Параметры: \n
    user_id - int \n
    amount - float \n
    transaction_type - TransactionType.DEPOSIT или TransactionType.WITHDRAW \n
    confirm' - bool
    """
    user_id: int
    amount: float
    transaction_type: TransactionType
    confirm: bool
