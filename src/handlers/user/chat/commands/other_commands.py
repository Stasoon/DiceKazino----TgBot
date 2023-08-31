from datetime import timedelta, datetime, timezone

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.command import Command
from aiogram.types import Message

from src.database import users, games, transactions
from src.messages import GameErrors
from src.messages.user import UserMenuMessages, get_short_game_info_text
from src.misc import GameStatus


async def handle_profile_command(message: Message):
    user = await users.get_user_or_none(message.from_user.id)
    await message.answer(text=await UserMenuMessages.get_profile(user), parse_mode='HTML')


async def handle_my_games_command(message: Message):
    game = await games.get_user_active_game(message.from_user.id)
    if not game:
        await message.answer(GameErrors.get_no_active_games(), parse_mode='HTML')
        return

    text = await get_short_game_info_text(game)

    try:
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_to_message_id=game.message_id,
            parse_mode='HTML'
        )
    except TelegramBadRequest:
        await message.answer(text, parse_mode='HTML')


async def handle_all_games_command(message: Message):
    chat_id = message.chat.id
    chat_available_games = await games.get_chat_available_games(chat_id)

    if not chat_available_games:
        await message.answer(GameErrors.get_no_active_games(), parse_mode='HTML')
        return

    for game in chat_available_games:
        text = await get_short_game_info_text(game)
        try:
            await message.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=game.message_id,
                parse_mode='HTML'
            )
        except TelegramBadRequest:
            await message.answer(text, parse_mode='HTML')


async def handle_delete_game_command(message: Message):
    # если не ответ на игру
    if not message.reply_to_message:
        return

    game = await games.get_game_by_message_id(message.reply_to_message.message_id)

    # игра не найдена
    if not game:
        await message.answer(text=GameErrors.get_game_is_finished(), parse_mode='HTML')
        return

    # minutes_while_cant_delete_game = 30
    # time_difference = datetime.now().astimezone(game.start_time.tzinfo) - game.start_time
    # # не прошло N минут
    # if time_difference < timedelta(minutes=minutes_while_cant_delete_game):
    #     await message.answer(text=GameErrors.get_delete_game_time_limit(), parse_mode='HTML')
    # игра начата
    # elif game.status != GameStatus.WAIT_FOR_PLAYERS:
    #     await message.answer(text=GameErrors.get_cannot_delete_game_message_after_start(), parse_mode='HTML')
    # не является создателем
    elif message.from_user.id != (await games.get_creator_of_game(game)).telegram_id:
        await message.answer(text=GameErrors.get_not_creator_of_game(), parse_mode='HTML')
    # если всё хорошо, удаляем игру
    else:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=game.message_id)
        except TelegramBadRequest:
            pass
        await games.cancel_game(game)
        await transactions.refund((message.from_user.id,), amount=game.bet, game=game)


def register_other_commands_handlers(router: Router):
    router.message.register(handle_delete_game_command, Command('del'))
    router.message.register(handle_profile_command, Command('profile'))
    router.message.register(handle_all_games_command, Command('allgames'))
    router.message.register(handle_my_games_command, Command('mygames'))
