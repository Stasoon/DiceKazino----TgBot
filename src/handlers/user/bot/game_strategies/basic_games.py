import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message

from src.database import games, Game, transactions
from src.database.games import game_scores
from src.handlers.user.bot.game_strategies.game_strategy import GameStrategy
from src.keyboards import UserMenuKeyboards, UserPrivateGameKeyboards
from src.messages import UserPublicGameMessages
from src.utils.game_messages_sender import GameMessageSender


class BasicGameStrategy(GameStrategy):

    @staticmethod
    async def start_game(bot: Bot, game: Game):
        text = 'Нажмите на клавиатуру, чтобы походить'
        markup = UserPrivateGameKeyboards.get_dice_kb(game.game_type.value)
        await GameMessageSender(bot, game).send(text, markup=markup)

    @staticmethod
    async def finish_game(bot: Bot, game: Game):
        win_coefficient = 2
        game_moves = await game_scores.get_game_moves(game)
        await games.finish_game(game)
        await game_scores.delete_game_scores(game)
        winner_id = None

        max_move = max(game_moves, key=lambda move: move.value)

        if all(move.value == max_move.value for move in game_moves):  # Если значения одинаковы (ничья)
            # Возвращаем деньги участникам
            for move in game_moves:
                player = await move.player.get()
                await transactions.make_bet_refund(game=game, player_id=player.telegram_id, amount=game.bet)
        else:  # значения разные
            # Получаем победителя
            winner_id = (await max_move.player.get()).telegram_id
            # Начисляем выигрыш на баланс
            await transactions.accrue_winnings(
                game_category=game.category, winner_telegram_id=winner_id,
                amount=game.bet * win_coefficient
            )

        seconds_to_wait = 3
        await asyncio.sleep(seconds_to_wait)

        text = await UserPublicGameMessages.get_game_in_chat_finish(game, winner_id, game_moves,
                                                                    game.bet * win_coefficient)
        markup = UserMenuKeyboards.get_main_menu()
        await GameMessageSender(bot, game).send(text, markup=markup)

    @classmethod
    async def handle_game_move_message(cls, message: Message):
        game = await games.get_user_unfinished_game(message.from_user.id)
        if not game:
            return 

        dice = message.dice

        # Если игрок есть в игре и тип эмодзи соответствует
        if game and dice.emoji == game.game_type.value:
            await cls.process_player_move(game, message)

        # если все походили, ждём окончания анимации и заканчиваем игру
        if len(await game_scores.get_game_moves(game)) == game.max_players:
            await cls.finish_game(bot=message.bot, game=game)

    @classmethod
    async def process_player_move(cls, game: Game, message: Message):
        """Обрабатывает ход в игре"""
        game_moves = await game_scores.get_game_moves(game)
        player_telegram_id = message.from_user.id
        dice_value = message.dice.value

        # если не все игроки сделали ходы
        if len(game_moves) != game.max_players:
            await game_scores.add_player_move_if_not_moved(
                game=game, player_telegram_id=player_telegram_id, move_value=dice_value
            )

    @classmethod
    def register_moves_handlers(cls, router: Router):
        router.message.register(cls.handle_game_move_message, F.dice)
