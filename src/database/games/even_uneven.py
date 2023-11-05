from typing import Literal

from ..models import EvenUnevenRound, EvenUnevenPlayerBet


async def get_current_round() -> EvenUnevenRound | None:
    return await EvenUnevenRound.all().first()


async def create_round_and_get_number() -> int:
    await EvenUnevenRound.all().delete()
    created_round = await EvenUnevenRound.create()
    return created_round.number


async def set_round_message(message_id: int) -> None:
    current_round = await EvenUnevenRound.all().first()
    current_round.message_id = message_id
    await current_round.save()


async def add_player_bet(player_id: int, amount: float, option: Literal['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']):
    await EvenUnevenPlayerBet.create(player_id=player_id, amount=amount, option=option)


async def delete_player_bet(player_id: int):
    await EvenUnevenPlayerBet.filter(player_id=player_id).delete()


async def get_players_bets() -> list[EvenUnevenPlayerBet]:
    return await EvenUnevenPlayerBet.all()
