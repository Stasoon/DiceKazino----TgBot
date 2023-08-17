import asyncio
from functools import wraps

from aiogram import Router, Dispatcher, types, F
from aiogram.filters.command import Command, CommandObject
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.fsm.context import FSMContext

from src.database import users, games, moves, Game
from settings import Config
from src.misc import GameCommands, GameType, GamesCallbackFactory, PlayingStates
from src.filters import GameChatFilter
from src.messages.user import Messages
from src.keyboards import InlineKeyboards


# region Utils

### СДЕЛАТЬ РЕФАКТОР ФИЛЬТРА
def check_arguments(args_count: int = 1, min_bet: int = 30):
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, command: CommandObject, *args, **kwargs):
            try:
                cmd_args = command.args.split()
                bet = float(cmd_args[0])
            except AttributeError:
                await message.reply(await Messages.Exceptions.get_invalid_argument_count(args_count))
            except ValueError:
                await message.reply(await Messages.Exceptions.get_arguments_have_invalid_types())
            else:
                if bet < min_bet:
                    await message.reply(await Messages.Exceptions.get_arguments_have_invalid_types())
                    return
                if len(cmd_args) != args_count:
                    await message.reply(await Messages.Exceptions.get_invalid_argument_count(args_count))
                    return
                if not all(arg.isdigit() for arg in command.args.split()[1:]):
                    await message.reply(await Messages.Exceptions.get_arguments_have_invalid_types())
                    return

                user_active_game = await games.get_user_active_game(message.from_user.id)
                if user_active_game:
                    await message.answer(await Messages.Exceptions.get_another_game_not_finished(user_active_game))
                    return

                return await func(message, command, *args, **kwargs)
        return wrapper
    return decorator


def check_balance(min_bet: float = 30):
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, command: CommandObject, *args, **kwargs):
            balance = await users.get_user_balance(telegram_id=message.from_user.id)
            if balance > min_bet:
                return await func(message, command, *args, **kwargs)
            else:
                await message.answer(await Messages.Exceptions.get_low_balance())
        return wrapper
    return decorator


async def start_mini_game(game_start_msg: types.Message, game_start_cmd: CommandObject, game_type: GameType) -> Game:
    bet = float(game_start_cmd.args.split()[0])
    await users.reduce_user_balance(telegram_id=game_start_msg.from_user.id, value=bet)

    game = await games.create_game(creator_telegram_id=game_start_msg.from_user.id,
                                   max_players=1,
                                   game_type=game_type,
                                   bet=bet)
    return game


async def process_mini_game_result(user_message: types.Message, game: Game, win_coefficient: int = 0):
    """В win_coefficient передать коэффициент выигрыша, или 0 при проигрыше"""
    if win_coefficient:
        winning_amount = game.bet * win_coefficient
        await user_message.answer(text=await Messages.get_mini_game_victory(game, winning_amount), parse_mode='HTML')
        await games.finish_game(game.number, winner_telegram_id=user_message.from_user.id)
        await users.increase_user_balance(user_message.from_user.id, value=winning_amount)
    else:
        await user_message.answer(await Messages.get_mini_game_loose(game=game), parse_mode='HTML')
        await games.finish_game(game.number)


# endregion


# region MiniGames

@check_arguments(args_count=2)
@check_balance()
async def handle_cube_command(message: types, command: CommandObject):
    game = await start_mini_game(message, command, GameType.DICE)

    user_choice = command.args.split()[1]
    dice_message = await message.reply_dice(DiceEmoji.DICE)
    await asyncio.sleep(4)

    win_coefficient = 2.5 if user_choice == str(dice_message.dice.value) else 0
    await process_mini_game_result(message, game, win_coefficient)


@check_arguments(args_count=1)
@check_balance()
async def handle_casino_command(message: types.Message, command: CommandObject):
    game = await start_mini_game(message, command, GameType.CASINO)

    dice_message = await message.reply_dice(DiceEmoji.SLOT_MACHINE)
    await asyncio.sleep(2)

    dice_value = dice_message.dice.value
    win_coefficient = 0
    if dice_value in (6, 11, 16, 17, 27, 32, 33, 38, 48, 49, 54, 59):  # Первые 2
        win_coefficient = 1.5
    if dice_value in (1, 22, 43):  # Первые 3
        win_coefficient = 2.25
    elif dice_value == 64:  # Три семёрки (джек-пот)
        win_coefficient = 5

    await process_mini_game_result(message, game, win_coefficient)


