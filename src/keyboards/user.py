from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, \
    ReplyKeyboardMarkup, InlineKeyboardBuilder
from src.database.models import Game
from src.database import games
from src.misc import GamesCallbackFactory


invite_link = 'tg://msg_url?url=https://t.me/{bot_username}?start={user_tg_id}&text=Присоединяйся%20по%20моей%20ссылке'


class ReplyKeyboards:
    @staticmethod
    async def get_menu() -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton(text="🎰  Играть  🎰")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="ℹ Информация")],
        ]
        menu_kb = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True,
                                      input_field_placeholder="Что вы хотите сделать?")
        return menu_kb


class InlineKeyboards:
    @staticmethod
    async def get_games(available_games: list[Game]) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(text='➕ Создать', callback_data='create'),
                InlineKeyboardButton(text='♻ Обновить', callback_data='refresh')]
        ]
        builder = InlineKeyboardBuilder(markup=keyboard)

        for game in available_games[:8]:
            text = f'{game.type.value}#{game.number} | {game.bet} | {(await games.get_players_of_game(game))[0].name}'
            builder.button(text=text, callback_data=GamesCallbackFactory(number=game.number, action='show')).row()

        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    async def get_join_markup(game: Game) -> InlineKeyboardMarkup | None:
        if len(await games.get_players_of_game(game)) == game.max_players:
            return None

        builder = InlineKeyboardBuilder()

        if not len(await games.get_players_of_game(game)) == game.max_players:
            builder.button(
                text='✅ Присоединиться', callback_data=GamesCallbackFactory(action='join', number=game.number)
            )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def get_profile_markup() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(text="💰 Вывести", callback_data="withdraw"),
                InlineKeyboardButton(text="💳 Пополнить", callback_data="top_up", ),
            ],
            [InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral_system")]
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def get_information_markup() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(text='Чат', url='https://t.me/'),
                InlineKeyboardButton(text='Новости', url='https://t.me/')
            ],
            [InlineKeyboardButton(text='Правила', url='https://t.me/')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def get_referrals_markup(bot_username: str, user_telegram_id: int) -> InlineKeyboardMarkup:
        url = invite_link.format(bot_username=bot_username, user_tg_id=user_telegram_id)
        keyboard = [
            [InlineKeyboardButton(text='📲 Пригласить друга', url=url)]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


