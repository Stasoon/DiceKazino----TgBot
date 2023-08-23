from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from src.database import users, games
from src.keyboards.user import PrivateKeyboards
from src.messages.user import UserMessages
from src.misc import NavigationCallback


# region Utils

async def get_play_message_data(user_id: int) -> dict:
    text = UserMessages.get_play_menu(await users.get_user_or_none(user_id))
    reply_markup = PrivateKeyboards.get_play_menu()
    return {'text': text, 'reply_markup': reply_markup, 'parse_mode': 'HTML'}

# endregion


# region Handlers

async def handle_play_button(message: Message):
    await message.answer(**(await get_play_message_data(message.from_user.id)))


async def handle_game_category_callback(callback: CallbackQuery):
    """Обработка нажатия на одну из категорий игр"""
    available_games = await games.get_available_games(callback.from_user.id)
    await callback.message.edit_text(text='asdfhgddsfas', reply_markup=await PrivateKeyboards.get_game_category(available_games))


async def handle_back_in_play_callback(callback: CallbackQuery, callback_data: NavigationCallback):
    await callback.message.edit_text(**(await get_play_message_data(callback.from_user.id)))


# async def handle_refresh_games_callback(callback: CallbackQuery):
#     """Обновление списка доступных игр"""
#     try:
#         available_games = await games.get_available_games(callback.from_user.id)
#         reply_markup = await PrivateKeyboards.get_games(available_games)
#         await callback.message.edit_reply_markup(reply_markup=reply_markup)
#     except TelegramBadRequest:
#         await callback.answer()


def register_play_handlers(router: Router):
    router.message.register(handle_play_button, F.text.contains('🎰  Играть  🎰'))

    router.callback_query.register(handle_back_in_play_callback, NavigationCallback.filter(
        (F.branch == 'play') & F.option))
    router.callback_query.register(handle_game_category_callback, NavigationCallback.filter(F.branch == 'play'))
