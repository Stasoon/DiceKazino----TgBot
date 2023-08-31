import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ForceReply

from src.database import games, transactions, player_moves, Game
from src.messages.user import UserPublicGameMessages
from src.misc import GamesCallback
from src.utils.game_validations import validate_join_game_request


# region Utils

async def start_chat_game(game: Game, callback: CallbackQuery):
    """Запускает игру в чате"""
    await games.activate_game(game)
    await callback.message.delete()

    markup = ForceReply(selective=True, input_field_placeholder=f'Отправьте {game.game_type.value}')
    msg = await callback.message.bot.send_message(
        chat_id=callback.message.chat.id,
        text=await UserPublicGameMessages.get_game_in_chat_start(game),
        reply_markup=markup, parse_mode='HTML'
    )

    await games.update_message_id(game, msg.message_id)


async def join_chat_game(callback: CallbackQuery, game: Game):
    """Добавляет юзера в игру. Если все игроки собраны, запускает игру"""
    await games.add_user_to_game(telegram_id=callback.from_user.id, game_number=game.number)
    await transactions.debit_bet(game=game, user_telegram_id=callback.from_user.id, amount=game.bet)

    if len(await games.get_players_of_game(game)) >= game.max_players:
        await start_chat_game(game, callback)


async def process_player_move(game: Game, message: Message):
    """Обрабатывает ход в игре в чате"""
    game_moves = await player_moves.get_game_moves(game)
    player_telegram_id = message.from_user.id
    dice_value = message.dice.value

    # если не все игроки сделали ходы
    if len(game_moves) < game.max_players:
        await player_moves.add_player_move_if_not_moved(game, player_telegram_id=player_telegram_id, move_value=dice_value)

    # если все походили, ждём окончания анимации и заканчиваем игру
    if len(await player_moves.get_game_moves(game)) == game.max_players:
        seconds_to_wait = 3
        await asyncio.sleep(seconds_to_wait)
        await finish_game(game, message)


async def finish_game(game: Game, message: Message):
    win_coefficient = 2
    game_moves = await player_moves.get_game_moves(game)
    winner_id = None

    if all(move.value == game_moves[0].value for move in game_moves):  # Если значения одинаковы (ничья)
        # Возвращаем деньги участникам
        for move in game_moves:
            player = await move.player.get()
            await transactions.refund((player.telegram_id,), game=game, amount=game.bet)
    else:  # значения разные
        # Получаем победителя
        max_move = max(game_moves, key=lambda move: move.value)
        winner_id = (await max_move.player.get()).telegram_id
        # Начисляем выигрыш на баланс
        await transactions.accrue_winnings(game, winner_id, game.bet * win_coefficient)

    await games.finish_game(game.number, winner_id)
    await message.answer(
        text=await UserPublicGameMessages.get_game_in_chat_finish(game, winner_id, game_moves, game.bet * win_coefficient),
        parse_mode='HTML'
    )
    await player_moves.delete_game_moves(game)

# endregion Utils

# region Handlers


async def handle_game_move_message(message: Message):
    game = await games.get_user_active_game(message.from_user.id)
    dice = message.dice

    # Если игрок есть в игре и тип эмодзи соответствует
    if dice and game and message.reply_to_message \
            and message.reply_to_message.message_id == game.message_id and \
            dice.emoji == game.game_type.value:
        await process_player_move(game, message)


async def handle_join_game_in_chat_callback(callback: CallbackQuery, callback_data: GamesCallback):
    """Обработка на нажатие кнопки Присоединиться к созданной игре в чате"""
    game_number = int(callback_data.game_number)
    game = await games.get_game_obj(game_number=game_number)

    if not await validate_join_game_request(callback, game):
        return

    await join_chat_game(callback, game)


# endregion Handlers

def register_game_actions_handlers(router: Router):
    router.message.register(handle_game_move_message)
    router.callback_query.register(handle_join_game_in_chat_callback, GamesCallback.filter(F.action == 'join'))