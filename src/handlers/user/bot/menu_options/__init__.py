from aiogram import Router

from .play import register_play_handlers
from .profile import register_profile_handlers
from .info import register_info_handlers
from .top_players import register_top_players_handlers


def register_menu_options_handlers(router: Router):
    register_play_handlers(router)
    register_profile_handlers(router)
    register_info_handlers(router)
    register_top_players_handlers(router)
