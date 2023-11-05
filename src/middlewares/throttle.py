from typing import Callable, Dict, Any, Awaitable, Union

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from cachetools import TTLCache

from src.messages import get_throttling_message


SECONDS_BETWEEN_ACTIONS = 0.8
cache = TTLCache(maxsize=20_000, ttl=SECONDS_BETWEEN_ACTIONS)


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
            await event.answer(get_throttling_message())
            return
        elif message_count > 2:
            return

        await handler(event, data)
