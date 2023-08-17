from aiogram import html

from src.database import User, Game, PlayerMove, users
from src.database import games
from settings import Config


class Messages:
    # region Utils
    @classmethod
    async def __get_game_header(cls, game: Game):
        return f"{game.type.value} №{game.number}"

    @classmethod
    async def __get_players_results(cls, game_moves: list[PlayerMove]) -> str:
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
    async def get_welcome(user_name: str = 'незнакомец') -> str:
        return f'''👋 Привет, {html.bold(user_name)}! '''

    @staticmethod
    async def get_play_menu(user: User) -> str:
        return f'''👤 Вы в игровом меню \n
🪙 Баланс: {html.code(user.balance)}'''

    @staticmethod
    async def get_referral_system(bot_username, user_telegram_id: int, referrals_count: int) -> str:
        return f'''
👥 Реферальная система \n
👤 Кол-во рефералов: {referrals_count}
💰 Заработано: !!! ₽ \n
— За каждую победу Вашего реферала - Вы будете получать 0.5%
— Вывод заработанных денег возможен от 300 ₽ \n
🔗 Ваша партнёрская ссылка:
http://t.me/{bot_username}?start={user_telegram_id}'''

    @staticmethod
    async def get_information(total_users_count: int, total_games_count: int) -> str:
        return f'''
📜 Информация о боте: \n
👥 Всего пользователей: {total_users_count} \n
♻ Всего сыграно игр: {total_games_count} \n
👤 Администрация:
┣ @stascsa
┗ @stascsa'''

    @staticmethod
    async def get_user_profile(user: User) -> str:
        return f'''
🌀 ID: {html.code(user.telegram_id)}
👤 Ник: {html.code(user.name)}
🪙 Баланс: {html.code(user.balance)}
🕑 Дата регистрации: {html.code(user.registration_date.strftime("%d/%m/%Y"))} \n
➕ Пополнил: !!!
➖ Вывел: !!!'''

    # endregion

    @classmethod
    async def get_game_in_chat(cls, game: Game, game_title: str = 'Игра') -> str:
        header = await cls.__get_game_header(game)
        players_text = f"👥 Игроки: \n{await Messages.get_game_participants(game)}"
        bet_text = f"💰 Ставка: {game.bet} ₽"

        result = f"{header} \n\n{players_text} \n\n{bet_text} \n\n"

        if await games.is_game_full(game):
            result += f"Отправьте  {html.code(f'{game.type.value}')}  в ответ на это сообщение:"
        else:
            result += f"🚪 Количество свободных мест: {len(await games.get_player_ids(game))}/{game.max_players} чел."

        return result

    @classmethod
    async def get_game_in_chat_finish(cls, game: Game, winner_id: int | None, game_moves: list[PlayerMove], win_amount: float):
        header = f'{await cls.__get_game_header(game)}'
        results = f'Результаты: \n{await cls.__get_players_results(game_moves)}'

        winner_text = '🏆 Победитель: {} \n💰 Выигрыш: {} ₽'
        draw = f'⚡⚡⚡ Ничья ⚡⚡⚡ \n♻ Возвращаю ставки'

        return f"{header} \n\n{results} \n\n" \
               f"{winner_text.format(await users.get_user_obj(telegram_id=winner_id), win_amount) if winner_id else draw}"

    # region MiniGames

    @classmethod
    async def get_mini_game_loose(cls, game: Game) -> str:
        creator = await games.get_creator_of_game(game)
        return f'''👤 {str(creator)}
😞 Вы проиграли {game.bet} ₽
🍀 Возможно, в следующий раз повезёт'''

    @classmethod
    async def get_mini_game_victory(cls, game: Game, win_amount: float):
        creator = await games.get_creator_of_game(game)
        return f'''👤 {str(creator)}
🎉 Вы выиграли!
➕ Сумма выигрыша: {html.code(f'{win_amount} ₽')}'''

    class Exceptions:
        @staticmethod
        async def get_low_balance() -> str:
            return '❌ Недостаточный баланс!'

        @staticmethod
        async def get_already_in_game() -> str:
            return '❗Вы уже участвуете'

        @staticmethod
        async def get_invalid_argument_count(must_be_count: int) -> str:
            return f'В команде должно быть {must_be_count} аргументов'

        @staticmethod
        async def get_another_game_not_finished(user_active_game: Game) -> str:
            return f'Чтобы начать игру, завершите игру {user_active_game.type.value} №{user_active_game.number}'

        @staticmethod
        async def get_arguments_have_invalid_types() -> str:
            return 'Аргументами команды должны быть числа!'

    # endregion
