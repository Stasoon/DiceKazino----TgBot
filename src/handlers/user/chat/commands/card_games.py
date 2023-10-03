# from aiogram import Router
# from aiogram.filters import Command, CommandObject
# from aiogram.types import Message
#
# from src.database import games, transactions
# from src.handlers.user.bot.game_strategies import BaccaratStrategy, BlackJackStrategy
# from src.keyboards import UserPublicGameKeyboards
# from src.messages import UserPublicGameMessages
# from src.misc import GameType, GameCategory
# from src.utils.game_validations import validate_create_game_start_cmd
#
#
# # !!! Та же самая функция есть в src/handlers/user/chat/commands/base_games
# async def create_game_and_send(message: Message, command: CommandObject, category: GameCategory,
#                                game_type: GameType, users_count: int):
#     bet = float(command.args.split()[0])
#
#     game = await games.create_game(
#         creator_telegram_id=message.from_user.id,
#         max_players=users_count,
#         game_category=category,
#         game_type=game_type,
#         chat_id=message.chat.id,
#         bet=bet)
#
#     await transactions.debit_bet(game=game, user_telegram_id=message.from_user.id, amount=bet)
#
#     game_start_message = await message.answer(
#         text=await UserPublicGameMessages.get_game_in_chat_created(game, message.chat.username),
#         reply_markup=await UserPublicGameKeyboards.get_join_game_in_chat(game),
#         parse_mode='HTML'
#     )
#
#     await games.update_message_id(game, game_start_message.message_id)
#
#
# # region Handlers
#
# @validate_create_game_start_cmd(args_count=1)
# async def handle_black_jack_cmd(message: Message, command: CommandObject):
#     await create_game_and_send(message=message, command=command,
#                                category=GameCategory.BLACKJACK, game_type=GameType.BJ,
#                                users_count=2)
#
#
# @validate_create_game_start_cmd(args_count=2)
# async def handle_baccarat_cmd(message: Message, command: CommandObject):
#     pass
#
# # endregion
#
#
# def register_card_games_handlers(router: Router):
#     router.message.register(handle_black_jack_cmd, Command('bj'))
#     router.message.register(handle_baccarat_cmd, Command('baccara'))
#
#     BaccaratStrategy.register_moves_handlers(router)
#     BlackJackStrategy.register_moves_handlers(router)
