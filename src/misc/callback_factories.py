from typing import Optional
from aiogram.filters.callback_data import CallbackData


class GamesCallbackFactory(CallbackData, prefix="games"):
    number: int
    action: Optional[str]

