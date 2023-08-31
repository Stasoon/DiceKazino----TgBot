import asyncio

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from src.database import games, Game, player_moves, transactions
from src.keyboards import UserMenuKeyboards, UserPrivateGameKeyboards
from src.messages import UserPublicGameMessages


# region Utils

async def start_basic_game(callback: CallbackQuery, game: Game):
    """Начать базовую игру"""
    for player_id in await games.get_player_ids_of_game(game):
        await callback.bot.send_message(
            chat_id=player_id,
            text='Нажмите на клавиатуру, чтобы походить',
            reply_markup=UserPrivateGameKeyboards.get_dice_kb(game.game_type.value)
        )


async def process_player_move(game: Game, message: Message):
    """Обрабатывает ход в игре"""
    game_moves = await player_moves.get_game_moves(game)
    player_telegram_id = message.from_user.id
    dice_value = message.dice.value

    if len(game_moves) != game.max_players:  # если не все игроки сделали ходы
        await player_moves.add_player_move_if_not_moved(game, player_telegram_id=player_telegram_id, move_value=dice_value)
    if len(game_moves) + 1 == game.max_players:  # если все походили, ждём окончания анимации и заканчиваем игру
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
            await transactions.refund(game=game, players_telegram_ids=(player.telegram_id,), amount=game.bet)
    else:  # значения разные
        # Получаем победителя
        max_move = max(game_moves, key=lambda move: move.value)
        winner_id = (await max_move.player.get()).telegram_id
        # Начисляем выигрыш на баланс
        await transactions.accrue_winnings(game, winner_id, game.bet * win_coefficient)

    await games.finish_game(game.number, winner_id)

    text = await UserPublicGameMessages.get_game_in_chat_finish(game, winner_id, game_moves, game.bet * win_coefficient)
    markup = UserMenuKeyboards.get_main_menu()
    await send_messages_to_players(message.bot, game, text, markup)

    await player_moves.delete_game_moves(game)


async def send_messages_to_players(bot: Bot, game: Game, text: str, markup):
    for player_id in await games.get_player_ids_of_game(game):
        try:
            await bot.send_message(
                chat_id=player_id,
                text=text,
                reply_markup=markup,
                parse_mode='HTML'
            )
        except TelegramBadRequest:
            pass

# endregion Utils


async def handle_game_move_message(message: Message):
    game = await games.get_user_active_game(message.from_user.id)
    dice = message.dice

    # Если игрок есть в игре и тип эмодзи соответствует
    if game and dice.emoji == game.game_type.value:
        await process_player_move(game, message)


def register_basic_games_handlers(router: Router):
    router.message.register(handle_game_move_message, F.dice)
