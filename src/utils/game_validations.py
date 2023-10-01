from functools import wraps

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject
from aiogram.types import Message, CallbackQuery

from src.database import games, users, Game
from src.messages import InputErrors, BalanceErrors, GameErrors
from src.misc import GameStatus


def validate_create_game_start_cmd(args_count: int = 1, min_bet: int = 30):
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, command: CommandObject, *args, **kwargs):
            try:
                cmd_args = command.args.split()
                bet = float(cmd_args[0])
                user_active_game = await games.get_user_unfinished_game(message.from_user.id)
                balance = await users.get_user_balance(telegram_id=message.from_user.id)
            except AttributeError:
                await message.reply(InputErrors.get_cmd_invalid_argument_count(args_count))
            except ValueError:
                await message.reply(InputErrors.get_cmd_arguments_should_be_digit())
            else:
                if bet < min_bet:
                    await message.reply(BalanceErrors.get_bet_too_low(min_bet))
                    return
                elif balance < min_bet:
                    await message.answer(BalanceErrors.get_low_balance())
                    return
                elif user_active_game:
                    text = GameErrors.get_another_game_not_finished(user_active_game)
                    try:
                        await message.bot.send_message(
                            chat_id=message.chat.id,
                            text=text,
                            reply_to_message_id=user_active_game.message_id
                        )
                    except TelegramBadRequest:
                        await message.answer(text)
                    return
                elif len(cmd_args) != args_count:
                    await message.reply(InputErrors.get_cmd_invalid_argument_count(args_count))
                    return
                elif not all(arg.isdigit() for arg in command.args.split()[1:]):
                    await message.reply(InputErrors.get_cmd_arguments_should_be_digit())
                    return

                return await func(message, command, *args, **kwargs)

        return wrapper

    return decorator


async def validate_join_game_request(callback: CallbackQuery, game: Game) -> bool:
    """Проверяет, что игрок может присоединиться к игре. Если нет, отправляет сообщение и возвращает False \n
    Проверки: баланс для ставки, участие в этой / другой игре, есть ли места"""
    user_id = callback.from_user.id
    balance = await users.get_user_balance(user_id)
    user_active_game = await games.get_user_unfinished_game(user_id)

    # если игра уже закончена
    if game.status in (GameStatus.CANCELED, GameStatus.FINISHED):
        await callback.answer(text=GameErrors.get_game_is_full())
        return False
    # если баланс меньше ставки
    elif balance < game.bet:
        await callback.answer(text=BalanceErrors.get_low_balance(), show_alert=True)
        return False
    # если игрок уже участник
    elif user_id in await games.get_player_ids_of_game(game):
        await callback.answer(text=GameErrors.get_already_in_this_game(), show_alert=True)
        return False
    # если игрок задействован в другой игре
    elif user_active_game:
        await callback.answer(text=GameErrors.get_already_in_other_game(user_active_game), show_alert=True)
        return False
    # если игра уже заполнена
    elif await games.is_game_full(game) or game.status == GameStatus.ACTIVE:
        await callback.answer(text=GameErrors.get_game_is_full(), show_alert=True)
        return False
    return True
