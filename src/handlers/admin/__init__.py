from aiogram import Dispatcher, Router

from src.filters import IsAdminFilter
from .admin_menu import register_admin_menu_handlers
from .mailing import register_mailing_handlers
from .payments_validation import register_validate_request_handlers
from .statistics import register_statistics_handlers
from .commands import register_commands_handlers


def register_admin_handlers(router: Dispatcher | Router):
    IsAdminFilter(True)

    register_admin_menu_handlers(router)
    register_mailing_handlers(router)
    register_validate_request_handlers(router)
    register_statistics_handlers(router)
    register_commands_handlers(router)
