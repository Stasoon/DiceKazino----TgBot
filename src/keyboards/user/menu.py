from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import (InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton,
                                    ReplyKeyboardMarkup, InlineKeyboardBuilder)

from src.misc import MenuNavigationCallback

invite_link = 'tg://msg_url?url=https://t.me/{bot_username}?start={user_tg_id}&text=Присоединяйся%20по%20моей%20ссылке'


class UserMenuKeyboards:
    # branch MAIN
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        menu_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🎰  Играть  🎰")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🔝 Топ игроков")],
            [KeyboardButton(text="📰 События"), KeyboardButton(text="ℹ Информация")],
            ],
            resize_keyboard=True, input_field_placeholder=None)
        return menu_kb

    # Events
    @staticmethod
    def get_events():
        builder = InlineKeyboardBuilder()

        builder.button(text='📆 История и планы 📆', web_app=WebAppInfo(url='https://mj6290.craftum.io/spotdiceroadmap'))
        builder.button(text='⚽ Турнир "Бутс"', url='https://t.me/SpotDiceN/24')
        builder.button(text='🎴 Турнир "Козырь"', url='https://t.me/SpotDiceN/24')

        return builder.adjust(1).as_markup()

    # branch PROFILE
    @staticmethod
    def get_profile() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться после перехода в Профиль"""
        builder = InlineKeyboardBuilder()

        builder.button(text='💳 Пополнить', callback_data=MenuNavigationCallback(branch='profile', option='deposit'))
        builder.button(text='💰 Вывести', callback_data=MenuNavigationCallback(branch='profile', option='withdraw'))
        builder.button(text='👥 Реферальная система',
                       callback_data=MenuNavigationCallback(branch='profile', option='referral_system'))

        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    def get_referral_system(bot_username: str, user_telegram_id: int) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться при переходе в Реферальную систему"""
        builder = InlineKeyboardBuilder()

        url = invite_link.format(bot_username=bot_username, user_tg_id=user_telegram_id)
        builder.button(text='📲 Пригласить друга', url=url)
        builder.button(text='🔙 Назад', callback_data=MenuNavigationCallback(branch='profile'))
        builder.adjust(1)

        return builder.as_markup()

    # branch INFORMATION
    @staticmethod
    def get_information() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться при переходе во вкладку Информация"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(text='💬 Чат', url='https://t.me/'),
            InlineKeyboardButton(text='📰 Новости', url='https://t.me/'),
            InlineKeyboardButton(text='📚 Правила', url='https://t.me/')
        )

        builder.adjust(1, 2, 1)
        return builder.as_markup()




