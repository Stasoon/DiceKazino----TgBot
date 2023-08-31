from aiogram import html

from src.database import transactions, User, get_referrals_count_of_user, get_total_games_count, get_total_users_count
from src.utils.texts import format_float_to_rub_string


class UserMenuMessages:
    @staticmethod
    def get_welcome(user_name: str = 'незнакомец') -> str:
        return f'''👋 Привет, {html.bold(user_name)}! '''

    @staticmethod
    def get_play_menu(user: User) -> str:
        return f'👤 Вы в игровом меню \n' \
               f'🪙 Баланс: {html.code(user.balance)}'

    @staticmethod
    async def get_referral_system(bot_username, user_id: int) -> str:
        return f'''
👥 Реферальная система \n
👤 Кол-во рефералов: {await get_referrals_count_of_user(user_id)}
💰 Заработано: {format_float_to_rub_string(await transactions.get_referral_earnings(user_id))} \n
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
        return f'{html.bold("🎖 10-ка лучших игроков")} \n\n{html.code("| Имя | Количество побед |")}'

    @staticmethod
    async def get_profile(user: User) -> str:
        return f'''
🌀 ID: {html.code(user.telegram_id)}
👤 Ник: {html.code(user.name)}
🪙 Баланс:  {format_float_to_rub_string(user.balance)}
🕑 Дата регистрации: {html.code(user.registration_date.strftime("%d/%m/%Y"))} \n
➕ Пополнил:  {format_float_to_rub_string(await transactions.get_user_all_deposits_sum(user))}
➖ Вывел:  {format_float_to_rub_string(await transactions.get_user_all_withdraws_sum(user))} '''
