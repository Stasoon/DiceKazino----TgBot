from typing import Tuple

from PIL import Image, ImageDraw, ImageFont
from aiogram.types import BufferedInputFile

from src.database import Game, games
from ...database.games import playing_cards
from .base_painter import _GameImagePainter


class BlackJackImagePainter(_GameImagePainter):
    def __init__(self, game: Game):
        super().__init__(game)
        self.card_size = (160, 257)

        self.table: Image = None
        self.table_size: Tuple[int, int] = (0, 0)
        self.draw: ImageDraw = None

        self.points_font = ImageFont.truetype("font.otf", 45, encoding='UTF-8')

        self.cards_x_offset = 80

    async def __draw_banker_cards_and_points(self, show_cards: False):
        banker_points = await playing_cards.count_dealer_score(self.game.number)
        banker_cards = await playing_cards.get_dealer_cards(self.game.number)
        banker_points_text = banker_points if show_cards else f'? + {banker_points - banker_cards[0].points}'

        # Рисуем текст дилера
        self.draw.text(
            xy=(self.table_size[0] // 2, self.table_size[1] // 2 + 80),
            text=f"Банкир: {banker_points_text}",
            fill=(255, 255, 0, 230),
            font=self.points_font,
            align='center',
            anchor='mm'
        )

        # рисуем карты дилера
        cards_count = len(banker_cards)
        cards_start_x = (self.table_size[0] - self.card_size[0] - self.cards_x_offset * (cards_count - 1)) // 2
        cards_y = 200

        for n, card in enumerate(banker_cards, start=0):
            card_file_name = f"{card.value}{card.suit}" if n != 0 or show_cards else 'back'
            card_pos = (cards_start_x + n * self.cards_x_offset, cards_y)
            await self._draw_card(card_file_name, xy=card_pos)

    async def __draw_player_points(self, player_id: int, player_name: str, points_xy: tuple[int, int]) -> None:
        points = await playing_cards.count_player_score(game_number=self.game.number, player_id=player_id)

        # рисуем очки игрока
        self.draw.text(
            xy=points_xy,
            text=f'{player_name}: {points}',
            font=self.points_font,
            fill=(255, 255, 0, 230),
            align='center',
            anchor='mm'
        )

    async def __draw_first_player_cards(self, player_id: int, cards_start_xy) -> None:
        player_cards = await playing_cards.get_player_cards(
            game_number=self.game.number, player_id=player_id
        )

        for card_num, card in enumerate(player_cards):
            card_file_name = f'{card.value}{card.suit}'
            card_pos = (cards_start_xy[0] - self.card_size[0] // 8 * len(player_cards) + self.cards_x_offset * card_num,
                        cards_start_xy[1])
            await self._draw_card(card_file_name=card_file_name, xy=card_pos)

    async def __draw_second_player_cards(self, player_id: int, cards_start_xy) -> None:
        player_cards = await playing_cards.get_player_cards(
            game_number=self.game.number, player_id=player_id
        )

        for card_num, card in enumerate(player_cards):
            card_file_name = f'{card.value}{card.suit}'
            card_pos = (cards_start_xy[0] + self.card_size[0] // 8 * len(player_cards) - self.cards_x_offset * card_num,
                        cards_start_xy[1])
            await self._draw_card(card_file_name=card_file_name, xy=card_pos)

    async def get_image(self, is_finish: bool = False) -> BufferedInputFile:
        with Image.open('cards/clear_table.png') as table:
            self.table = table
            self.table_size = table.size
            self.draw = ImageDraw.Draw(table)

            # рисуем заголовок
            self._draw_header(game_name='BlackJack')

            # получаем игроков (сортировка, чтобы игроки всегда были в одном порядке)
            players = sorted(await games.get_players_of_game(game=self.game), key=lambda user: user.telegram_id)

            # рисуем очки игроков
            await self.__draw_player_points(player_id=players[0].telegram_id,
                                            player_name=players[0].name,
                                            points_xy=(150, 415))
            await self.__draw_player_points(player_id=players[1].telegram_id,
                                            player_name=players[1].name,
                                            points_xy=(self.table_size[0] - 150, 420))

            # рисуем карты игроков
            middle_x = (self.table_size[0] - self.card_size[0]) // 2
            middle_y = (self.table_size[1] - self.card_size[1]) // 2
            players_cards_start_y = middle_y + int(middle_y // 1.5)
            await self.__draw_first_player_cards(
                player_id=players[0].telegram_id,
                cards_start_xy=(int(middle_x / 6), players_cards_start_y),
            )
            await self.__draw_second_player_cards(
                player_id=players[1].telegram_id,
                cards_start_xy=(middle_x + int(middle_x / 1.2), players_cards_start_y)
            )
            # рисуем карты и очки банкира
            await self.__draw_banker_cards_and_points(show_cards=is_finish)

            # Сохраняем в буфер готовое фото и возвращаем
            return self._get_buffered_file_from_generated_photo()
