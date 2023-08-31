from aiogram.utils.keyboard import (InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton,
                                    ReplyKeyboardMarkup, InlineKeyboardBuilder)

from src.misc import NavigationCallback

invite_link = 'tg://msg_url?url=https://t.me/{bot_username}?start={user_tg_id}&text=Присоединяйся%20по%20моей%20ссылке'


class UserMenuKeyboards:
    # branch MAIN
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        menu_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🎰  Играть  🎰")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💵 Кошелёк")],
            [KeyboardButton(text="🔝 Топ игроков"), KeyboardButton(text="ℹ Информация")],
            ],
            resize_keyboard=True)
        return menu_kb

    # branch PROFILE
    @staticmethod
    def get_profile() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться после перехода в Профиль"""
        builder = InlineKeyboardBuilder()

        builder.button(text='💳 Пополнить', callback_data=NavigationCallback(branch='profile', option='deposit'))
        builder.button(text='💰 Вывести', callback_data=NavigationCallback(branch='profile', option='withdraw'))
        builder.button(text='👥 Реферальная система',
                       callback_data=NavigationCallback(branch='profile', option='referral_system'))

        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    def get_referral_system(bot_username: str, user_telegram_id: int) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру, которая должна отображаться при переходе в Реферальную систему"""
        builder = InlineKeyboardBuilder()

        url = invite_link.format(bot_username=bot_username, user_tg_id=user_telegram_id)
        builder.button(text='📲 Пригласить друга', url=url)
        builder.button(text='🔙 Назад', callback_data=NavigationCallback(branch='profile'))
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




