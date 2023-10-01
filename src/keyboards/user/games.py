from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums.dice_emoji import DiceEmoji

from src.database import Game, games
from src.misc import GamesCallback, NavigationCallback, GameType, GameCategory
from src.misc.callback_factories import BlackJackCallback


class BaccaratKeyboards:
    @staticmethod
    def get_bet_options() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='👤 Игрок')],
            [KeyboardButton(text='🤝 Ничья')],
            [KeyboardButton(text='🏦 Банкир')],
        ])


class BlackJackKeyboards:
    @staticmethod
    def get_controls(game_number: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='👇 Взять', callback_data=BlackJackCallback(game_number=game_number, move='take'))
        builder.button(text='✋ Хватит', callback_data=BlackJackCallback(game_number=game_number, move='stand'))
        return builder.as_markup()
        # "🙅‍♂ Отказаться"


# клавиатуры для отображения в боте
class UserPrivateGameKeyboards:
    @staticmethod
    def get_dice_kb(dice_emoji: str) -> ReplyKeyboardMarkup:
        """Возвращает reply клавиатуру с эмодзи"""
        dice_button = KeyboardButton(text=dice_emoji)
        return ReplyKeyboardMarkup(keyboard=[[dice_button]])

    @staticmethod
    def get_play_menu() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться после перехода в Играть"""
        builder = InlineKeyboardBuilder()

        builder.button(text='🎲 Games', callback_data=GamesCallback(action='show', game_category=GameCategory.BASIC))
        builder.button(text='♠ BlackJack', callback_data=GamesCallback(action='show',
                                                                       game_category=GameCategory.BLACKJACK,
                                                                       game_type=GameType.BJ))
        builder.button(text='🎴 Baccarat', callback_data=GamesCallback(action='show',
                                                                      game_category=GameCategory.BACCARAT,
                                                                      game_type=GameType.BACCARAT))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def get_game_category(available_games: list[Game], category: GameCategory) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться при нажатии на категорию игр"""
        builder = InlineKeyboardBuilder()
        builder.button(text='➕ Создать', callback_data=GamesCallback(action='create', game_category=category))
        builder.button(text='♻ Обновить', callback_data=GamesCallback(action='refresh', game_category=category))
        builder.adjust(2)
        builder.button(text='📊 Статистика', callback_data=GamesCallback(action='stats', game_category=category))

        for game in available_games[:10]:
            text = f'{game.game_type.value}#{game.number} | 💰{game.bet} | {(await games.get_creator_of_game(game)).name}'
            builder.button(
                text=text,
                callback_data=GamesCallback(action='show', game_category=category, game_number=game.number)
            ).row()

        builder.button(text='🔙 Назад', callback_data=NavigationCallback(branch='game_strategies'))
        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    def get_back_from_stats(category: GameCategory) -> InlineKeyboardMarkup:
        """Возвращает кнопку для возврата из окна со статистикой по категории игр"""
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 Назад', callback_data=GamesCallback(action='show', game_category=category))
        return builder.as_markup()

    @staticmethod
    def get_basic_game_types() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для выбора типа базовой игры при её создании"""
        builder = InlineKeyboardBuilder()
        # ide может ругаться, но всё в порядке
        dice_emojis = [emoji.value for emoji in DiceEmoji]

        for game_type in GameType:
            if game_type.value in dice_emojis:
                builder.button(
                    text=f'{game_type.value} {game_type.get_full_name()}',
                    callback_data=GamesCallback(
                        action='create',
                        game_category=GameCategory.BASIC,
                        game_type=game_type
                    )
                )

        builder.adjust(2)
        back_builder = InlineKeyboardBuilder()
        back_builder.button(text='🔙 Назад',
                            callback_data=GamesCallback(action='show', game_category=GameCategory.BASIC))
        builder.attach(back_builder)
        return builder.as_markup()

    @staticmethod
    def get_cancel_bet_entering(game_category: GameCategory) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 Отмена', callback_data=GamesCallback(action='show', game_category=game_category))
        return builder.as_markup()

    @staticmethod
    async def get_join_game_or_back(game_category: GameCategory, game_number: int) -> InlineKeyboardMarkup:
        """Клавиатура для просмотра игры из меню"""
        builder = InlineKeyboardBuilder()
        builder.button(text='⚡ Принять ставку ⚡',
                       callback_data=GamesCallback(
                           action='join', game_category=game_category, game_number=game_number)
                       )
        builder.button(text='🔙 Назад', callback_data=GamesCallback(action='show', game_category=game_category))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def show_game(game: Game) -> InlineKeyboardMarkup | None:
        """Принять ставку (когда перешёл в бота)"""
        if len(await games.get_players_of_game(game)) == game.max_players:
            return None

        builder = InlineKeyboardBuilder()

        builder.button(
            text=f'{game.game_type.value} Присоединиться',
            callback_data=GamesCallback(
                action='join', game_number=game.number,
                game_category=game.category, game_type=game.game_type
            )
        )

        return builder.as_markup()


# клавиатуры для отображения в чатах
class UserPublicGameKeyboards:
    @staticmethod
    async def get_go_to_bot_and_join(game: Game, bot_username: str):
        """Перейти в бота с кнопкой старт и показать игру (кнопка для чата)"""
        if len(await games.get_players_of_game(game)) == game.max_players:
            return None

        builder = InlineKeyboardBuilder()
        builder.button(
            text='🔗 Присоединиться в боте',
            url=f"https://t.me/{bot_username}?start=_{game.game_type.name}_{game.number}"
        )
        return builder.as_markup()

    @staticmethod
    async def get_join_game_in_chat(game: Game) -> InlineKeyboardMarkup | None:
        """Клавиатура под игрой для чата"""
        if len(await games.get_players_of_game(game)) == game.max_players:
            return None

        builder = InlineKeyboardBuilder()
        builder.button(
            text='✅ Присоединиться', callback_data=GamesCallback(action='join', game_number=game.number)
        )
        return builder.as_markup()
