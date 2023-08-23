import asyncio
from functools import wraps

from aiogram.types import Message, CallbackQuery, ForceReply
from aiogram.filters.command import Command, CommandObject
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram import Router, Dispatcher, F

from src.filters import ChatTypeFilter, UserExistFilter, MessageIsForward
from src.database import users, games, transactions, moves, Game
from src.messages.user import UserMessages, ExceptionMessages
from src.misc import GameCommands, GameType, GamesCallback
from src.middlewares.throttle import ThrottlingMiddleware
from src.keyboards import PublicKeyboards
from settings import Config


# region Utils

### СДЕЛАТЬ РЕФАКТОР ФИЛЬТРА + ПЕРЕИМЕНОВАТЬ
def validate_game_start(args_count: int = 1, min_bet: int = 30):
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, command: CommandObject, *args, **kwargs):
            try:
                cmd_args = command.args.split()
                bet = float(cmd_args[0])
                user_active_game = await games.get_user_active_game(message.from_user.id)
                balance = await users.get_user_balance(telegram_id=message.from_user.id)
            except AttributeError:
                await message.reply(ExceptionMessages.get_invalid_argument_count(args_count))
            except ValueError:
                await message.reply(ExceptionMessages.get_arguments_have_invalid_types())
            else:
                if bet < min_bet:
                    await message.reply(ExceptionMessages.get_bet_too_low(min_bet))
                    return
                elif balance < min_bet:
                    await message.answer(ExceptionMessages.get_low_balance())
                    return
                elif user_active_game:
                    await message.answer(ExceptionMessages.get_another_game_not_finished(user_active_game))
                    return
                elif len(cmd_args) != args_count:
                    await message.reply(ExceptionMessages.get_invalid_argument_count(args_count))
                    return
                elif not all(arg.isdigit() for arg in command.args.split()[1:]):
                    await message.reply(ExceptionMessages.get_arguments_have_invalid_types())
                    return

                return await func(message, command, *args, **kwargs)

        return wrapper

    return decorator


async def start_mini_game(game_start_msg: Message, game_start_cmd: CommandObject, game_type: GameType) -> Game:
    bet = float(game_start_cmd.args.split()[0])
    user_id = game_start_msg.from_user.id
    await transactions.debit_bet(user_telegram_id=user_id, amount=bet)

    game = await games.create_game(creator_telegram_id=user_id, max_players=1, game_type=game_type, bet=bet)
    return game


async def process_mini_game_result(user_message: Message, game: Game, win_coefficient: int = 0):
    """В win_coefficient передать коэффициент выигрыша, или 0 при проигрыше"""
    if win_coefficient:
        winning_amount = game.bet * win_coefficient
        await user_message.answer(text=await UserMessages.get_mini_game_victory(game, winning_amount),
                                  parse_mode='HTML')
        await games.finish_game(game.number, winner_telegram_id=user_message.from_user.id)
        await transactions.accrue_winnings(user_message.from_user.id, amount=winning_amount)
    else:
        await user_message.answer(await UserMessages.get_mini_game_loose(game=game), parse_mode='HTML')
        await games.finish_game(game.number)


# endregion


# region MiniGames

@validate_game_start(args_count=2)
async def handle_cube_command(message: Message, command: CommandObject):
    game = await start_mini_game(message, command, GameType.DICE)

    user_choice = command.args.split()[1]
    dice_message = await message.reply_dice(DiceEmoji.DICE)
    await asyncio.sleep(4)

    win_coefficient = 2.5 if user_choice == str(dice_message.dice.value) else 0
    await process_mini_game_result(message, game, win_coefficient)


@validate_game_start(args_count=1, min_bet=10)
async def handle_casino_command(message: Message, command: CommandObject):
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

async def create_game_and_send(message: Message, command: CommandObject, game_type: GameType, users_count: int):
    bet = float(command.args.split()[0])

    game = await games.create_game(message.from_user.id, users_count, game_type=game_type, bet=bet)
    await message.answer(text=await UserMessages.get_game_in_chat(game),
                         reply_markup=await PublicKeyboards.get_join_game(game),
                         parse_mode='HTML')


@validate_game_start(args_count=1)
async def handle_dice_command(message: Message, command: CommandObject):
    await create_game_and_send(message, command, game_type=GameType.DICE, users_count=2)


@validate_game_start(args_count=1)
async def handle_darts_command(message: Message, command: CommandObject):
    await create_game_and_send(message, command, game_type=GameType.DARTS, users_count=2)


@validate_game_start(args_count=1)
async def handle_basketball_commands(message: Message, command: CommandObject):
    await create_game_and_send(message, command, game_type=GameType.BASKETBALL, users_count=2)


@validate_game_start(args_count=1)
async def handle_football_command(message: Message, command: CommandObject):
    await create_game_and_send(message, command, game_type=GameType.FOOTBALL, users_count=2)


