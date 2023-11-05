import asyncio

from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums.dice_emoji import DiceEmoji

from .logging import logger
from src.database.games import even_uneven
from src.database import transactions
from src.keyboards.user.games import EvenUnevenKeyboards
from src.misc.enums.games_enums import EvenUnevenCoefficients
from src.messages.user.games import EvenUnevenMessages


def get_formatted_time(seconds: int = 0):
    return f"{seconds // 60:02}:{seconds % 60:02}"


def get_won_bet_options(dice_values) -> str:
    """Возвращает строку с кодовыми названиями опций, которые победили исходя из значений на костях"""
    won_options = ''
    a, b = dice_values
    if a % 2 == 0 or b % 2 == 0:  # На чётное
        won_options += 'A'
    if a % 2 != 0 or b % 2 != 0:  # На
        won_options += 'B'
    if a > b:
        won_options += 'C'
    if a < b:
        won_options += 'D'
    if a % 2 == 0 and b % 2 == 0:
        won_options += 'E'
    if a % 2 != 0 or b % 2 != 0:
        won_options += 'F'
    if a == b:
        won_options += 'G'
    if a == 5 or b == 5:
        won_options += 'H'
    return won_options


class EvenUneven:
    def __init__(self, bot: Bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id

        self.__round_message_ids = []
        self.markup = None

    async def __timer(
            self,
            message_to_edit: Message,
            template: str,
            seconds: int = 300, delta_seconds: int = 10
    ):
        chat_id = message_to_edit.chat.id
        msg_id = message_to_edit.message_id
        while seconds > 0:
            await asyncio.sleep(delta_seconds)

            seconds -= delta_seconds
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=self.markup,
                text=template.format(get_formatted_time(seconds=seconds))
            )
        # Удаляем сообщение с таймером
        await self.bot.delete_message(chat_id=chat_id, message_id=msg_id)

    async def __accrue_winnings_and_notify_players(self, won_bet_options):
        player_bets = await even_uneven.get_players_bets()
        winnings_sum = 0

        for bet in player_bets:
            player_id = (await bet.player.get()).telegram_id
            await even_uneven.delete_player_bet(player_id=player_id)

            if bet.option in won_bet_options:
                win_amount = await transactions.accrue_winnings(
                    winner_telegram_id=player_id,
                    amount=bet.amount * EvenUnevenCoefficients.get(bet.option)
                )
                winnings_sum += win_amount
                text = f'Вы выиграли {win_amount}'
                logger.info(f'{player_id} {bet.amount} +++выигрыш {EvenUnevenCoefficients.get(bet.option)} {bet.option}')
            else:
                text = f'<b>🎲 Вы проиграли {bet.amount}₽</b>'
                logger.info(f'{player_id} {bet.amount} ---проигрыш {bet.option}')
            await self.bot.send_message(chat_id=player_id, text=text, parse_mode='HTML')

        return winnings_sum

    async def __send_round_start_and_start_timer(self, round_number: int):
        # seconds_to_wait = randint(5, 8) * 60 - 1
        seconds_to_wait = 40

        # Отправляем сообщение
        template = EvenUnevenMessages.get_timer_template(round_number=round_number)
        bot_username = (await self.bot.get_me()).username
        self.markup = EvenUnevenKeyboards.get_bet_options(round_number=round_number, bot_username=bot_username)

        msg = await self.bot.send_message(
            chat_id=self.chat_id,
            text=template.format(get_formatted_time(seconds_to_wait)),
            reply_markup=self.markup
        )
        await even_uneven.set_round_message(message_id=msg.message_id)

        # Запускаем таймер
        await self.__timer(
            message_to_edit=msg, template=template,
            seconds=seconds_to_wait
        )

    async def __send_dices_and_get_values(self) -> list[int, int]:
        self.__round_message_ids.append(
            (await self.bot.send_message(chat_id=self.chat_id, text='🎲 Бросаем кубики')).message_id
        )

        values = []
        for _ in range(2):
            dice_msg = await self.bot.send_dice(chat_id=self.chat_id, emoji=DiceEmoji.DICE)
            values.append(dice_msg.dice.value)
            self.__round_message_ids.append(dice_msg.message_id)

        self.__round_message_ids.append(
            (await self.bot.send_message(chat_id=self.chat_id, text='Выигрыши начислены')).message_id
        )
        return values

    async def process_round(self):
        # Создаём раунд
        current_round = await even_uneven.get_current_round()
        if current_round and current_round.message_id:
            try:
                await self.bot.delete_message(chat_id=self.chat_id, message_id=current_round.message_id)
            except Exception:
                pass
            round_number = current_round.number
        else:
            round_number = await even_uneven.create_round_and_get_number()

        await self.__send_round_start_and_start_timer(round_number)

        # Бросаем кости и получаем победившие ставки
        results = await self.__send_dices_and_get_values()
        won_bet_options = get_won_bet_options(results)

        await self.__accrue_winnings_and_notify_players(won_bet_options=won_bet_options)

    async def clear_round_messages(self):
        # Удаляем сообщения, присланные за раунд
        for msg_id in self.__round_message_ids:
            try:
                await self.bot.delete_message(chat_id=self.chat_id, message_id=msg_id)
            except TelegramBadRequest:
                continue


async def start_even_uneven_loop(bot: Bot, channel_id: int):
    while True:
        even_uneven_round = EvenUneven(bot=bot, chat_id=channel_id)

        try:
            await even_uneven_round.process_round()
        except Exception as e:
            logger.error(e)

        # Ждём, чтобы игроки увидели результаты
        seconds_btw_rounds = 40
        await asyncio.sleep(seconds_btw_rounds)

        await even_uneven_round.clear_round_messages()
