from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.database import users, games, transactions
from src.handlers.user.chat.chat import send_game_created_in_bot_notification
from src.keyboards.user import UserPrivateGameKeyboards, UserMenuKeyboards
from src.messages.user import UserMenuMessages, UserPrivateGameMessages, get_full_game_info_text, \
    GameErrors, BalanceErrors, InputErrors
from src.misc import NavigationCallback, GamesCallback, GameCategory, GameType, UserStates, GameStatus
from settings import Config


# region Utils


async def validate_and_get_deposit_amount(amount_message: Message) -> float | None:
    """Делает проверку суммы депозита, написанной в сообщении.
    При некорректно введённых данных, отправляет сообщение и возвращает None.
    Если всё хорошо, возвращает float из сообщения"""
    try:
        bet_amount = float(amount_message.text.replace(',', '.'))
    except (ValueError, TypeError):
        await amount_message.answer(InputErrors.get_message_not_number_retry(), parse_mode='HTML')
        return None

    min_bet_amount = Config.Games.min_bet_amount

    if await users.get_user_balance(amount_message.from_user.id) < bet_amount:
        await amount_message.answer(text=BalanceErrors.get_low_balance())
        return None

    if bet_amount < min_bet_amount:
        await amount_message.answer(
            text=BalanceErrors.get_insufficient_transaction_amount(min_bet_amount),
            parse_mode='HTML'
        )
        return None

    return bet_amount


async def get_play_message_data(user_id: int) -> dict:
    text = UserMenuMessages.get_play_menu(await users.get_user_or_none(user_id))
    reply_markup = UserPrivateGameKeyboards.get_play_menu()
    return {'text': text, 'reply_markup': reply_markup, 'parse_mode': 'HTML'}


async def show_basic_game_types(to_message: Message):
    await to_message.edit_text(
        text=UserPrivateGameMessages.get_choose_game_type(),
        reply_markup=UserPrivateGameKeyboards.get_basic_game_types(),
        parse_mode='HTML'
    )


async def show_bet_entering(callback: CallbackQuery, game_type: GameType, game_category: GameCategory):
    message = callback.message
    await message.delete()
    await message.answer(
        text=await UserPrivateGameMessages.enter_bet_amount(callback.from_user.id, game_type.get_full_name()),
        reply_markup=UserPrivateGameKeyboards.get_cancel_bet_entering(game_category),
        parse_mode='HTML'
    )

# endregion


# region Handlers

async def handle_play_button(message: Message, state: FSMContext):
    """Обработка кнопки Играть из меню"""
    await state.clear()
    await message.answer(**(await get_play_message_data(message.from_user.id)))


async def handle_game_category_callback(callback: CallbackQuery, callback_data: GamesCallback, state: FSMContext):
    """Обработка нажатия на одну из категорий игр"""
    await state.clear()

    available_games = await games.get_bot_available_games(callback_data.game_category)
    await callback.message.edit_text(
        text=UserPrivateGameMessages.get_game_category(category=callback_data.game_category),
        reply_markup=await UserPrivateGameKeyboards.get_game_category(available_games, category=callback_data.game_category)
    )


async def handle_game_category_stats_callback(callback: CallbackQuery, callback_data: GamesCallback):
    """Показывает статистику по выбранной категории игр"""
    game_category = callback_data.game_category
    await callback.message.edit_text(
        text=await UserPrivateGameMessages.get_game_category_stats(game_category),
        reply_markup=UserPrivateGameKeyboards.get_back_from_stats(game_category),
        parse_mode='HTML'
    )


async def handle_refresh_games_callback(callback: CallbackQuery, callback_data: GamesCallback):
    """Обновление списка доступных игр"""
    available_games = await games.get_bot_available_games(callback_data.game_category)
    reply_markup = await UserPrivateGameKeyboards.get_game_category(available_games, callback_data.game_category)
    try:
        await callback.message.edit_reply_markup(reply_markup=reply_markup)
    except TelegramBadRequest:
        pass
    await callback.answer()


