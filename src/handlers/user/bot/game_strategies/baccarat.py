import asyncio
from typing import Collection, Union, Any, Generator

from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from src.database import Game, PlayerScore, games, game_scores, transactions, playing_cards
from src.handlers.user.game_strategy import GameStrategy
from src.misc.enums import BaccaratBettingOption
from src.utils.game_messages_sender import GameMessageSender
from src.utils.generate_card_images import BaccaratImagePainter
from src.keyboards.user.games import BaccaratKeyboards
from src.messages.user.games import BaccaratMessages
from src.keyboards import UserMenuKeyboards
from src.misc import GameStatus
from src.utils.cards import get_shuffled_deck, Card
from settings import Config


# region Utils

BANKER_ID = 0
PLAYER_ID = 1


def get_points_of_card(card: Card) -> int:
    if card.value in ["10", "В", "Д", "К"]:
        return 0
    elif card.value == 'Т':
        return 1
    else:
        return int(card.value)


def count_player_points(cards: list[Card]) -> int:
    points = (get_points_of_card(card) for card in cards)
    return sum(points) % 10


async def deal_card(deck: Generator[Card, Any, Any], player_id: int, game: Game):
    card = next(deck)
    await playing_cards.add_card_to_player_hand(
        game_number=game.number, player_telegram_id=player_id,
        card_suit=card.suit, card_value=card.value,
        points=get_points_of_card(card)
    )
    return card


def get_win_coefficient(winner: BaccaratBettingOption):
    match winner:
        case BaccaratBettingOption.PLAYER:
            return 2
        case BaccaratBettingOption.BANKER:
            return 1.95
        case BaccaratBettingOption.TIE:
            return 8
        case _:
            return None


def check_clear_win_and_get_won_option(player_points: int, banker_points: int) -> Union[BaccaratBettingOption, None]:
    if player_points not in (8, 9) and banker_points not in (8, 9):
        return None

    if (player_points == 9 and banker_points < 9) or (player_points == 8 and banker_points < player_points):
        return BaccaratBettingOption.PLAYER
    elif (player_points != 9 and banker_points == 9) or (banker_points == 8 and player_points < banker_points):
        return BaccaratBettingOption.BANKER
    return None


def should_dealer_pick_third_card(banker_points: int, player_third_card: Card) -> bool:
    card_points = get_points_of_card(player_third_card)
    flag = (
            (0 <= banker_points <= 2) or
            (banker_points == 3 and (card_points <= 7 or card_points == 9)) or
            (banker_points == 4 and 2 <= card_points <= 7) or
            (banker_points == 5 and 4 <= card_points <= 7) or
            (banker_points == 6 and 6 <= card_points <= 7)
    )
    return True if flag else False


def get_winner(banker_points: int, player_points: int) -> BaccaratBettingOption:
    if banker_points == player_points:
        return BaccaratBettingOption.TIE
    elif player_points > banker_points:
        return BaccaratBettingOption.PLAYER
    else:
        return BaccaratBettingOption.BANKER


async def process_game_and_get_won_option(bot: Bot, game: Game):
    deck = get_shuffled_deck(decks_count=2)

    player_cards = [await deal_card(player_id=PLAYER_ID, game=game, deck=deck) for _ in range(2)]
    banker_cards = [await deal_card(player_id=BANKER_ID, game=game, deck=deck) for _ in range(2)]

    player_points = count_player_points(player_cards)
    banker_points = count_player_points(banker_cards)

    # Если набрано 8 или 9 очков первыми двумя картами
    winner = check_clear_win_and_get_won_option(player_points, banker_points)
    if winner:
        return winner

    # выдача карты игроку, если от 0 до 5 очков
    sender = GameMessageSender(bot, game)
    if player_points < 6:
        player_third_card = await deal_card(deck=deck, player_id=PLAYER_ID, game=game)
        await sender.send(text='Игрок берёт третью карту...')
        await asyncio.sleep(0.8)

        # если игрок взял третью карту, проверяем, должен ли банкир брать карту по правилам
        if should_dealer_pick_third_card(banker_points, player_third_card):
            await deal_card(deck=deck, player_id=BANKER_ID, game=game)
            await sender.send(text='Дилер берёт третью карту...')
            await asyncio.sleep(0.8)
    # если игрок не взял карту, но у дилера от 0 до 5, берёт карту
    elif banker_points < 6:
        await deal_card(deck=deck, player_id=BANKER_ID, game=game)
        await sender.send(text='Дилер берёт третью карту...')
        await asyncio.sleep(0.8)


