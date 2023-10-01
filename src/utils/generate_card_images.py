import io
from abc import ABC, abstractmethod
from random import randint
from typing import Final, Tuple

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import BICUBIC, NEAREST, HAMMING
from aiogram.types import BufferedInputFile

from src.database import Game, game_scores, playing_cards, games
from settings import Config


class _GameImagePainter(ABC):
    def __init__(self, game: Game):
        self.game = game

        self.draw: ImageDraw = None
        self.table: Image = None
        self.table_size: Tuple[int, int] = (0, 0)

        self.card_size: Final[tuple[int, int]] = (180, 277)

    def _draw_header(self, game_name: str):
        baccarat_text = f"{game_name} №{self.game.number}"
        header_font = ImageFont.truetype("font.otf", 55)
        header_pos = (self.table_size[0] // 2, self.table_size[1] // 9 + 50)

        self.draw.text(
            xy=header_pos, text=baccarat_text,
            fill=(0, 0, 0, 220), font=header_font,
            align='center', anchor='mm'
        )

    async def _draw_card(self, card_file_name: str, xy: tuple[int, int]):
        with Image.open(f'{Config.Games.CARD_IMAGES_PATH}/{card_file_name}.png') as card_img:
            card_img = card_img.resize(self.card_size)
            self.table.paste(card_img, xy, card_img)

    def _get_buffered_file_from_generated_photo(self):
        img_buffer = io.BytesIO()
        self.table.save(img_buffer, format='PNG')
        image_bytes = img_buffer.getvalue()
        buffered_image = BufferedInputFile(image_bytes, filename=f'Результаты игры №{self.game.number}')
        img_buffer.close()
        return buffered_image

    @abstractmethod
    def get_image(self) -> BufferedInputFile:
        ...


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

        print(self.table_size[0] // 2, self.table_size[1] // 2 + 150)
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

    async def __draw_player_cards_and_points(self, player_id: int, player_name: str, cards_start_xy, points_xy):
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

        player_cards = await playing_cards.get_player_cards(
            game_number=self.game.number, player_id=player_id
        )

        for card_num, card in enumerate(player_cards):
            card_file_name = f'{card.value}{card.suit}'
            card_pos = (cards_start_xy[0] - self.card_size[0]//8 * len(player_cards) + self.cards_x_offset * card_num,
                        cards_start_xy[1])
            await self._draw_card(card_file_name=card_file_name, xy=card_pos)

    async def get_image(self, is_finish: bool = False) -> BufferedInputFile:
        with Image.open('cards/clear_table.png') as table:
            self.table = table
            self.table_size = table.size
            self.draw = ImageDraw.Draw(table)

            # рисуем заголовок
            self._draw_header(game_name='BlackJack')

            # рисуем карты и очки игроков
            players = await games.get_players_of_game(game=self.game)
            middle_x = (self.table_size[0] - self.card_size[0]) // 2
            middle_y = (self.table_size[1]-self.card_size[1])//2

            players_cards_start_y = middle_y + int(middle_y // 1.5)
            await self.__draw_player_cards_and_points(
                player_id=players[0].telegram_id, player_name=players[0].name,
                cards_start_xy=(int(middle_x/6), players_cards_start_y),
                points_xy=(150, 415)
            )
            await self.__draw_player_cards_and_points(
                player_id=players[1].telegram_id, player_name=players[1].name,
                cards_start_xy=(middle_x + int(middle_x / 1.5), players_cards_start_y),
                points_xy=(self.table_size[0]-150, 415)
            )
            # рисуем карты и очки банкира
            await self.__draw_banker_cards_and_points(show_cards=is_finish)

            # Сохраняем в буфер готовое фото и возвращаем
            return self._get_buffered_file_from_generated_photo()


class BaccaratImagePainter(_GameImagePainter):
    def __init__(self, game: Game):
        super().__init__(game)

        self.cards_x_spacing = self.card_size[0] - 110
        self.cards_y_spacing = self.card_size[1] // 5

        self.points_font = ImageFont.truetype("font.otf", 45, encoding='UTF-8')

    async def __draw_tokens(self, table: Image):
        token_size = (80, 80)
        table_middle_x = (self.table_size[0] - token_size[0])//2

        fields_y_positions = [
            265,  # Координаты поля 1
            350,  # Координаты поля 2
            435,  # Координаты поля 3
        ]

        moves = sorted(move.value for move in await game_scores.get_game_moves(game=self.game))
        positions = []

        for n, pos in enumerate(fields_y_positions, start=1):
            token_count = moves.count(n)
            used_positions = []
            # Отрисовка фишек
            for _ in range(token_count):
                while True:
                    random_x_pos = randint(500, 700)  # Или другой диапазон, какой вам нужен
                    if all(abs(random_x_pos - pos) >= 20 for pos in used_positions):
                        used_positions.append(random_x_pos)
                        break
                random_rotation = randint(0, 360)

                with Image.open('cards/token.png') as token_img:
                    token_img = token_img.resize(token_size, resample=HAMMING)
                    token_img = token_img.rotate(random_rotation, expand=True, resample=BICUBIC)
                    table.paste(token_img, (random_x_pos, pos), token_img)

    async def __draw_player_cards_and_points(self, start_y_pos: int):
        start_x_left = 50
        player_points = await playing_cards.count_player_score(game_number=self.game.number, player_id=1)
        text = f"ИГРОК\n{player_points}"

        # рисуем текст с очками игрока
        self.draw.text(
            xy=(start_x_left + 5, (self.table_size[1] - self.card_size[1]) // 2 + 100 + 300),
            text=text,
            fill=(255, 255, 0, 230),
            font=self.points_font,
            align='center'
        )
        # рисуем карты игрока
        player_cards = await playing_cards.get_player_cards(game_number=self.game.number, player_id=1)
        for n, card in enumerate(player_cards):
            with Image.open('cards/' + f"{card.value}{card.suit}" + '.png') as card_img:
                card_img = card_img.resize(self.card_size)

                x = start_x_left + n * self.cards_x_spacing
                y = start_y_pos + n * self.cards_y_spacing

                self.table.paste(card_img, (x, y), card_img)

    async def __draw_banker_cards_and_points(self, start_y_pos: int):
        start_x_right = self.table_size[0] - self.card_size[0] - 50

        # Рисуем текст дилера
        banker_points = await playing_cards.count_dealer_score(game_number=self.game.number)
        self.draw.text(
            xy=(start_x_right - 20, (self.table_size[1] - self.card_size[1]) // 2 + 100 + 300),
            text=f"БАНКИР\n{banker_points}",
            fill=(255, 255, 0, 230),
            font=self.points_font,
            align='center'
        )
        # рисуем карты дилера
        banker_cards = await playing_cards.get_dealer_cards(game_number=self.game.number)
        for n, card in enumerate(banker_cards):
            with Image.open('cards/' + f"{card.value}{card.suit}" + '.png') as card_img:
                card_img = card_img.resize(self.card_size)

                x = start_x_right - n * self.cards_x_spacing
                y = start_y_pos + n * self.cards_y_spacing

                self.table.paste(card_img, (x, y), card_img)

    async def get_image(self) -> BufferedInputFile:
        with Image.open('cards/baccarat_table.png') as table:
            self.table = table
            self.table_size = table.size

            self.draw = ImageDraw.Draw(table)

            # рисуем заголовок
            self._draw_header(game_name='BACCARAT')

            # рисуем фишки
            await self.__draw_tokens(table)

            # вычисляем стартовую карт по вертикали
            player_cards = await playing_cards.get_player_cards(game_number=self.game.number, player_id=1)
            banker_cards = await playing_cards.get_dealer_cards(game_number=self.game.number)
            cards_count_vertical_offset = (
                28 if len(player_cards) == 3 or len(banker_cards) == 3
                else 0
            )
            start_y = (self.table_size[1] - self.card_size[1]) // 2 - cards_count_vertical_offset
            # рисуем карты и очки игрока
            await self.__draw_player_cards_and_points(start_y)
            # рисуем карты и очки банкира
            await self.__draw_banker_cards_and_points(start_y)

            # Возвращаем буфер с фото
            return self._get_buffered_file_from_generated_photo()
