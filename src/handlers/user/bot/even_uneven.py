from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.database import transactions
from src.database.games.even_uneven import add_player_bet
from src.keyboards.user.games import EvenUnevenKeyboards
from src.misc import UserStates
from src.utils.game_validations import validate_and_extract_bet_amount


def get_bet_option_description(option: str):
    match option:
        case 'A':
            return 'одно из чисел чётное'
        case 'B':
            return 'одно из чисел нечётное'
        case 'C':
            return '1>2'
        case 'D':
            return '2>1'
        case 'E':
            return 'оба чётные'
        case 'F':
            return 'оба нечётные'
        case 'G':
            return 'число 5'
        case 'H':
            return '1 == 2'


async def show_bet_entering(message: Message, state: FSMContext, round_number: int, bet_option: str):
    await message.answer(
        text='Введите сумму ставки:',
        reply_markup=EvenUnevenKeyboards.get_cancel_bet_entering(),
        parse_mode='HTML'
    )
    await state.update_data(round_number=round_number, bet_option=bet_option)
    await state.set_state(UserStates.EnterEvenUnevenBet.wait_for_bet)


from loguru import logger
async def handle_bet_amount_message(message: Message, state: FSMContext):
    """Обработка сообщения с суммой ставки"""
    data = await state.get_data()
    bet_amount = await validate_and_extract_bet_amount(message)
    if not bet_amount:
        return

    # списываем деньги
    await transactions.deduct_bet_from_user_balance(user_telegram_id=message.from_user.id, amount=bet_amount)

    # сохраняем ставку
    await add_player_bet(player_id=message.from_user.id, amount=bet_amount, option=data.get('bet_option'))

    # отвечаем, что ставка принята
    option_description = get_bet_option_description(data.get("bet_option"))
    await message.answer(
        f'Вы поставили {bet_amount:.2f} руб на: {option_description}'
    )

    logger.info(f"Игрок {message.from_user.full_name}; Ставка:{bet_amount}; Опция: {option_description} ({data.get('bet_option')})")

    await state.clear()


async def handle_cancel_bet_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()


def register_even_uneven_handlers(router: Router):
    router.message.register(handle_bet_amount_message, UserStates.EnterEvenUnevenBet.wait_for_bet)
    router.callback_query.register(handle_cancel_bet_callback,
                                   F.data == 'cancel_even_uneven_bet',
                                   UserStates.EnterEvenUnevenBet.wait_for_bet)
