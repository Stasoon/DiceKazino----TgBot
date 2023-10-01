from abc import ABC, abstractmethod

from aiogram import Router, Bot
from aiogram.types import CallbackQuery

from src.database import Game


class GameStrategy(ABC):

    @staticmethod
    @abstractmethod
    async def start_game(callback: CallbackQuery, game: Game):
        ...

    @staticmethod
    @abstractmethod
    async def finish_game(bot: Bot, game: Game):
        ...

    @classmethod
    @abstractmethod
    def register_moves_handlers(cls, router: Router):
        ...
