from aiogram import Router

from .join_game import register_join_game_handlers
from .basic_games import register_basic_games_handlers
from .baccarat import register_baccarat_game_handlers


def register_games_process_handlers(router: Router):
    register_join_game_handlers(router)
    register_basic_games_handlers(router)
    register_baccarat_game_handlers(router)
