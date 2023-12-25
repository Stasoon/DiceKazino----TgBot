import asyncio

from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from src.database import Game, games, users, transactions
from src.database.games import playing_cards, game_scores
from src.handlers.user.bot.game_strategies.game_strategy import GameStrategy
from src.keyboards import UserMenuKeyboards
from src.keyboards.user.games import BlackJackKeyboards
from src.messages.user.games import BlackJackMessages
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
    async def __send_move_cards_to_player(
            bot: Bot, game: Game, caption_text: str | None, player_id: int, show_markup: bool = True
    ) -> str:
        await bot.send_chat_action(chat_id=player_id, action=ChatAction.UPLOAD_PHOTO)
        image_painter = BlackJackImagePainter(game)
        markup = BlackJackKeyboards.get_controls(game_number=game.number) if show_markup else None
        photo = await image_painter.get_image()

        result_photo_file_id = await bot.send_photo(
            chat_id=player_id, photo=photo, caption=caption_text, reply_markup=markup
        )
        return result_photo_file_id.photo[0].file_id

    @staticmethod
    async def __calculate_winnings_and_losses(game: Game, dealer_points: int) -> dict[int, float]:
        """
        Вычисляет победителей и начисляет им выигрыши.
        :returns:
            dict[int, float]: словарь с победителями в формате id игрока: сумма выигрыша
        """
        players_scores = await game_scores.get_game_moves(game)
        won_players = {}

        for player_score in players_scores:
            # Если перебор очков, пропускаем игрока
            if player_score.value > 21:
                continue

            player_id = (await player_score.player.get()).telegram_id
            # обычный выигрыш
            if player_score.value > dealer_points or dealer_points > 21:
                amount = await transactions.accrue_winnings(
                    game_category=game.category, winner_telegram_id=player_id, amount=game.bet * 2
                )
                won_players[player_id] = amount
                continue
            # если ничья
            elif player_score.value == dealer_points:
                await transactions.make_bet_refund(player_id=player_id, amount=game.bet, game=game)
                # !!!!
                continue

            # блэк джек (чистая победа)
            player_cards = await playing_cards.get_player_cards(game_number=game.number, player_id=player_id)
            if len(player_cards) == 2 and player_score.value == 21:
                amount = await transactions.accrue_winnings(
                    game_category=game.category, winner_telegram_id=player_id, amount=game.bet * 2.5
                )
                won_players[player_id] = amount
                continue

        return won_players

    @staticmethod
    async def __get_result_text(won_players: dict[int, float], player_id: int):
        text = None  # Инициализируем переменную text для каждого игрока
        if player_id not in won_players:
            text = BlackJackMessages.get_player_loose()
        elif player_id in won_players:
            player_name = (await users.get_user_or_none(telegram_id=player_id)).name
            text = BlackJackMessages.get_player_won(
                player_name=player_name, win_amount=won_players.get(player_id)
            )

        # Если won_players пуст, то устанавливаем текст о победе дилера
        if len(won_players) == 0:
            text = BlackJackMessages.get_dealer_won()

        return text

    @staticmethod
    async def __send_result_photo(bot: Bot, game: Game, won_players: dict[int, float], player_ids: list[int]):
        # отправляем action загрузки фото
        await asyncio.gather(*[
            bot.send_chat_action(chat_id=player_id, action=ChatAction.UPLOAD_PHOTO)
            for player_id in player_ids
        ])

        # Генерируем фото и загружаем из буфера. Отправляем первому юзеру
        image_painter = BlackJackImagePainter(game=game)
        img = await image_painter.get_image(is_finish=True)
        text = await BlackJackStrategy.__get_result_text(player_id=player_ids[0], won_players=won_players)

        result_photo_file_id = await bot.send_photo(
            chat_id=player_ids[0], photo=img, caption=text
        )
        result_photo_file_id = result_photo_file_id.photo[0].file_id

        # Копируем фото другим игрокам, если оно создалось успешно
        if result_photo_file_id:
            for player_id in player_ids[1:]:
                text = await BlackJackStrategy.__get_result_text(player_id=player_id, won_players=won_players)
                await bot.send_photo(
                    chat_id=player_id,
                    caption=text,
                    photo=result_photo_file_id
                )

    @staticmethod
    async def start_game(bot: Bot, game: Game):
        player_ids = sorted(await games.get_player_ids_of_game(game))

        # Выдаём две карты банкиру
        [await give_card_to_dealer_and_get_score(game.number) for _ in range(2)]

        # выдаём карты игрокам
        for player_id in player_ids:
            for _ in range(2):
                await deal_next_card_for_player_and_get_score(game.number, player_id)

        for player_id in player_ids:
            username = (await users.get_user_or_none(telegram_id=player_id)).name
            await bot.send_message(
                chat_id=player_id, parse_mode='HTML',
                text=BlackJackMessages.get_game_started(player_name=username),
                reply_markup=ReplyKeyboardRemove()
            )

        await BlackJackStrategy.__send_move_cards_to_player(bot, game, None, player_ids[0])

    @staticmethod
    async def let_next_player_move_or_finish_game(player_id, game_number, bot):
        game = await games.get_game_obj(game_number)
        player_ids = sorted(await games.get_player_ids_of_game(game))
        next_player_index = player_ids.index(player_id) + 1

        if next_player_index > len(player_ids) - 1:
            await BlackJackStrategy.finish_game(bot, game)
        else:
            next_player_id = player_ids[next_player_index]
            await BlackJackStrategy.__send_move_cards_to_player(
                bot=bot, game=game, player_id=next_player_id, caption_text=None
            )

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

        # Дилер добирает карты
        dealer_points = await playing_cards.count_dealer_score(game.number)
        while dealer_points <= 16:
            dealer_points = await give_card_to_dealer_and_get_score(game_number=game.number)

        # Начисляем выигрыши
        won_players = await BlackJackStrategy.__calculate_winnings_and_losses(game=game, dealer_points=dealer_points)

        # Отправляем фото с результатом игры
        await GameMessageSender(game=game, bot=bot).send(
            text=BlackJackMessages.get_game_finished(), markup=UserMenuKeyboards.get_main_menu()
        )
        player_ids = await games.get_player_ids_of_game(game)
        await BlackJackStrategy.__send_result_photo(bot=bot, game=game, won_players=won_players, player_ids=player_ids)

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
        if points <= 21:
            await BlackJackStrategy.__send_move_cards_to_player(
                bot=callback.bot, game=game, player_id=callback.from_user.id,
                caption_text=BlackJackMessages.get_player_took_card(player_points=points)
            )
            return

        # выводим игрока из игры, так как перебор очков
        await callback.message.answer(BlackJackMessages.get_too_much_points(player_points=points))
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
        await callback.message.answer(BlackJackMessages.get_player_stopped(player_points=points))
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