async def handle_create_game_callback(callback: CallbackQuery, callback_data: GamesCallback, state: FSMContext):
    """Обработка нажатия на кнопку Создать"""
    user_active_game = await games.get_user_unfinished_game(callback.from_user.id)
    if user_active_game:
        await callback.answer(text=GameErrors.get_another_game_not_finished(user_active_game))
        return

    game_category = callback_data.game_category

    # СЮДА ДОБАВЛЯТЬ СОЗДАНИЕ ИГРЫ
    if game_category == GameCategory.BASIC:
        await show_basic_game_types(callback.message)
    else:
        if game_category == GameCategory.BLACKJACK:
            game_type = GameType.BJ
        elif game_category == GameCategory.BACCARAT:
            game_type = GameType.BACCARAT

        await show_bet_entering(callback, game_type, game_category)

        await state.update_data(game_category=game_category, game_type=game_type)
        await state.set_state(UserStates.EnterBet.wait_for_bet_amount)


async def handle_basic_game_type_callback(callback: CallbackQuery, callback_data: GamesCallback, state: FSMContext):
    """Обработка нажатия на тип обычной игры при её создании"""
    await show_bet_entering(callback, callback_data.game_type, callback_data.game_category)

    await state.update_data(game_category=callback_data.game_category, game_type=callback_data.game_type)
    await state.set_state(UserStates.EnterBet.wait_for_bet_amount)


async def handle_bet_amount_message(message: Message, state: FSMContext):
    """Обработка сообщения с суммой ставки"""
    bet_amount = await validate_and_get_deposit_amount(message)
    data = await state.get_data()

    if not bet_amount:
        return

    # создаём игру
    created_game = await games.create_game(
        game_category=data.get('game_category'), game_type=data.get('game_type'),
        chat_id=message.chat.id,
        creator_telegram_id=message.from_user.id, max_players=2, bet=bet_amount
    )
    # списываем деньги
    await transactions.debit_bet(created_game, message.from_user.id, bet_amount)
    # отвечаем, что игра создана
    await message.answer(
        text=UserPrivateGameMessages.get_game_created(created_game),
        reply_markup=UserMenuKeyboards.get_main_menu(),
        parse_mode='HTML',
    )

    await send_game_created_in_bot_notification(message.bot, created_game)

    await state.clear()


async def handle_show_game_callback(callback: CallbackQuery, callback_data: GamesCallback):
    """Обработка нажатия на доступную игру"""
    game = await games.get_game_obj(callback_data.game_number)
    await callback.message.edit_text(
        text=await get_full_game_info_text(game),
        reply_markup=await UserPrivateGameKeyboards.get_join_game_or_back(
            callback_data.game_category, callback_data.game_number
        ),
        parse_mode='HTML'
    )


async def handle_back_in_play_callback(callback: CallbackQuery):
    await callback.message.edit_text(**(await get_play_message_data(callback.from_user.id)))


def register_play_handlers(router: Router):
    router.message.register(handle_play_button, F.text.contains('🎰  Играть  🎰'))

    # показать игру
    router.callback_query.register(handle_show_game_callback, GamesCallback.filter(
        (F.action == 'show') & F.game_number
    ))
    # показать категорию
    router.callback_query.register(handle_game_category_callback, GamesCallback.filter(
        (F.action == 'show') & F.game_category))

    # статистика
    router.callback_query.register(handle_game_category_stats_callback, GamesCallback.filter(
        F.action == 'stats'
    ))
    # обновить игры
    router.callback_query.register(handle_refresh_games_callback, GamesCallback.filter(
        F.action == 'refresh'
    ))
    # создать игру
    router.callback_query.register(handle_create_game_callback, GamesCallback.filter(
        (F.action == 'create') & ~F.game_type & ~F.game_number
    ))

    router.callback_query.register(handle_basic_game_type_callback, GamesCallback.filter(
        (F.action == 'create') & F.game_type
    ))
    # назад
    router.message.register(handle_bet_amount_message, UserStates.EnterBet.wait_for_bet_amount)

    router.callback_query.register(handle_back_in_play_callback, NavigationCallback.filter(
        (F.branch == 'game_strategies') & ~F.option))
