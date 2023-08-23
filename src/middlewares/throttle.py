from typing import Callable, Dict, Any, Awaitable, Union

from random import randint

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from cachetools import TTLCache

from src.messages import ExceptionMessages


SECONDS_BETWEEN_ACTIONS = 1
cache = TTLCache(maxsize=15_000, ttl=SECONDS_BETWEEN_ACTIONS)


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
            event: Union[Message, CallbackQuery],
            data: Dict[str, Any],
    ) -> Any:

        user_id = event.from_user.id
        message_count = cache.get(user_id, 0) + 1
        cache[user_id] = message_count

        if message_count == 2:
            await event.answer(ExceptionMessages.get_too_many_requests())
            return
        elif message_count > 2:
            return

        await handler(event, data)
