# РЕГИСТРИРОВАТЬ БЛОКИРОВКУ БОТА
from aiogram import Router
from aiogram.types import Message, CallbackQuery

from src.filters import UserExistFilter, MessageIsCommand
from src.messages import ExceptionMessages


# Срабатывает, если юзер не зарегистрирован в боте и присылает команду
async def handle_not_registered_in_bot_messages(message: Message):
    await message.reply(text=ExceptionMessages.get_not_registered_in_bot())


# Срабатывает, если юзер не зарегистрирован в боте и нажимает кнопку
async def handle_not_registered_in_bot_callbacks(callback: CallbackQuery):
    await callback.answer(text=ExceptionMessages.get_not_registered_in_bot(), show_alert=True)


def register_other_handlers(router: Router):
    router.message.register(handle_not_registered_in_bot_messages, MessageIsCommand(), UserExistFilter(False))
    router.callback_query.register(handle_not_registered_in_bot_callbacks, UserExistFilter(False))

