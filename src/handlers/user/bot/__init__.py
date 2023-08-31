from aiogram import Router

from src.filters import ChatTypeFilter
from src.middlewares import ThrottlingMiddleware
from .start_command import register_start_command_handler
from .menu_options import register_menu_options_handlers
from .games_process import register_games_process_handlers


def register_bot_handlers(router: Router):
    # Фильтр, что сообщения в приватном чате
    router.message.filter(ChatTypeFilter('private'))
    router.callback_query.filter(ChatTypeFilter('private'))

    # Регистрация throttling middleware на сообщения и калбэки
    router.message.middleware(ThrottlingMiddleware())
    router.callback_query.middleware(ThrottlingMiddleware())

    # Регистрация команды /start
    register_start_command_handler(router)
    # Регистрация опций меню
    register_menu_options_handlers(router)
    # Регистрация игрового процесса
    register_games_process_handlers(router)
