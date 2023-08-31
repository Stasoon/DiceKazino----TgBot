from aiogram import html

from src.utils.texts import format_float_to_rub_string
from src.misc import PaymentMethod


class UserPaymentMessages:
    @staticmethod
    def get_choose_deposit_method() -> str:
        return html.bold('💎 Выберите способ пополнения баланса:')

    @staticmethod
    def get_choose_withdraw_method() -> str:
        return html.bold('💎 Выберите способ вывода средств с баланса:')

    @staticmethod
    def get_confirm_withdraw_requisites() -> str:
        return '💎 Отправить заявку на вывод?'

    @staticmethod
    def choose_currency() -> str:
        return html.bold('💎 Выберите валюту:')

    @staticmethod
    def enter_deposit_amount(min_deposit_amount) -> str:
        return html.bold(f"💎 Введите, сколько рублей вы хотите внести: \n") + \
               f"(Минимальный депозит - {format_float_to_rub_string(min_deposit_amount)})"

    @staticmethod
    def enter_withdraw_amount(min_withdraw_amount) -> str:
        return html.bold("💎 Введите, сколько рублей вы хотите вывести с баланса: \n") + \
               f"(Минимальная сумма вывода - {format_float_to_rub_string(min_withdraw_amount)})"

    @staticmethod
    def enter_user_withdraw_requisites(withdraw_method: PaymentMethod) -> str:
        """Возвращает строку с просьбой ввести реквизиты пользователя, на которые нужно переводить деньги,
        в зависимости от метода"""
        necessary_requisites = None

        if withdraw_method == PaymentMethod.SBP:
            necessary_requisites = f"💳 Введите {html.bold('название банка')} и {html.bold('номер телефона/карты')}:"
        elif withdraw_method == PaymentMethod.U_MONEY:
            necessary_requisites = f"💳 Введите ваш {html.bold('номер кошелька ЮMoney')}:"
        return necessary_requisites

    @staticmethod
    def get_half_auto_deposit_method_requisites(deposit_method: PaymentMethod):
        """Возвращает реквизиты владельца в зависимости от метода"""
        requisites = ''

        if deposit_method == PaymentMethod.SBP:
            requisites = "📩 Отправьте деньги по СБП по реквизитам: \n" \
                         f"💳 По номеру: \n{html.code('+7 (978) 212-83-15')}"
        elif deposit_method == PaymentMethod.U_MONEY:
            requisites = "📩 Отправьте деньги на ЮMoney по реквизитам: \n" \
                         f"💳 По номеру счёта: \n{html.code('5599002035793779')}"

        requisites += '\n\n📷 Отправьте боту скриншот чека:'
        return requisites

    @staticmethod
    def get_deposit_link_message() -> str:
        return "🔗 Вот ссылка на пополнение:"

    @staticmethod
    def get_deposit_confirmed() -> str:
        return '✅ Готово! Сумма начислена на ваш баланс.'

    @staticmethod
    def get_wait_for_administration_confirm() -> str:
        return '✅ Заявка создана \n\n⏰ Ожидайте рассмотрения...'
