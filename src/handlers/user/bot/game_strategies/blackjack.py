import asyncio

from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from src.database import Game, games, transactions
from src.database.games import playing_cards, game_scores
from src.handlers.user.bot.game_strategies.game_strategy import GameStrategy
from src.keyboards import UserMenuKeyboards
from src.keyboards.user.games import BlackJackKeyboards
from src.misc import GameStatus
from src.misc.callback_factories import BlackJackCallback
from src.utils.cards import Card, get_random_card
from src.utils.card_images import BlackJackImagePainter
from src.utils.game_messages_sender import GameMessageSender


def get_card_points(next_card: Card, current_player_score: int):
    if next_card.value in ('10', 'В', 'Д', 'К'):
        return 10
    elif next_card.value == 'Т':
        return 11 if (current_player_score and current_player_score + 11 < 21) else 1
    else:
        return int(next_card.value[0])


async def deal_next_card_for_player_and_get_score(game_number: int, player_id: int):
    # Генерируем новую карту
    next_card = get_random_card()

    # Вычисляем очки, которые даст карта
    player_points = await playing_cards.count_player_score(game_number=game_number, player_id=player_id)
    next_card_points = get_card_points(next_card=next_card, current_player_score=player_points)

    # Сохраняем карту
    await playing_cards.add_card_to_player_hand(
        game_number=game_number,
        player_telegram_id=player_id,
        card_suit=next_card.suit, card_value=next_card.value,
        points=next_card_points
    )


async def give_card_to_dealer_and_get_score(game_number: int) -> int:
    # Генерируем новую карту
    next_card = get_random_card()

    # Вычисляем очки, которые даст карта
    dealer_points = await playing_cards.count_dealer_score(game_number=game_number)
    next_card_points = get_card_points(next_card=next_card, current_player_score=dealer_points)

    if dealer_points and dealer_points > 16:
        return dealer_points

    # Сохраняем карту
    await playing_cards.add_card_to_dealer_hand(
        game_number=game_number, points=next_card_points,
        card_suit=next_card.suit, card_value=next_card.value
    )
    return dealer_points


# endregion


