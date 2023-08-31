from aiogram import Router
from aiogram.filters.command import CommandObject, Command
from aiogram.types import Message

from src.database import games, transactions
from src.keyboards import UserPublicGameKeyboards
from src.messages import UserPublicGameMessages
from src.misc import GameType, GameCategory
from src.utils.game_validations import validate_game_start


async def create_game_and_send(message: Message, command: CommandObject, game_type: GameType, users_count: int):
    bet = float(command.args.split()[0])

    game = await games.create_game(
        creator_telegram_id=message.from_user.id,
        max_players=users_count,
        game_type=game_type,
        chat_id=message.chat.id,
        game_category=GameCategory.BASIC,
        bet=bet)

    await transactions.debit_bet(game=game, user_telegram_id=message.from_user.id, amount=bet)

    game_start_message = await message.answer(
        text=await UserPublicGameMessages.get_game_in_chat_created(game, message.chat.username),
        reply_markup=await UserPublicGameKeyboards.get_join_game_in_chat(game),
        parse_mode='HTML'
    )

    await games.update_message_id(game, game_start_message.message_id)


# region For two players

# в словарь добавлять 'команда': GameType
game_type_map = {
    'dice': GameType.DICE,
    'darts': GameType.DARTS,
    'basket': GameType.BASKETBALL,
    'foot': GameType.FOOTBALL,
    'bowl': GameType.BOWLING
}


@validate_game_start(args_count=1)
async def handle_games_for_two_players_commands(message: Message, command: CommandObject):
    await create_game_and_send(message, command, game_type=game_type_map.get(command.command), users_count=2)


def register_games_for_two_commands_handlers(router: Router):
    # Games for 2 players
    router.message.register(
        handle_games_for_two_players_commands,
        # распаковываем ключи команд для создания игр для двоих
        Command(*game_type_map.keys())
    )
