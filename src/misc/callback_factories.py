from typing import Optional, Literal

from aiogram.filters.callback_data import CallbackData

from .enums import PaymentMethod, GameType, GameCategory


class BlackJackCallback(CallbackData, prefix='BJ'):
    """
    game_number: int \n
    move: Literal['take', 'stand']
    """
    game_number: int
    move: Literal['take', 'stand']


class GamesCallback(CallbackData, prefix="games"):
    """
    action: str  \n
    game_number: Optional[int] = None  \n
    game_category: Optional[GameCategory] = None  \n
    game_type: Optional[GameType] = None
    """
    action: Literal['create', 'show', 'refresh', 'stats', 'cancel', 'join']
    game_number: Optional[int] = None
    game_category: Optional[GameCategory] = None
    game_type: Optional[GameType] = None


class GamePagesNavigationCallback(CallbackData, prefix='games_nav'):
    direction: Literal['prev', 'next']
    category: GameCategory
    current_page: int = 0


class MenuNavigationCallback(CallbackData, prefix="nav"):
    """
    Отвечает за навигацию в основных ветках меню. Если option не задана, возврат в ветку
    branch: str
    option: Optional[str] = None
    """
    branch: str  # play / profile / info / ...
    option: Optional[str] = None


class BalanceTransactionCallback(CallbackData, prefix='balance_transaction'):
    """Отвечает за выбор метода пополнения/депозита"""
    transaction_type: Literal['deposit', 'withdraw']
    method: PaymentMethod
    currency: Optional[str] = None


class PaymentCheckCallback(CallbackData, prefix='check_payment'):
    """Отвечает за кнопку проверки платежа при автооплате"""
    method: PaymentMethod
    invoice_id: int


class ConfirmWithdrawRequisitesCallback(CallbackData, prefix='confirm_withdraw_requisites'):
    """
    Отвечает за подтверждение отправки запроса на вывод средств \n
    requisites_correct: bool
    """
    requisites_correct: bool


class AdminValidatePaymentCallback(CallbackData, prefix='confirm_payment'):
    """
    Отвечает за отклонение или подтверждение оплаты у админа \n
    user_id: int \n
    amount: float \n
    transaction_type: Literal['deposit', 'withdraw'] \n
    confirm: bool
    """
    user_id: int
    amount: float
    transaction_type: Literal['deposit', 'withdraw']
    confirm: bool
