from aiogram.utils.keyboard import (InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton,
                                    ReplyKeyboardMarkup, InlineKeyboardBuilder)
from src.database import Game, games
from src.misc import (NavigationCallback, PaymentCheckCallback, TransactionType, BalanceTransactionCallback,
                      GamesCallback, PaymentMethod, ConfirmWithdrawRequisitesCallback)
from src.utils import cryptobot

invite_link = 'tg://msg_url?url=https://t.me/{bot_username}?start={user_tg_id}&text=Присоединяйся%20по%20моей%20ссылке'


def get_navigation_callback(branch: str, option: str = None) -> NavigationCallback:
    return NavigationCallback(branch=branch, option=option)


class PrivateKeyboards:
    # branch MAIN
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        menu_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🎰  Играть  🎰")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="ℹ Информация")]],
            resize_keyboard=True)
        return menu_kb

    @staticmethod
    def get_cancel_payment() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
            is_persistent=True
        )

    # branch PLAY
    @staticmethod
    def get_play_menu() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться после перехода в Играть"""
        builder = InlineKeyboardBuilder()

        builder.button(text='♠ BlackJack', callback_data=get_navigation_callback('play', 'blackjack'))
        builder.button(text='🎲 Games', callback_data=get_navigation_callback('play', 'games'))

        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    async def get_game_category(available_games: list[Game]) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться при нажатии на тип игры"""
        builder = InlineKeyboardBuilder()
        builder.button(text='➕ Создать', callback_data='create')
        builder.add(InlineKeyboardButton(text='♻ Обновить', callback_data='refresh_games'))

        for game in available_games[:8]:
            text = f'{game.type.value}#{game.number} | 💸{game.bet} | {(await games.get_players_of_game(game))[0].name}'
            builder.button(text=text, callback_data=GamesCallback(game_number=game.number, action='show')).row()

        builder.button(text='🔙 Назад', callback_data=get_navigation_callback('play'))
        builder.adjust(2, 1)
        return builder.as_markup()

    # branch PROFILE
    @staticmethod
    def get_profile() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться после перехода в Профиль"""
        builder = InlineKeyboardBuilder()

        builder.button(text='💳 Пополнить', callback_data=get_navigation_callback('profile', 'deposit'))
        builder.button(text='💰 Вывести', callback_data=get_navigation_callback('profile', 'withdraw'))
        builder.button(text='👥 Реферальная система', callback_data=get_navigation_callback('profile', 'referral_system'))

        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    def get_payment_methods(transaction_type: TransactionType) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру с методами пополнения"""
        builder = InlineKeyboardBuilder()
        back_builder = InlineKeyboardBuilder().button(text='🔙 Назад', callback_data=get_navigation_callback('profile'))

        builder.button(
            text='💳 СБП',
            callback_data=BalanceTransactionCallback(
                transaction_type=transaction_type, method=PaymentMethod.SBP
            )
        )
        builder.button(
            text='🤖 КриптоБот',
            callback_data=BalanceTransactionCallback(
                transaction_type=transaction_type, method=PaymentMethod.CRYPTO_BOT
            )
        )
        builder.button(
            text='💜 ЮMoney',
            callback_data=BalanceTransactionCallback(
                transaction_type=transaction_type, method=PaymentMethod.U_MONEY
            )
        )

        builder.adjust(2)
        return builder.attach(back_builder).as_markup()

    @staticmethod
    def get_confirm_withdraw_requisites() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text='✅ Отправить', callback_data=ConfirmWithdrawRequisitesCallback(requisites_correct=True))
        builder.button(text='✏ Изменить реквизиты', callback_data=ConfirmWithdrawRequisitesCallback(requisites_correct=False))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    async def get_cryptobot_choose_currency(transaction_type: TransactionType) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться после нажатия на метод оплаты Крипто Ботом"""
        currency_builder = InlineKeyboardBuilder()

        currencies = await cryptobot.get_currencies()
        for code in currencies:
            currency_builder.button(
                text=code, callback_data=BalanceTransactionCallback(
                transaction_type=transaction_type,
                method=PaymentMethod.CRYPTO_BOT, currency=code)
            )
        currency_builder.adjust(4)

        back_builder = InlineKeyboardBuilder()
        back_builder.button(text='🔙 Отмена', callback_data=NavigationCallback(branch='profile', option='deposit'))
        back_builder.adjust(1)

        currency_builder.attach(back_builder)
        return currency_builder.as_markup()

    @staticmethod
    def get_invoice(method: PaymentMethod, pay_url: str, invoice_id: int) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для оплаты и её проверки"""
        builder = InlineKeyboardBuilder()
        builder.button(text='Оплатить', url=pay_url)
        builder.button(text='Проверить', callback_data=PaymentCheckCallback(method=method, invoice_id=invoice_id))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_referral_system(bot_username: str, user_telegram_id: int) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться при переходе в Реферальную систему"""
        builder = InlineKeyboardBuilder()

        url = invite_link.format(bot_username=bot_username, user_tg_id=user_telegram_id)
        builder.button(text='📲 Пригласить друга', url=url)
        builder.button(text='🔙 Назад', callback_data=get_navigation_callback('profile'))
        builder.adjust(1)

        return builder.as_markup()

    # branch INFORMATION
    @staticmethod
    def get_information() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться при переходе во вкладку Информация"""
        builder = InlineKeyboardBuilder()
        builder.button(
            text='🔝 Топ-10 игроков 🔝',
            callback_data=NavigationCallback(branch='info', option='top_players')
        )

        builder.add(
            InlineKeyboardButton(text='💬 Чат', url='https://t.me/'),
            InlineKeyboardButton(text='📰 Новости', url='https://t.me/'),
            InlineKeyboardButton(text='📚 Правила', url='https://t.me/')
        )

        builder.adjust(1, 2, 1)
        return builder.as_markup()

    @staticmethod
    async def get_top_players() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, отображающую топ игроков с количеством их побед"""
        top_players = await games.get_top_players()
        builder = InlineKeyboardBuilder()
        for data in top_players:
            builder.button(
                text=f"🆔{data.get('telegram_id')} | 👤{data.get('name')} | 🏆 {data.get('winnings_count')}",
                url=f"tg://user?id={data.get('telegram_id')}"
            )
        builder.button(text='🔙 Назад', callback_data=get_navigation_callback('info'))
        builder.adjust(1)
        return builder.as_markup()


class PublicKeyboards:
    @staticmethod
    async def get_join_game(game: Game) -> InlineKeyboardMarkup | None:
        if len(await games.get_players_of_game(game)) == game.max_players:
            return None

        builder = InlineKeyboardBuilder()

        builder.button(
            text='✅ Присоединиться', callback_data=GamesCallback(action='join', game_number=game.number)
        )

        builder.adjust(1)
        return builder.as_markup()
