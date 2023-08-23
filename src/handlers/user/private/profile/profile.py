from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.database import users
from src.keyboards.user import PrivateKeyboards
from src.messages import UserMessages
from src.misc import (NavigationCallback)
from .deposit import register_deposit_handlers
from .withdraw import register_withdraw_handlers


# region Utils

async def get_profile_message_data(user_id: int) -> dict:
    user = await users.get_user_or_none(user_id)
    text = await UserMessages.get_profile(user)
    reply_markup = PrivateKeyboards.get_profile()
    return {'text': text, 'reply_markup': reply_markup, 'parse_mode': 'HTML'}


# endregion


# region Handlers

async def handle_cancel_transaction_button_message(message: Message, state: FSMContext):
    """Обработка нажатия на кнопку отмены пополнения"""
    await state.clear()
    await message.answer('Отменено', reply_markup=PrivateKeyboards.get_main_menu())


async def handle_profile_button(message: Message):
    """Показывает сообщение по нажатию на кнопку Профиль"""
    msg_data = await get_profile_message_data(message.from_user.id)
    await message.answer(**msg_data)


# Реферальная система
async def handle_referral_system_callback(callback: CallbackQuery):
    """Показывает сообщение по нажатию на кнопку Реферальная система"""
    bot_username = (await callback.bot.get_me()).username
    user_id = callback.from_user.id
    await callback.message.edit_text(
        text=await UserMessages.get_referral_system(bot_username, user_id),
        reply_markup=PrivateKeyboards.get_referral_system(bot_username, user_id),
        parse_mode='HTML'
    )


# обработка кнопок Назад
async def handle_back_in_profile_callbacks(callback: CallbackQuery):
    """Обработка нажатия на кнопку назад в Профиль"""
    await callback.message.edit_text(**(await get_profile_message_data(callback.from_user.id)))


# endregion


def register_profile_handlers(router: Router):
    # обработка кнопки отмены транзакции
    router.message.register(handle_cancel_transaction_button_message, F.text == '❌ Отмена')
    # обработка кнопки Профиль
    router.message.register(handle_profile_button, F.text.contains('👤 Профиль'))

    # опция Реферальная система
    router.callback_query.register(handle_referral_system_callback, NavigationCallback.filter(
        (F.branch == 'profile') & (F.option == 'referral_system')))

    # кнопка назад в Профиль
    router.callback_query.register(handle_back_in_profile_callbacks, NavigationCallback.filter(
        (F.branch == 'profile') & ~F.option))

    register_deposit_handlers(router)
    register_withdraw_handlers(router)
