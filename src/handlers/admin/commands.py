from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command, CommandObject

from src.database.transactions import deposit_to_user


# !!! При пересылке сообщения от игрока, показывать инфу о профиле
# + Командой с user_id показывать профиль


async def handle_give_balance_command(message: Message, command: CommandObject):
    cmd = command.command
    try:
        cmd_args = command.args.split()
        user_id = int(cmd_args[0])
        amount = float(cmd_args[1])
    except ValueError:
        await message.answer(f'Команда должна иметь формат /{cmd}'+'{id игрока} {сумма}', parse_mode='HTML')
        return

    res = await deposit_to_user(user_id=user_id, amount=amount, create_record=True if cmd == 'dep' else False)
    if res:
        await message.answer(f"Депозит начислен <a href='tg://user?id={user_id}'>игроку</a>", parse_mode='HTML')
    else:
        await message.answer('Игрок с таким user_id не найден!')


def register_commands_handlers(router: Router):
    router.message.register(handle_give_balance_command, Command('give', 'dep'))
