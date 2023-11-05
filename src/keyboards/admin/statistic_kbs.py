from aiogram.utils.keyboard import KeyboardButton

from .admin_keyboards import AdminKeyboardBase


class StatisticsKbs(AdminKeyboardBase):
    @staticmethod
    def get_button_for_admin_menu() -> KeyboardButton:
        return KeyboardButton(text='📊 Статистика 📊')

    @staticmethod
    def get_():
        return 