async def send_result_to_players(bot, game: Game, bet_choices: Collection[PlayerScore]):
    player_ids = await games.get_player_ids_of_game(game)

    # отправляем action загрузки фото
    await asyncio.gather(*[
        bot.send_chat_action(chat_id=player_id, action=ChatAction.UPLOAD_PHOTO)
        for player_id in player_ids
    ])

    # Генерируем фото и загружаем из буфера. Отправляем первому юзеру

    image_painter = BaccaratImagePainter(game=game)
    img = await image_painter.get_image()

    result_photo_file_id = (await bot.send_photo(
        chat_id=player_ids[0], photo=img
    )).photo[0].file_id

    # Копируем фото другим игрокам, если оно создалось успешно
    sender = GameMessageSender(bot, game)
    if result_photo_file_id:
        await sender.send(photo=result_photo_file_id, player_ids=player_ids[1:])

    # Отправляем сообщение с результатами игры всем игрокам
    text = await BaccaratMessages.get_baccarat_results(bet_choices)
    reply_markup = UserMenuKeyboards.get_main_menu()
    await sender.send(text, markup=reply_markup)

    # отправляем сообщение о том, что игра завершена, в чат
    await bot.send_photo(
        photo=result_photo_file_id,
        chat_id=Config.Games.GAME_CHAT_ID,
        caption=text,
        parse_mode='HTML'
    )


# endregion Utils

# region Handlers


class BaccaratStrategy(GameStrategy):

    @staticmethod
    async def start_game(callback: CallbackQuery, game: Game):
        """Когда все игроки собраны, вызывается функция для старта игры в баккара"""
        text = BaccaratMessages.get_bet_prompt()
        reply_markup = BaccaratKeyboards.get_bet_options()
        await GameMessageSender(callback.bot, game).send(text, markup=reply_markup)

    @staticmethod
    def __interpret_user_bet_choice(bet_text: str) -> int:
        match bet_text:
            case '👤 Игрок':
                return BaccaratBettingOption.PLAYER.value
            case '🤝 Ничья':
                return BaccaratBettingOption.TIE.value
            case '🏦 Банкир':
                return BaccaratBettingOption.BANKER.value

    @classmethod
    async def handle_bet_move_message(cls, message: Message) -> None:
        """Обрабатывает сообщение с тем, на кого ставит игрок - банк, ничью, игрока"""
        user_id = message.from_user.id
        game = await games.get_user_unfinished_game(user_id)
        if not game:
            return

        betting_option_number = cls.__interpret_user_bet_choice(message.text)
        if not betting_option_number:
            return

        await game_scores.add_player_move_if_not_moved(game, user_id, betting_option_number)
        await message.answer(text='Ваша ставка принята', reply_markup=ReplyKeyboardRemove())

        if await game_scores.is_all_players_moved(game):
            await BaccaratStrategy.finish_game(message.bot, game)

    @staticmethod
    async def finish_game(bot: Bot, game: Game):
        if game.status != GameStatus.ACTIVE:
            return
        await games.finish_game(game)

        await GameMessageSender(bot, game).send(text='Все игроки сделали ставки')
        await process_game_and_get_won_option(game=game, bot=bot)

        player_res = await playing_cards.count_player_score(game_number=game.number, player_id=PLAYER_ID)
        banker_res = await playing_cards.count_player_score(game_number=game.number, player_id=BANKER_ID)
        if banker_res > player_res: won_option = BaccaratBettingOption.BANKER
        elif banker_res < player_res: won_option = BaccaratBettingOption.PLAYER
        else: won_option = BaccaratBettingOption.TIE

        win_coefficient = get_win_coefficient(won_option)
        bet_choices = await game_scores.get_game_moves(game)

        for choice in bet_choices:
            if choice.value == won_option.value:
                await transactions.accrue_winnings(
                    game=game,
                    winner_telegram_id=(await choice.player.get()).telegram_id,
                    amount=game.bet * win_coefficient
                )

        await send_result_to_players(bot, game, bet_choices)
        await game_scores.delete_game_scores(game)
        await playing_cards.delete_game_cards(game_number=game.number)

    @classmethod
    def register_moves_handlers(cls, router: Router):
        router.message.register(BaccaratStrategy.handle_bet_move_message, F.text)
