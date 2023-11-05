from aiogram import Router
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message

from src.handlers.user.bot import even_uneven
from src.filters.cmd_args_starts_with_filter import CmdArgsStartsWithFilter
from src.messages import get_full_game_info_text, GameErrors
from src.keyboards import UserPrivateGameKeyboards
from src.keyboards.user import UserMenuKeyboards
from src.messages.user import UserMenuMessages
from src.database import users, games, Game
from src.misc import GameStatus


# region Utils


async def send_welcome(start_message: Message):
    await start_message.answer(
        text=UserMenuMessages.get_welcome(start_message.from_user.first_name),
        reply_markup=UserMenuKeyboards.get_main_menu(),
        parse_mode='HTML'
    )


async def process_referral_code_arg(command: CommandObject, new_user_id: int) -> bool:
    """Обрабатывает реферальный код. Если код невалидный, возвращает False."""
    args = command.args.split()
    if not args[0].isdigit():
        return False

    referral_code = int(args[0])
    return await users.add_referral(referrer_id=referral_code, user_telegram_id=new_user_id)


async def get_game_by_args(command_args: str) -> Game | None:
    """Получает игру по аргументам команды /start"""
    try:
        game_number = int(command_args.split('_')[2])
        return await games.get_game_obj(game_number)
    except Exception as e:
        return


# endregion


async def handle_empty_start_cmd(message: Message, command: CommandObject):
    user = message.from_user

    # отправляем приветствие
    await send_welcome(message)

    # создаём пользователя, если не существует
    is_user_created = await users.create_user_if_not_exists(
        first_name=user.first_name, username=user.username, telegram_id=user.id
    )

    # если создан новый юзер и команда содержит аргументы, обрабатываем реферальный код
    if is_user_created and command.args:
        await process_referral_code_arg(command, message.from_user.id)


async def handle_start_to_show_game_cmd(message: Message, command: CommandObject):
    game = await get_game_by_args(command.args)

    if not game or game.status != GameStatus.WAIT_FOR_PLAYERS:
        await message.answer(GameErrors.get_game_is_finished(), parse_mode='HTML')
        return

    await message.answer(
        text=await get_full_game_info_text(game),
        reply_markup=await UserPrivateGameKeyboards.show_game(game),
        parse_mode='HTML'
    )


async def handle_even_u_neven_cmd(message: Message, args: str, state):
    # такой формат аргументов задаётся в коде игры
    round_num, bet_option = args.split('_')
    await even_uneven.show_bet_entering(message=message, state=state, round_number=round_num, bet_option=bet_option)


# endregion


def register_start_command_handler(router: Router):
    # Регистрация обработчика команды /start
    router.message.register(handle_start_to_show_game_cmd, Command('start'), CmdArgsStartsWithFilter('_'))
    router.message.register(handle_even_u_neven_cmd, Command('start'), CmdArgsStartsWithFilter('EuN_'))
    router.message.register(handle_empty_start_cmd, Command('start'))