# endregion

# region For two players


@check_arguments(1)
@check_balance()
async def handle_dice_command(message: types.Message, command: CommandObject, state: FSMContext):
    bet = float(command.args.split()[0])

    game = await games.create_game(message.from_user.id, 2, game_type=GameType.DICE, bet=bet)
    await message.answer(text=await Messages.get_game_in_chat(game, 'Кости'),
                         reply_markup=await InlineKeyboards.get_join_markup(game),
                         parse_mode='HTML')
    await state.set_state(PlayingStates.wait_for_move)


# endregion

# region Other


# РЕФАКТОР!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
async def handle_game_move_message(message: types.Message):
    game = await games.get_user_active_game(message.from_user.id)

    # Если игрок есть в игре и тип соответствует
    if game and message.dice and message.dice.emoji == game.type.value: ## !!!! ЕЩЁ ПРОВЕРКИ +что это пересыл
        game_moves = await moves.get_game_moves(game)

        if len(game_moves) != game.max_players:
            await moves.add_player_move(game, player_telegram_id=message.from_user.id, move=message.dice.value)

        # Если все игроки сделали ходы
        if len(game_moves) + 1 == game.max_players:
            game_moves = await moves.get_game_moves(game)
            winner_id = None

            if game_moves[0].value == game_moves[1].value:  # Если значения одинаковы (ничья)
                # Возвращаем деньги участникам
                for move in game_moves:
                    player = await move.player.get()
                    await users.increase_user_balance(player.telegram_id, game.bet)
            else:  # значения разные
                # Получаем победителя
                winner_id = game_moves[0].player \
                    if game_moves[0].value > game_moves[1].value else game_moves[1].player
                winner_id = (await winner_id.get()).telegram_id
                # Начисляем выигрыш на баланс
                await users.increase_user_balance(winner_id, game.bet * 2)

            await games.finish_game(game.number, winner_id)
            await message.answer(text=await Messages.get_game_in_chat_finish(game, winner_id, game_moves, game.bet*2),
                                 parse_mode='HTML')
            await moves.delete_game_moves(game)


# РЕФАКТОР!!!!!!!!!!!
async def handle_join_game_callback(callback: types.CallbackQuery, callback_data: GamesCallbackFactory):
    game_number = int(callback_data.number)
    game = await games.get_game_obj(game_number=game_number)

    # проверка баланса
    if await users.get_user_balance(callback.from_user.id) < game.bet:
        await callback.answer(text=await Messages.Exceptions.get_low_balance(), show_alert=True)
        return

    #  проверка, что есть места и юзер ещё не является участником
    if not await games.is_game_full(game) \
            and callback.from_user.id not in await games.get_player_ids(game) \
            and not await games.get_user_active_game(callback.from_user.id):
        await games.add_user_to_game(telegram_id=callback.from_user.id, game_number=game_number)
        await users.reduce_user_balance(telegram_id=callback.from_user.id, value=game.bet)
        kb = types.ForceReply(selective=True, input_field_placeholder=f'Отправьте эмодзи {game.type.value}')

        await callback.message.delete()
        await callback.message.bot.send_message(callback.message.chat.id,
                                                text=await Messages.get_game_in_chat(game),
                                                reply_markup=kb, parse_mode='HTML')
    else:
        await callback.answer(text=await Messages.Exceptions.get_already_in_game(), show_alert=True)


async def handle_profile_command(message: types.Message):
    user = await users.get_user_obj(message.from_user.id)
    await message.answer(text=await Messages.get_user_profile(user), parse_mode='HTML')


# endregion


def register_public_handlers(router: Dispatcher | Router):
    router.message.filter(GameChatFilter(Config.CHAT_USERNAME))

    # MiniGames
    router.message.register(handle_cube_command, GameCommands.cube)
    router.message.register(handle_casino_command, GameCommands.casino)
    # Games for 2 players
    router.message.register(handle_dice_command, GameCommands.dice)

    # Other
    router.message.register(handle_profile_command, Command('profile'))
    router.callback_query.register(handle_join_game_callback, GamesCallbackFactory.filter(F.action == 'join'))
    router.message.register(handle_game_move_message)
