from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.keyboards.user import UserMenuKeyboards
from src.messages.user import UserMenuMessages
from src.misc import NavigationCallback


# region Utils

async def get_information_message_data() -> dict:
    text = await UserMenuMessages.get_information()
    reply_markup = UserMenuKeyboards.get_information()
    return {'text': text, 'reply_markup': reply_markup, 'parse_mode': 'HTML'}

# endregion


# region Handlers


async def handle_information_button(message: Message, state: FSMContext):
    await state.clear()
    msg_data = await get_information_message_data()
    await message.answer(**msg_data)


# endregion


def register_info_handlers(router: Router):
    # ветка Информация
    router.message.register(handle_information_button, F.text.contains('ℹ Информация'))
