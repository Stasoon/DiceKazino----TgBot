from src.database import get_top_winners_by_amount
from src.misc import GameCategory


class HitOrMissMessages:
    @staticmethod
    def get_timer_template(round_number: int) -> str:
        return f'🎲 Раунд #{round_number} \n' + \
               '⏱ {} \n♻ Ожидание ставок...'

    @staticmethod
    async def get_top() -> str:
        top_players = await get_top_winners_by_amount(category=GameCategory.EVEN_UNEVEN, days_back=7, limit=6)
        text = 'Топ кабедителей: \n\n'
        for n, player in enumerate(top_players, start=1):
            text += f'{n}. - {str(player)} : {player.winnings_amount}\n'
        return text
