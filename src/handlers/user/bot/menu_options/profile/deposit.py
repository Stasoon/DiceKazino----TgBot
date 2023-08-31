from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from settings import Config
from src.database import transactions
from src.keyboards.user import UserPaymentKeyboards, UserMenuKeyboards
from src.messages import UserPaymentMessages, BalanceErrors, InputErrors, PaymentErrors
from src.misc import (NavigationCallback, BalanceTransactionCallback, UserStates,
                      PaymentCheckCallback, PaymentMethod, TransactionType)
from src.utils import cryptobot, post_payment, logger


# region Utils

async def validate_and_get_deposit_amount(amount_message: Message) -> float | None:
    """Делает проверку суммы депозита, написанной в сообщении.
    При некорректно введённых данных, отправляет сообщение и возвращает None.
    Если всё хорошо, возвращает float из сообщения"""
    try:
        transaction_amount = float(amount_message.text.replace(',', '.'))
    except (ValueError, TypeError):
        await amount_message.answer(InputErrors.get_message_not_number_retry(), parse_mode='HTML')
        return None

    min_transaction_amount = Config.Payments.min_deposit_amount

    if transaction_amount < min_transaction_amount:
        await amount_message.answer(
            text=BalanceErrors.get_insufficient_transaction_amount(min_transaction_amount),
            parse_mode='HTML'
        )
        return None

    return transaction_amount


async def send_cryptobot_invoice(message: Message, currency: str, deposit_amount: float):
    """Когда валюта и сумма пополнения выбраны, формирует и присылает ссылку на платёж"""
    exchange_rate = await cryptobot.get_exchange_rate(currency)

    invoice_data = await cryptobot.create_invoice(
        currency_code=currency,
        amount=deposit_amount / exchange_rate,
        user_id=message.from_user.id,
        bot_username=(await message.bot.get_me()).username
    )

    pay_url = invoice_data.get('pay_url')
    invoice_id = invoice_data.get('invoice_id')
    if not pay_url or not invoice_id:
        await message.answer(PaymentErrors.get_payment_system_error(), parse_mode='HTML')
        return

    await message.answer(
        UserPaymentMessages.get_deposit_link_message(),
        reply_markup=UserPaymentKeyboards.get_invoice(PaymentMethod.CRYPTO_BOT, pay_url, invoice_id),
        parse_mode='HTML')

# endregion Utils


# region Handlers
# ПОПОЛНЕНИЕ БАЛАНСА
async def handle_deposit_callback(callback: CallbackQuery):
    """Показывает сообщение с методами пополнения"""
    await callback.message.edit_text(
        text=UserPaymentMessages.get_choose_deposit_method(),
        reply_markup=UserPaymentKeyboards.get_payment_methods(transaction_type=TransactionType.DEPOSIT),
        parse_mode='HTML'
    )


async def handle_show_deposit_method_callbacks(callback: CallbackQuery, callback_data: BalanceTransactionCallback,
                                               state: FSMContext):
    """Обрабатывает нажатие на метод пополнения"""
    # сохраняем метода платежа
    await state.update_data(method=callback_data.method)
    # если метод вывода - криптобот
    if callback_data.method == PaymentMethod.CRYPTO_BOT:
        await callback.message.edit_text(
            text=UserPaymentMessages.choose_currency(),
            reply_markup=await UserPaymentKeyboards.get_cryptobot_choose_currency(callback_data.transaction_type),
            parse_mode='HTML'
        )
    # если метод вывода - полуавтоматический
    elif callback_data.method in (PaymentMethod.SBP, PaymentMethod.U_MONEY):
        await callback.message.delete()
        await callback.message.answer(
            text=UserPaymentMessages.enter_deposit_amount(min_deposit_amount=Config.Payments.min_deposit_amount),
            reply_markup=UserPaymentKeyboards.get_cancel_payment(), parse_mode='HTML'
        )
        await state.set_state(UserStates.HalfAutoDeposit.wait_for_amount)


# region Полуавтоматические методы

async def handle_halfauto_deposit_amount_message(message: Message, state: FSMContext):
    """Обрабатывает сообщение с размером депозита при полуавтоматическом пополнении"""
    deposit_amount = await validate_and_get_deposit_amount(message)
    deposit_method = (await state.get_data()).get('method')

    if deposit_amount:
        await state.update_data(amount=deposit_amount)
        await message.answer(
            text=UserPaymentMessages.get_half_auto_deposit_method_requisites(deposit_method),
            parse_mode='HTML')
        await state.set_state(UserStates.HalfAutoDeposit.wait_for_screen)


