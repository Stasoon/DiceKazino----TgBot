import html
from decimal import Decimal

from settings import Config
from src.database.models import Band, User
from src.misc.enums.leagues import BandLeague
from src.utils.text_utils import format_float_to_rub_string


def get_member_link(member: User):
    if member.telegram_id:
        return f"<a href='tg://user?id={member.telegram_id}'>{html.escape(member.name)}</a>"
    else:
        return html.escape(member.name)


class BandsMessages:

    @staticmethod
    def get_bands_menu() -> str:
        return 'Меню банд'

    @staticmethod
    def get_league_name(league: BandLeague) -> str:
        match league:
            case BandLeague.CROOKS:
                return 'Жулики'
            case BandLeague.GAMBLERS:
                return 'Картёжники'
            case BandLeague.CARD_MASTERS:
                return 'Мастера карт'
            case BandLeague.BUSINESSMEN:
                return 'Бизнесмены'
            case BandLeague.INDUSTRIALISTS:
                return 'Промышленники'
            case BandLeague.TYCOONS:
                return 'Магнаты'
            case BandLeague.MONOPOLISTS:
                return 'Монополисты'

    @classmethod
    def get_band_description(cls, band: Band, band_creator: User, members_scores: list[tuple[User, float | Decimal]]) -> str:
        members_text = f'🫂 Участники: ({len(members_scores)}/{Config.Bands.BAND_MEMBERS_LIMIT})'
        members_list = "\n".join(
            f"{n}) {member[0]} — {format_float_to_rub_string(member[1])}"
            for n, member in enumerate(members_scores, start=1)
        )

        return (
            f'<b>Банда "{band.title}"</b> \n\n'
            f'👑 Главарь: {band_creator} \n'
            f'📈 Ранг: {cls.get_league_name(band.league)} \n'
            f'💰 Общак: {format_float_to_rub_string(band.score)} \n\n'
            f'{members_text} \n{members_list}'
        )

    @classmethod
    def get_ask_for_join_band(cls, band: Band, band_creator: User, band_members: list[User]) -> str:
        band_description = cls.get_band_description(band=band, band_creator=band_creator, band_members=band_members)
        return f'Хотите ли вы вступить в эту банду? \n\n{band_description}'

    @staticmethod
    def ask_for_member_to_kick() -> str:
        return 'Нажмите на пользователя, которого хотите исключить:'
