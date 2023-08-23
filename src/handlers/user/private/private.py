from src.filters import ChatTypeFilter
from src.middlewares.throttle import ThrottlingMiddleware

from .play import register_play_handlers
from .profile import register_profile_handlers
from .info import register_info_handlers


from aiogram import Router, Dispatcher
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message

from src.database import users, referrals
from src.filters import ChatTypeFilter
from src.keyboards.user import PrivateKeyboards
from src.messages.user import UserMessages
from src.middlewares.throttle import ThrottlingMiddleware


# region Utils

async def process_referral_code(command: CommandObject, new_user_id: int) -> None:
    if not command.args:
        return

    args = command.args.split()
    if len(args) == 1 and args[0].isdigit():
        referral_code = int(args[0])
        await referrals.add_referral(referrer_telegram_id=referral_code, referral_telegram_id=new_user_id)


async def create_user(start_message: Message, command: CommandObject):
    name = start_message.from_user.first_name
    username = start_message.from_user.username

    is_user_created = await users.create_user_if_not_exists(
        first_name=name, username=username, telegram_id=start_message.from_user.id
    )

    if is_user_created:
        await process_referral_code(command, start_message.from_user.id)


# endregion

async def handle_start_command(message: Message, command: CommandObject):
    await message.answer(text=UserMessages.get_welcome(message.from_user.first_name),
                         reply_markup=PrivateKeyboards.get_main_menu(),
                         parse_mode='HTML')
    await create_user(start_message=message, command=command)

# endregion


def register_private_handlers(router):
    router.message.filter(ChatTypeFilter('private'))
    router.message.middleware(ThrottlingMiddleware())
    router.callback_query.middleware(ThrottlingMiddleware())

    router.message.register(handle_start_command, Command('start'))
    register_play_handlers(router)
    register_profile_handlers(router)
    register_info_handlers(router)
