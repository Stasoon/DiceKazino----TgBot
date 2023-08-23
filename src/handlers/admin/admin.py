from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.filters import IsAdminFilter
from src.keyboards.admin import AdminKeyboards
from .mailing import register_mailing_handlers
from .payments_validation import register_validate_request_handlers


async def handle_admin_command(message: Message):
    await message.answer('Что вы хотите сделать?', reply_markup=AdminKeyboards.get_admin_menu())


def register_admin_handlers(router: Dispatcher | Router):
    IsAdminFilter(True)
    router.message.register(handle_admin_command, Command('admin'))
    register_mailing_handlers(router)
    register_validate_request_handlers(router)
