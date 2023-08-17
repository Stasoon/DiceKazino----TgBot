# from datetime import datetime
# from typing import Callable, Dict, Any, Awaitable
#
# from aiogram import BaseMiddleware
# from aiogram.types import Message, CallbackQuery
#
#
# class MessageThrottlingMiddleware(BaseMiddleware):
#     async def __call__(
#         self,
#         handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
#         event: Message,
#         data: Dict[str, Any]
#     ) -> Any:
#
#
#
#
# class CallbackThrottlingMiddleware(BaseMiddleware):
#     async def __call__(
#         self,
#         handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
#         event: Message,
#         data: Dict[str, Any]
#     ) -> Any:
#
