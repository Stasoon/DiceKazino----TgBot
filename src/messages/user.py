from aiogram import html

from src.database import (transactions, games, User, Game, PlayerMove, get_referrals_count_of_user,
                          get_total_games_count, get_total_users_count, get_user_or_none)
from src.misc import PaymentMethod


def format_float(value: float) -> str:
    return f"{value:.2f}"


def format_balance(balance: float, use_html: bool = True) -> str:
    balance_text = f"{ format_float(balance) } ₽"
    return html.code(balance_text) if use_html else balance_text


class UserMessages:
    # region Utils
    @classmethod
    def get_game_header(cls, game: Game):
        return f"Игра {game.type.value} №{game.number}"

    @classmethod
    async def get_players_results(cls, game_moves: list[PlayerMove]) -> str:
        strings = []

        for move in game_moves:
            strings.append(f"{str(await move.player.get())} - [{move.value}]")

        return '\n'.join(strings)

    @staticmethod
    async def get_game_participants(game: Game):
        player_strings = []
        number_emojis = ['1️⃣', '2️⃣', '3️⃣']
        players = await games.get_players_of_game(game)
        players = [*players, *(None,) * (game.max_players-len(players))]

        for emoji, player in zip(number_emojis, players):
            text = str(player) if player else 'Ожидание...'
            player_strings.append(f"{emoji} - {text}")

        return '\n'.join(player_strings)

    # endregion

    # region Private

    @staticmethod
    def get_welcome(user_name: str = 'незнакомец') -> str:
        return f'''👋 Привет, {html.bold(user_name)}! '''

    @staticmethod
    def get_play_menu(user: User) -> str:
        return f'''👤 Вы в игровом меню \n
🪙 Баланс: {html.code(user.balance)}'''

    @staticmethod
    async def get_referral_system(bot_username, user_id: int) -> str:
        return f'''
👥 Реферальная система \n
👤 Кол-во рефералов: {await get_referrals_count_of_user(user_id)}
💰 Заработано: {format_balance(await transactions.get_referral_earnings(user_id))} \n
— За каждую победу Вашего реферала - Вы будете получать 0.5%
— Вывод заработанных денег возможен от 300 ₽ \n
🔗 Ваша партнёрская ссылка:
http://t.me/{bot_username}?start={user_id}'''

    @staticmethod
    async def get_information() -> str:
        return f'''
📜 Информация о боте: \n
👥 Всего пользователей: {await get_total_users_count()} \n
♻ Всего сыграно игр: {await get_total_games_count()} \n
👤 Администрация:
┣ @stascsa
┗ @stascsa'''

    @staticmethod
    def get_top_players() -> str:
        return '🎖 10-ка лучших игроков \n\nID | Имя | Количество побед'

    @staticmethod
    async def get_profile(user: User) -> str:
        return f'''
🌀 ID: {html.code(user.telegram_id)}
👤 Ник: {html.code(user.name)}
🪙 Баланс:  {format_balance(user.balance)}
🕑 Дата регистрации: {html.code(user.registration_date.strftime("%d/%m/%Y"))} \n
➕ Пополнил:  {format_balance(await transactions.get_user_all_deposits_sum(user))}
➖ Вывел:  {format_balance(await transactions.get_user_all_withdraws_sum(user))} '''

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
               f"(Минимальный депозит - {format_balance(min_deposit_amount)})"

    @staticmethod
    def enter_withdraw_amount(min_withdraw_amount) -> str:
        return html.bold("💎 Введите, сколько рублей вы хотите вывести с баланса: \n") + \
               f"(Минимальная сумма вывода - {format_balance(min_withdraw_amount)})"

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

    # endregion

    @classmethod
    async def get_game_in_chat(cls, game: Game) -> str:
        header = cls.get_game_header(game)
        players_text = f"👥 Игроки: \n{await UserMessages.get_game_participants(game)}"
        bet_text = f"💰 Ставка: {game.bet} ₽"

        result = f"{header} \n\n{players_text} \n\n{bet_text} \n\n"

        if await games.is_game_full(game):
            result += f"Отправьте  {html.code(f'{game.type.value}')}  в ответ на это сообщение:"
        else:
            result += f"🚪 Количество свободных мест: {len(await games.get_player_ids_of_game(game))}/{game.max_players} чел."

        return result

    @classmethod
    async def get_game_in_chat_finish(cls, game: Game, winner_id: int | None, game_moves: list[PlayerMove],
                                      win_amount: float):
        # Получаем заголовок игры
        header = cls.get_game_header(game)

        # Получаем результаты игры
        results = await cls.get_players_results(game_moves)

        # Формируем сообщение о победителе и выигрыше
        if winner_id:
            winner_text = f'💰 Выигрыш: {format_balance(win_amount)}\n' \
                          f'🏆 Победитель: {await get_user_or_none(telegram_id=winner_id)}'
        else:
            winner_text = '⚡⚡⚡ Ничья ⚡⚡⚡ \n♻ Возвращаю ставки'

        # Собираем сообщение
        return f"{header}\n\n{results}\n\n{winner_text}"

    # region MiniGames

    @classmethod
    async def get_mini_game_loose(cls, game: Game) -> str:
        creator = await games.get_creator_of_game(game)
        return f'''👤 {str(creator)}
😞 Вы проиграли {format_balance(game.bet)}
🍀 Возможно, в следующий раз повезёт'''

    @classmethod
    async def get_mini_game_victory(cls, game: Game, win_amount: float):
        creator = await games.get_creator_of_game(game)
        return f'''👤 {str(creator)}
🎉 Вы выиграли!
➕ Сумма выигрыша: {format_balance(win_amount)}'''


