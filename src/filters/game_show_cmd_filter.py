from aiogram.filters import BaseFilter
from aiogram.types import Message


class GameShowCmdFilter(BaseFilter):
    def __init__(self, start_target_symbol: str):
        self.target_symbol = start_target_symbol

    async def __call__(self, message: Message) -> bool:
        args = message.text.split()[1:]
        if args:
            return args[0].startswith(self.target_symbol)
        return False
