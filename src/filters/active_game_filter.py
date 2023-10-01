from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from src.database.games import get_user_active_game

from src.utils import logger


class ActiveGameFilter(BaseFilter):
    def __init__(self, user_should_have_active_game: bool = True):
        self.user_should_have_active_game = user_should_have_active_game

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user_id = event.from_user.id
        active_game = await get_user_active_game(user_id)

        return bool(active_game) is self.user_should_have_active_game