async def handle_halfauto_deposit_screen_message(message: Message, state: FSMContext):
    """Обрабатывает скриншот с платежом при полуавтоматическом пополнении"""
    # если нет фото, отправляем ошибку и просим попробовать снова
    if not message.photo:
        await message.answer(InputErrors.get_photo_expected_retry(), parse_mode='HTML')
        return

    data = await state.get_data()

    try:
        await post_payment.send_payment_request_to_admin(
            bot=message.bot, user_id=message.from_user.id,
            user_name=message.from_user.full_name,
            amount=data.get('amount'),
            photo_file_id=message.photo[0].file_id,
            transaction_type=TransactionType.DEPOSIT,
            method=data.get('method')
        )
    except Exception as e:
        logger.error(f'Ошибка при пополнении баланса {e}')
        await message.answer(PaymentErrors.get_payment_system_error(), parse_mode='HTML')
    else:
        await message.answer(UserPaymentMessages.get_wait_for_administration_confirm(),
                             reply_markup=UserMenuKeyboards.get_main_menu(),
                             parse_mode='HTML')
    await state.clear()


# endregion Полуавтоматические методы

# region Оплата КриптоБотом

async def handle_cryptobot_deposit_currency_callback(callback: CallbackQuery, callback_data: BalanceTransactionCallback,
                                                     state: FSMContext):
    """Обрабатывает нажатие на валюту при пополнении через КриптоБота"""
    await callback.message.delete()
    await callback.message.answer(
        text=UserPaymentMessages.enter_deposit_amount(Config.Payments.min_deposit_amount),
        reply_markup=UserPaymentKeyboards.get_cancel_payment(),
        parse_mode='HTML'
    )
    # сохраняем валюту и просим ввести сумму пополнения
    await state.update_data(currency=callback_data.currency)
    await state.set_state(UserStates.AutoDeposit.wait_for_amount)


async def handle_auto_deposit_amount_message(message: Message, state: FSMContext):
    """Обрабатывает сообщение с размером депозита, показывает платёж"""
    deposit_amount = await validate_and_get_deposit_amount(message)
    if deposit_amount:
        data = await state.get_data()
        await send_cryptobot_invoice(message, data.get('currency'), deposit_amount)
        await state.clear()


async def handle_check_cryptobot_payment(callback: CallbackQuery, callback_data: PaymentCheckCallback):
    """Обработка нажатия на кнопку Проверить при пополнении через КриптоБота"""
    invoice = await cryptobot.get_invoice(callback_data.invoice_id)

    if invoice.get('status') != 'paid':
        await callback.answer(PaymentErrors.get_payment_not_found())
        return

    rate = await cryptobot.get_exchange_rate(invoice.get('asset'))
    amount = float(invoice.get('amount'))
    await transactions.deposit_to_user(callback.from_user.id, amount * rate)

    await callback.message.delete()
    await callback.message.answer(
        text=UserPaymentMessages.get_deposit_confirmed(),
        reply_markup=UserMenuKeyboards.get_main_menu(),
        parse_mode='HTML'
    )


# endregion Оплата Криптоботом


# endregion Handlers


def register_deposit_handlers(router: Router):
    # опция Пополнить
    router.callback_query.register(handle_deposit_callback, NavigationCallback.filter(
        (F.branch == 'profile') & (F.option == 'deposit')))

    # нажатие на метод пополнения
    router.callback_query.register(handle_show_deposit_method_callbacks, BalanceTransactionCallback.filter(
        (F.transaction_type == TransactionType.DEPOSIT) & ~F.currency))

    # Оплата КриптоБотом
    # нажатие на кнопку валюты
    router.callback_query.register(handle_cryptobot_deposit_currency_callback, BalanceTransactionCallback.filter(
        (F.transaction_type == TransactionType.DEPOSIT) & (F.method == PaymentMethod.CRYPTO_BOT) & F.currency
    ))
    # сообщение с суммой депозита для автоплатежа
    router.message.register(handle_auto_deposit_amount_message, UserStates.AutoDeposit.wait_for_amount)
    # проверка платежа в Крипто Боте
    router.callback_query.register(handle_check_cryptobot_payment, PaymentCheckCallback.filter(
        (F.method == PaymentMethod.CRYPTO_BOT)
    ))

    # Полуавтоматические методы
    router.message.register(handle_halfauto_deposit_amount_message,
                            UserStates.HalfAutoDeposit.wait_for_amount)
    # сообщение со скриншотом
    router.message.register(handle_halfauto_deposit_screen_message, UserStates.HalfAutoDeposit.wait_for_screen)
