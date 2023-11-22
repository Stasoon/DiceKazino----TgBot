from typing import Literal

from ..models import EvenUnevenPlayerBet


async def add_player_bet(player_id: int, amount: float, option: Literal['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']):
    await EvenUnevenPlayerBet.create(player_id=player_id, amount=amount, option=option)


async def delete_player_bet(player_id: int):
    await EvenUnevenPlayerBet.filter(player_id=player_id).delete()


async def get_players_bets() -> list[EvenUnevenPlayerBet]:
    return await EvenUnevenPlayerBet.all()
