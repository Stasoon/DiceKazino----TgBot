from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.database import games, Game, transactions
from src.misc import GamesCallback, GameCategory
from src.utils.game_validations import validate_join_game_request

from .baccarat import start_baccarat_game
from .basic_games import start_basic_game


async def add_user_to_bot_game(callback: CallbackQuery, game: Game):
    await callback.message.delete()
    await games.add_user_to_game(callback.from_user.id, game.number)

    # если игра заполнена
    if await games.is_game_full(game):
        # перенаправляем на начало нужной игры
        if game.category == GameCategory.BASIC:
            await start_basic_game(callback, game)
        elif game.category == GameCategory.BACCARAT:
            await start_baccarat_game(callback, game)


async def handle_join_game_callback(callback: CallbackQuery, callback_data: GamesCallback, state: FSMContext):
    # отменяем состояние игрока
    await state.clear()

    game = await games.get_game_obj(callback_data.game_number)
    if await validate_join_game_request(callback, game):
        await add_user_to_bot_game(callback, game)
        await transactions.debit_bet(game, callback.from_user.id, game.bet)


def register_join_game_handlers(router: Router):
    router.callback_query.register(handle_join_game_callback, GamesCallback.filter(
        (F.action == 'join') & F.game_number
    ))
