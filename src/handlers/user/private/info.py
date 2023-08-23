from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from src.keyboards.user import PrivateKeyboards
from src.messages.user import UserMessages
from src.misc import NavigationCallback


# region Utils

async def get_information_message_data() -> dict:
    text = await UserMessages.get_information()
    reply_markup = PrivateKeyboards.get_information()
    return {'text': text, 'reply_markup': reply_markup, 'parse_mode': 'HTML'}

# endregion


# region Handlers


async def handle_information_button(message: Message):
    msg_data = await get_information_message_data()
    await message.answer(**msg_data)


async def handle_top_players_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        text=UserMessages.get_top_players(),
        reply_markup=await PrivateKeyboards.get_top_players()
    )


async def handle_back_in_info_callback(callback: CallbackQuery):
    await callback.message.edit_text(**(await get_information_message_data()))

# endregion


def register_info_handlers(router: Router):
    # ветка Информация
    router.message.register(handle_information_button, F.text.contains('ℹ Информация'))

    router.callback_query.register(handle_top_players_callback, NavigationCallback.filter(
        (F.branch == 'info') & (F.option == 'top_players')))

    router.callback_query.register(handle_back_in_info_callback, NavigationCallback.filter(
        (F.branch == 'info') & ~F.option))