class BlackJackStrategy(GameStrategy):

    @staticmethod
    async def send_move_to_player(bot: Bot, game: Game, player_id: int, show_markup: bool = True) -> str:
        await bot.send_chat_action(chat_id=player_id, action=ChatAction.UPLOAD_PHOTO)
        image_painter = BlackJackImagePainter(game)
        markup = BlackJackKeyboards.get_controls(game_number=game.number) if show_markup else None
        photo = await image_painter.get_image()

        result_photo_file_id = await bot.send_photo(
            chat_id=player_id,
            photo=photo,
            reply_markup=markup
        )
        return result_photo_file_id.photo[0].file_id

    @staticmethod
    async def send_results(bot: Bot, game: Game):
        player_ids = await games.get_player_ids_of_game(game)

        # отправляем action загрузки фото
        await asyncio.gather(*[
            bot.send_chat_action(chat_id=player_id, action=ChatAction.UPLOAD_PHOTO)
            for player_id in player_ids
        ])

        # Генерируем фото и загружаем из буфера. Отправляем первому юзеру
        image_painter = BlackJackImagePainter(game=game)
        img = await image_painter.get_image(is_finish=True)
        result_photo_file_id = await bot.send_photo(
            chat_id=player_ids[0],
            photo=img,
        )
        result_photo_file_id = result_photo_file_id.photo[0].file_id

        # Копируем фото другим игрокам, если оно создалось успешно
        if result_photo_file_id:
            for player_id in player_ids[1:]:
                await bot.send_photo(
                    chat_id=player_id,
                    photo=result_photo_file_id
                )

        # Отправляем результат в игровой чат
        ...

    @staticmethod
    async def calculate_winnings_and_losses(game: Game, dealer_points: int):
        players_scores = await game_scores.get_game_moves(game)

        for player_score in players_scores:
            # Если перебор очков, пропускаем игрока
            if player_score.value > 21:
                continue

            player_id = (await player_score.player.get()).telegram_id
            # обычный выигрыш
            if player_score.value > dealer_points or dealer_points > 21:
                await transactions.accrue_winnings(game=game, winner_telegram_id=player_id, amount=game.bet * 2)
                continue
            # если ничья
            elif player_score.value == dealer_points:
                await transactions.make_bet_refund(player_id=player_id, amount=game.bet, game=game)
                continue

            # блэк джек (чистая победа)
            player_cards = await playing_cards.get_player_cards(game_number=game.number, player_id=player_id)
            if len(player_cards) == 2 and player_score.value == 21:
                await transactions.accrue_winnings(game=game, winner_telegram_id=player_id, amount=game.bet * 2.5)
                continue

    @staticmethod
    async def start_game(bot: Bot, game: Game):
        player_ids = sorted(await games.get_player_ids_of_game(game))

        # Выдаём две карты банкиру
        [await give_card_to_dealer_and_get_score(game.number) for _ in range(2)]

        # выдаём карты игрокам
        for player_id in player_ids:
            for _ in range(2):
                await deal_next_card_for_player_and_get_score(game.number, player_id)
        sender = GameMessageSender(bot=bot, game=game)
        await sender.send('Игра началась. Ожидайте своего хода', markup=ReplyKeyboardRemove(), player_ids=player_ids)

        await BlackJackStrategy.send_move_to_player(bot, game, player_ids[0])

    @staticmethod
    async def let_next_player_move_or_finish_game(player_id, game_number, bot):
        game = await games.get_game_obj(game_number)
        player_ids = sorted(await games.get_player_ids_of_game(game))
        next_player_index = player_ids.index(player_id) + 1

        if next_player_index > len(player_ids) - 1:
            await BlackJackStrategy.finish_game(bot, game)
        else:
            next_player_id = player_ids[next_player_index]
            await BlackJackStrategy.send_move_to_player(bot=bot, game=game, player_id=next_player_id)

    @staticmethod
    async def finish_game_for_player_and_get_points(game_number: int, user_id: int) -> int | None:
        game = await games.get_game_obj(game_number)
        if game.status != GameStatus.ACTIVE:
            return

        player_score = await playing_cards.count_player_score(game_number=game_number, player_id=user_id)

        # Сохраняем очки
        await game_scores.add_player_move_if_not_moved(
            game=game, player_telegram_id=user_id, move_value=player_score
        )

        return player_score

    @staticmethod
    async def finish_game(bot: Bot, game: Game):
        if game.status != GameStatus.ACTIVE:
            return

        # Останавливаем игру
        await games.finish_game(game)

        # Дилер набирает карты
        dealer_points = await playing_cards.count_dealer_score(game.number)
        while dealer_points < 17:
            dealer_points = await give_card_to_dealer_and_get_score(game_number=game.number)

        # Начисляем выигрыши
        await BlackJackStrategy.calculate_winnings_and_losses(game=game, dealer_points=dealer_points)

        # Отправляем результаты игры
        await GameMessageSender(game=game, bot=bot).send('Игра завершена!', markup=UserMenuKeyboards.get_main_menu())

        await BlackJackStrategy.send_results(bot, game)

        # Очищаем данные
        await game_scores.delete_game_scores(game)
        await playing_cards.delete_game_cards(game_number=game.number)

    @staticmethod
    async def handle_take_action_callback(callback: CallbackQuery, callback_data: BlackJackCallback):
        await callback.message.delete()
        game_number = callback_data.game_number
        game = await games.get_game_obj(game_number)

        # добавляем игроку карту
        await deal_next_card_for_player_and_get_score(game_number, player_id=callback.from_user.id)
        points = await playing_cards.count_player_score(game_number, callback.from_user.id)

        # если меньше не проиграл, даём ещё ход
        if points < 21:
            await BlackJackStrategy.send_move_to_player(bot=callback.bot, game=game, player_id=callback.from_user.id)
            return

        # выводим игрока из игры, так как перебор очков
        await callback.message.answer(f'Ваш счёт: {points}. Ожидайте результатов игры')
        await BlackJackStrategy.finish_game_for_player_and_get_points(
            game_number=game_number, user_id=callback.from_user.id,
        )
        # даём ход следующему игроку / заканчиваем игру
        await BlackJackStrategy.let_next_player_move_or_finish_game(
            bot=callback.bot, game_number=game_number, player_id=callback.from_user.id
        )

    @staticmethod
    async def handle_stand_action_callback(callback: CallbackQuery, callback_data: BlackJackCallback):
        await callback.message.delete()
        game_number = callback_data.game_number
        points = await playing_cards.count_player_score(game_number, callback.from_user.id)

        # Выводим игрока из игры
        await callback.message.answer(f'Вы остановили игру со счётом {points}. Ожидайте результатов игры')
        await BlackJackStrategy.finish_game_for_player_and_get_points(
            game_number=game_number, user_id=callback.from_user.id,
        )
        # даём ход следующему игроку / заканчиваем игру
        await BlackJackStrategy.let_next_player_move_or_finish_game(
            bot=callback.bot, game_number=game_number, player_id=callback.from_user.id
        )

    @classmethod
    def register_moves_handlers(cls, router: Router):
        router.callback_query.register(cls.handle_take_action_callback, BlackJackCallback.filter(F.move == 'take'))
        router.callback_query.register(cls.handle_stand_action_callback, BlackJackCallback.filter(F.move == 'stand'))
