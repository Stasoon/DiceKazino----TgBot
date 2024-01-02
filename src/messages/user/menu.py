from aiogram import html

from src.database import transactions, User, users, get_total_games_count, get_total_users_count, bands
from src.database.transactions import referral_bonuses
from src.utils.text_utils import format_float_to_rub_string
from settings import Config


class UserMenuMessages:
    @staticmethod
    def get_welcome(user_name: str = 'незнакомец') -> str:
        return f"👋 Привет, {html.bold(html.quote(user_name))}!"

    @staticmethod
    def get_play_menu(user: User) -> str:
        balance_str = html.code(format_float_to_rub_string(user.balance))
        return f'👤 Вы в игровом меню \n🪙 Баланс: {balance_str}'

    @staticmethod
    def get_events() -> str:
        return '📰 Наши события'

    @staticmethod
    async def get_referral_system(bot_username: str, user_id: int) -> str:
        percent_to_referrer = await referral_bonuses.calculate_referral_bonus_percent(user_id=user_id)
        user_referrals_count = await users.get_referrals_count_by_telegram_id(user_id)
        earned_amount = format_float_to_rub_string(await transactions.get_referral_earnings(user_id))

        return (
            f'👥 Реферальная система \n\n'
            f'👤 Кол-во рефералов: {user_referrals_count} \n'
            f'💰 Заработано: {earned_amount} \n\n'
            f'— За каждую победу Вашего реферала - Вы будете получать {percent_to_referrer * 100}% \n'
            f'— Вывод заработанных денег возможен от 300 ₽ \n\n'
            f'🔗 Ваша партнёрская ссылка: \n<code>https://t.me/{bot_username}?start=ref{user_id}</code>'
        )

    @staticmethod
    async def get_information() -> str:
        return (
            f'📜 Информация о боте: \n\n'
            f'👥 Всего пользователей: {await get_total_users_count()} \n'
            f'♻ Всего сыграно игр: {await get_total_games_count()} \n\n'
            f'👤 Администрация: \n'
            f'┣ @neverovmatvey \n'
            f'┗ @stascsa \n'
        )

    @staticmethod
    def get_top_players() -> str:
        return f'{html.bold("🎖 10-ка лучших игроков")} \n\n{html.code("Имя  |  Количество побед")}'

    @staticmethod
    async def get_profile(user: User) -> str:
        user_band = await bands.get_user_band(telegram_id=user.telegram_id)
        band_text = '' if not user_band else f'🫂 Банда: <code>{user_band.title}</code> \n'

        return (
            f'🌀 ID: {html.code(user.telegram_id)} \n'
            f'👤 Ник: {html.code(html.quote(user.name))} \n'
            f'{band_text}'
            f'🪙 Баланс:  {format_float_to_rub_string(user.balance)} \n'
            f'🕑 Дата регистрации: {html.code(user.registration_date.strftime("%d/%m/%Y"))} \n\n'
            f'➕ Пополнил:  {format_float_to_rub_string(await transactions.get_user_all_deposits_sum(user))} \n'
            f'➖ Вывел:  {format_float_to_rub_string(await transactions.get_user_all_withdraws_sum(user))} \n'
        )
