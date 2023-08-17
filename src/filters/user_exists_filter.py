# from aiogram.filters import BaseFilter
# from aiogram.types import Message, CallbackQuery
#
# from src.database.users import is_user_exists
# from src.messages.user import Messages
#
#
# class UserExistsFilter(BaseFilter):
#     async def __call__(self, message_or_callback: Message | CallbackQuery) -> bool:
#         user_id = None
#         if isinstance(message_or_callback, Message):
#             user_id = message_or_callback.from_user.id
#         elif isinstance(message_or_callback, CallbackQuery):
#             user_id = message_or_callback.from_user.id
#
#         if user_id is None:
#             return False
#
#         user_exists = await is_user_exists(user_id)
#         if not user_exists:
#             if isinstance(message_or_callback, Message):
#                 await message_or_callback.answer(Messages.)
#             elif isinstance(message_or_callback, CallbackQuery):
#                 user_id = message_or_callback.from_user.id
#
#         return user_exists
