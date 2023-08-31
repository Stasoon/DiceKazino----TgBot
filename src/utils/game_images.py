import io

from PIL import Image, ImageDraw, ImageFont
from aiogram.types import BufferedInputFile

from src.handlers.user.bot.games_process.baccarat import BaccaratResult


def _draw_baccarat_header(draw: ImageDraw, game_number: int, table_size: tuple[int, int]):
    baccarat_text = f"BACCARAT №{game_number}"

    draw.text(
        (table_size[0] // 2, table_size[1] // 9 + 50),
        text=baccarat_text,
        fill=(0, 0, 0, 220),
        font=ImageFont.truetype("font.otf", 55),
        align='center',
        anchor='mm'
    )


def draw_baccarat_results_image(game_number: int, result: BaccaratResult):
    with Image.open('cards/table.png') as table:
        bg_width, bg_height = table.size

        draw = ImageDraw.Draw(table)
        font = ImageFont.truetype("font.otf", 45)

        # рисуем заголовок
        _draw_baccarat_header(draw, game_number, table.size)

        card_size = (180, 277)

        cards_x_spacing = card_size[0] - 110
        cards_y_spacing = card_size[1] // 5

        start_x_left = 100
        start_x_right = bg_width - card_size[0] - 100

        # рисуем текст и карты для левой части
        draw.text(
            (start_x_left + 5, (bg_height - card_size[1]) // 2 + 100 + 300),
            text=f"ИГРОК\n{result.player_points}",
            fill=(255, 255, 0, 230),
            font=font,
            align='center'
        )

        for n, card in enumerate(result.player_cards):
            with Image.open('cards/' + f"{card.value}{card.suit}" + '.png') as card_img:
                card_img = card_img.resize(card_size)

                x = start_x_left + n * cards_x_spacing
                y = (bg_height - card_size[1]) // 2 + n * cards_y_spacing

                table.paste(card_img, (x, y), card_img)

        # Рисуем текст и карты для правой части
        draw.text(
            (start_x_right, (bg_height - card_size[1]) // 2 + 100 + 300),
            text=f"БАНКИР\n{result.banker_points}",
            fill=(255, 255, 0, 230),
            font=font,
            align='center'
        )

        for n, card in enumerate(result.banker_cards):
            with Image.open('cards/' + f"{card.value}{card.suit}" + '.png') as card_img:
                card_img = card_img.resize(card_size)

                x = start_x_right - n * cards_x_spacing
                y = (bg_height - card_size[1]) // 2 + n * cards_y_spacing

                table.paste(card_img, (x, y), card_img)

        img_buffer = io.BytesIO()
        table.save(img_buffer, format='PNG')
        image_bytes = img_buffer.getvalue()
        buffered_image = BufferedInputFile(image_bytes, 'Результаты игры')
        img_buffer.close()
        return buffered_image