# endregion

# region Other


async def handle_profile_command(message: Message):
    user = await users.get_user_or_none(message.from_user.id)
    await message.answer(text=await UserMessages.get_profile(user), parse_mode='HTML')


# endregion


# region Utils

async def show_alert(to_callback: CallbackQuery, text: str):
    await to_callback.answer(text=text, show_alert=True)


async def process_player_move(game: Game, message: Message):
    game_moves = await moves.get_game_moves(game)
    player_telegram_id = message.from_user.id
    dice_value = message.dice.value

    if len(game_moves) != game.max_players:  # если не все игроки сделали ходы
        await moves.add_player_move(game, player_telegram_id=player_telegram_id, move=dice_value)
    if len(game_moves) + 1 == game.max_players:  # если все походили, заканчиваем игру
        await finish_game(game, message)


# ЕСЛИ ПОНАДОБИТСЯ, СДЕЛАТЬ ВЫБОР УСЛОВИЯ ПОБЕДЫ  +  РЕФАКТОР
async def finish_game(game: Game, message: Message):
    win_coefficient = 2
    game_moves = await moves.get_game_moves(game)
    winner_id = None

    if all(move.value == game_moves[0].value for move in game_moves):  # Если значения одинаковы (ничья)
        # Возвращаем деньги участникам
        for move in game_moves:
            player = await move.player.get()
            await transactions.accrue_winnings(player.telegram_id, game.bet)
    else:  # значения разные
        # Получаем победителя
        max_move = max(game_moves, key=lambda move: move.value)
        winner_id = (await max_move.player.get()).telegram_id
        # Начисляем выигрыш на баланс
        await transactions.accrue_winnings(winner_id, game.bet * win_coefficient)

    await games.finish_game(game.number, winner_id)
    await message.answer(
        text=await UserMessages.get_game_in_chat_finish(game, winner_id, game_moves, game.bet * win_coefficient),
        parse_mode='HTML'
    )
    await moves.delete_game_moves(game)


async def is_user_have_right_to_join_game(callback: CallbackQuery, game: Game):
    user_id = callback.from_user.id
    balance = await users.get_user_balance(user_id)
    user_active_game = await games.get_user_active_game(user_id)

    if balance < game.bet:
        await show_alert(to_callback=callback, text=ExceptionMessages.get_low_balance())
        await callback.answer(text=ExceptionMessages.get_low_balance(), show_alert=True)
        return False
    elif user_id in await games.get_player_ids_of_game(game):
        await show_alert(to_callback=callback, text=ExceptionMessages.get_already_in_game())
        return False
    elif user_active_game:
        await show_alert(to_callback=callback, text=ExceptionMessages.get_already_in_other_game(user_active_game))
        return False
    elif await games.is_game_full(game):
        return False
    return True


async def join_game(callback, game):
    await games.add_user_to_game(telegram_id=callback.from_user.id, game_number=game.number)
    await transactions.debit_bet(user_telegram_id=callback.from_user.id, amount=game.bet)
    await callback.message.delete()

    kb = ForceReply(selective=True, input_field_placeholder=f'Отправьте {game.type.value}')
    await callback.message.bot.send_message(
        chat_id=callback.message.chat.id,
        text=await UserMessages.get_game_in_chat(game),
        reply_markup=kb, parse_mode='HTML'
    )

# endregion


# region Handlers


async def handle_game_move_message(message: Message):
    game = await games.get_user_active_game(message.from_user.id)
    dice = message.dice

    # Если игрок есть в игре и тип эмодзи соответствует
    if game and dice and dice.emoji == game.type.value:
        await process_player_move(game, message)


async def handle_join_game_callback(callback: CallbackQuery, callback_data: GamesCallback):
    game_number = int(callback_data.game_number)
    game = await games.get_game_obj(game_number=game_number)

    if not await is_user_have_right_to_join_game(callback, game):
        return

    await join_game(callback, game)

# endregion


def register_public_handlers(router: Dispatcher | Router):
    router.message.filter(ChatTypeFilter(chat_type=['group', 'supergroup']), UserExistFilter(True))
    router.message.middleware(ThrottlingMiddleware())

    # MiniGames
    router.message.register(handle_cube_command, GameCommands.cube)
    router.message.register(handle_casino_command, GameCommands.casino)

    # Games for 2 players
    router.message.register(handle_dice_command, GameCommands.dice)
    router.message.register(handle_darts_command, GameCommands.darts)
    router.message.register(handle_basketball_commands, GameCommands.basketball)
    router.message.register(handle_football_command, GameCommands.football)
    # router.message.register(handle_bowling_command, GameCommands.bowling)

    # Other
    router.message.register(handle_profile_command, Command('profile'))

    router.message.register(handle_game_move_message, MessageIsForward(True))
    router.callback_query.register(handle_join_game_callback, GamesCallback.filter(F.action == 'join'))
