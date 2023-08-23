from aiogram.filters import BaseFilter
from aiogram.types import Message


class MessageIsForward(BaseFilter):
    def __init__(self, should_be_forward: bool = True):
        self.should_be_forward = should_be_forward

    async def __call__(self, message: Message, *args, **kwargs) -> bool:
        flag = bool(message.reply_to_message)
        return flag is self.should_be_forward
