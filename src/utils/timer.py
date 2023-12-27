import asyncio
from abc import ABC, abstractmethod

from src.database.models import Timer


class BaseTimer(ABC):
    def __init__(
            self, chat_id: int, step: int = 5,
    ):
        self.step = step

        self.chat_id = chat_id
        self.timer = None
        self.timer_id = None

    async def setup_timer(self, seconds_expiry: int, message_id: int):
        old_timer = await Timer.get_or_none(chat_id=self.chat_id)
        if old_timer:
            await old_timer.delete()

        self.timer = await Timer.create(chat_id=self.chat_id, timer_expiry=seconds_expiry, message_id=message_id)
        self.timer_id = self.timer.unique_id

    async def start_timer(self):
        while True:
            if not self.timer:
                return

            await asyncio.sleep(self.step)
            await self.make_tick()

            if self.timer.timer_expiry <= 0:
                break

        await self.on_time_left()

    @abstractmethod
    async def make_tick(self):
        self.timer.timer_expiry -= self.step
        await self.timer.save()

    @abstractmethod
    async def on_time_left(self):
        await self.timer.delete()

    @staticmethod
    def format_seconds_to_time(seconds: int) -> str:
        res = []

        while seconds > 0:
            res.append(f"{seconds % 60:02}")
            seconds //= 60

        if len(res) < 2:
            res.append("00")

        return ':'.join(res[::-1])

    def __str__(self) -> str:
        if not self.timer:
            return ''

        return self.format_seconds_to_time(self.timer.timer_expiry)
