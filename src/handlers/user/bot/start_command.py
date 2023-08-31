from aiogram import Router
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message

from src.database import users, referrals
from src.handlers.user.bot.menu_options.play import show_game
from src.keyboards.user import UserMenuKeyboards
from src.messages.user import UserMenuMessages


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
    await create_user(start_message=message, command=command)

    try:
        if command.args and command.args.startswith('_'):
            await show_game(message, int(command.args.split('_')[2]))
            return
    except Exception as e:
        print(e)
        return

    await message.answer(text=UserMenuMessages.get_welcome(message.from_user.first_name),
                         reply_markup=UserMenuKeyboards.get_main_menu(),
                         parse_mode='HTML')

# endregion


def register_start_command_handler(router: Router):
    # Регистрация обработчика команды /start
    router.message.register(handle_start_command, Command('start'))