class ExceptionMessages:
    @staticmethod
    def get_too_many_requests() -> str:
        return '🙏 Пожалуйста, нажимайте не так часто'

    @staticmethod
    def get_not_registered_in_bot() -> str:
        return f'❗Чтобы играть в чате, сначала зайдите в нашего бота'

    @staticmethod
    def get_payment_error() -> str:
        return 'Что-то пошло не так❗ \nПросим прощения. Воспользуйтесь другим способом или обратитесь в поддержку'

    @staticmethod
    def get_payment_not_found() -> str:
        return '❗Платёж не найден'

    @staticmethod
    def get_message_text_too_long() -> str:
        return '❗Текст сообщения слишком длинный. \nПопробуйте снова:'

    @staticmethod
    def get_message_text_too_short() -> str:
        return '❗Текст сообщения слишком короткий. \nПопробуйте снова:'

    @staticmethod
    def get_insufficient_transaction_amount(min_transaction_amount: float) -> str:
        """Сумма транзакции меньше минимальной"""
        return f'❗Минимальная сумма транзакции - {format_balance(min_transaction_amount)}. \n' \
               f'Попробуйте ещё раз:'

    @staticmethod
    def get_insufficient_balance(balance: float):
        """На балансе всего <сумма>. Введите другую сумму"""
        return f'❗На вашем балансе всего {format_balance(balance)}. \nВведите другую сумму:'

    @staticmethod
    def get_photo_expected() -> str:
        return '❗Это не фотография. \nОтправьте боту скриншот оплаты:'

    @staticmethod
    def get_text_expected() -> str:
        return '❗Это не текст. \nПопробуйте снова:'

    @staticmethod
    def get_invalid_number_message():
        return '❗Вы ввели не число. \nПопробуйте ещё раз:'

    @staticmethod
    def get_low_balance() -> str:
        return '❌ Недостаточный баланс!'

    @staticmethod
    def get_already_in_game() -> str:
        return '❗Вы уже участвуете в этой игре'

    @staticmethod
    def get_already_in_other_game(game: Game) -> str:
        return f'❗Вы уже участвуете в {game.type.value}№{game.number}'

    @staticmethod
    def get_bet_too_low(min_bet: int) -> str:
        return f'❗Минимальная ставка в этой игре - {format_balance(min_bet, use_html=False)}'

    @staticmethod
    def get_invalid_argument_count(must_be_count: int) -> str:
        return f'❗В команде должно быть {must_be_count} параметра.'

    @staticmethod
    def get_another_game_not_finished(user_active_game: Game) -> str:
        return f'❗Чтобы начать игру, завершите {UserMessages.get_game_header(game=user_active_game)}'

    @staticmethod
    def get_arguments_have_invalid_types() -> str:
        return '❗Аргументами команды должны быть числа!'

    @staticmethod
    def low_balance_for_withdraw(min_withdraw_amount: float):
        return f'⛔Минимальная сумма вывода - {format_balance(min_withdraw_amount, use_html=False)}'
