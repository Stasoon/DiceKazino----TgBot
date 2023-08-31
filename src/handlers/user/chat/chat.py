from aiogram import Bot

from src.database import games, Game
from src.keyboards import UserPublicGameKeyboards
from src.messages import UserPublicGameMessages
from settings import Config


async def send_game_created_in_bot_notification(bot: Bot, created_game: Game):
    """Отправляет в игровой чат сообщение о том, что игра была создана в боте"""
    bot_username = (await bot.get_me()).username
    # отправляем сообщение о том, что игра создана, в игровой чат
    game_start_message = await bot.send_message(
        chat_id=Config.Games.GAME_CHAT_ID,
        text=await UserPublicGameMessages.get_game_created_in_bot_notification(created_game, bot_username),
        reply_markup=await UserPublicGameKeyboards.get_go_to_bot_and_join(created_game, bot_username),
        parse_mode='HTML'
    )
    # закрепляем сообщение за игрой
    await games.update_message_id(game=created_game, new_message_id=game_start_message.message_id)





