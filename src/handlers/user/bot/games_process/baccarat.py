from typing import Collection, Union, Any, Generator

from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from src.database import Game, PlayerMove, games, player_moves, transactions
from src.keyboards.user.games import BaccaratKeyboards
from src.keyboards import UserMenuKeyboards
from src.messages.user.games import BaccaratMessages
from src.misc.baccarat import BettingOption, BaccaratResult
from src.utils.cards import get_shuffled_deck, Card
from src.utils.game_images import draw_baccarat_results_image
from settings import Config


# region Utils

async def start_baccarat_game(callback: CallbackQuery, game: Game):
    """Когда все игроки собраны, вызывается функция для старта игры в баккара"""
    player_ids = await games.get_player_ids_of_game(game)

    for player_id in player_ids:
        await callback.bot.send_message(
            chat_id=player_id,
            text=BaccaratMessages.get_baccarat_bet_prompt(),
            reply_markup=BaccaratKeyboards.get_bet_options(),
            parse_mode='HTML'
        )


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


def deal_card(deck: Generator[Card, Any, Any], hand: list[Card]):
    card = next(deck)
    hand.append(card)
    return card


def check_clear_win_and_get_winner(player_points: int, banker_points: int) -> Union[BettingOption, None]:
    if player_points not in (8, 9) and banker_points not in (8, 9):
        return None

    if (player_points == 9 and banker_points < 9) or (player_points == 8 and banker_points < player_points):
        return BettingOption.PLAYER
    elif (player_points != 9 and banker_points == 9) or (banker_points == 8 and player_points < banker_points):
        return BettingOption.BANKER
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


def get_winner(banker_points: int, player_points: int) -> BettingOption:
    if banker_points == player_points:
        return BettingOption.TIE
    elif player_points > banker_points:
        return BettingOption.PLAYER
    else:
        return BettingOption.BANKER


def process_game_and_get_results(game: Game) -> BaccaratResult:
    deck = get_shuffled_deck(decks_cont=2)

    player_cards = [deal_card(deck, []) for _ in range(2)]
    banker_cards = [deal_card(deck, []) for _ in range(2)]

    player_points = count_player_points(player_cards)
    banker_points = count_player_points(banker_cards)

    # Если набрано 8 или 9 очков первыми двумя картами
    winner = check_clear_win_and_get_winner(player_points, banker_points)
    if winner:
        return BaccaratResult(
            player_points=player_points, player_cards=player_cards,
            banker_points=banker_points, banker_cards=banker_cards,
            winner=winner
        )

    # выдача карты игроку, если от 0 до 5 очков
    if player_points < 6:
        player_third_card = deal_card(deck, player_cards)
        # если игрок взял третью карту, проверяем, должен ли банкир брать карту по правилам
        if should_dealer_pick_third_card(banker_points, player_third_card):
            deal_card(deck, banker_cards)
    # если игрок не взял карту, но у дилера от 0 до 5, берёт карту
    elif banker_points < 6:
        deal_card(deck, banker_cards)

    player_points = count_player_points(player_cards)
    banker_points = count_player_points(banker_cards)

    winner = get_winner(banker_points, player_points)

    return BaccaratResult(
        player_points=player_points, player_cards=player_cards,
        banker_points=banker_points, banker_cards=banker_cards,
        winner=winner
    )


async def send_result_to_players(bot, game, result, player_ids):
    # отправляем action загрузки видео
    for player_id in player_ids:
        await bot.send_chat_action(chat_id=player_id, action=ChatAction.UPLOAD_PHOTO)
    # загружаем фото из буфера и отправляем первому юзеру
    try:
        photo_msg = await bot.send_photo(
            chat_id=player_ids[0],
            photo=draw_baccarat_results_image(game_number=game.number, result=result)
        )
    except TelegramBadRequest:
        photo_msg = None

    # копируем фото другим игрокам, если оно создалось успешно
    if photo_msg and photo_msg.photo[0]:
        for player_id in player_ids[1:]:
            await bot.send_photo(
                chat_id=player_id,
                photo=photo_msg.photo[0].file_id
            )

    text = 'Баккарат'
    # отправляем сообщение с результатами игры всем игрокам
    for player_id in player_ids:
        await bot.send_message(
            chat_id=player_id,
            text=text,
            reply_markup=UserMenuKeyboards.get_main_menu(),
            parse_mode='HTML'
        )
    # отправляем сообщение о том, что игра завершена, в чат
    await bot.send_message(chat_id=Config.Games.GAME_CHAT_ID,
                           text=text,
                           parse_mode='HTML')


def get_win_coefficient(winner: BettingOption):
    match winner:
        case BettingOption.PLAYER:
            return 2
        case BettingOption.BANKER:
            return 1.95
        case BettingOption.TIE:
            return 8
        case _:
            return None


async def finish_game(bot: Bot, game: Game, bet_choices: Collection[PlayerMove], result: BaccaratResult):
    player_ids = await games.get_player_ids_of_game(game)

    win_coefficient = get_win_coefficient(result.winner)

    for choice in bet_choices:
        if choice.value == result.winner.value:
            await transactions.accrue_winnings(game, (await choice.player.get()).telegram_id, game.bet * win_coefficient)

    await send_result_to_players(bot, game, result, player_ids)

    await games.finish_game(game.number)
    await player_moves.delete_game_moves(game)


# endregion Utils

# region Handlers


async def handle_bet_move_message(message: Message):
    """Обрабатывает сообщение с тем, на кого ставит игрок - банк, ничью, игрока"""
    user_id = message.from_user.id
    game = await games.get_user_active_game(user_id)
    if not game:
        return

    betting_option_choice = 0
    if message.text == '👤 Игрок':
        betting_option_choice = BettingOption.PLAYER.value
    elif message.text == '🤝 Ничья':
        betting_option_choice = BettingOption.TIE.value
    elif message.text == '🏦 Банкир':
        betting_option_choice = BettingOption.BANKER.value

    await player_moves.add_player_move_if_not_moved(game, user_id, betting_option_choice)

    bet_choices = await player_moves.get_game_moves(game)

    if len(bet_choices) == game.max_players:
        result = process_game_and_get_results(game)
        await finish_game(message.bot, game, bet_choices, result)


def register_baccarat_game_handlers(router: Router):
    router.message.register(handle_bet_move_message, F.text)
