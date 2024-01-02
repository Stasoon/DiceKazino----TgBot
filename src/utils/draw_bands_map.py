import io
import os

from PIL import Image, ImageDraw, ImageFont
from aiogram.types import BufferedInputFile

from src.misc.enums.leagues import BandLeague


def get_positions(league: BandLeague) -> list[tuple[int, int]]:
    match league:
        case BandLeague.GAMBLERS:
            return [(740, 1200), (200, 260), (800, 320)]
        case BandLeague.CARD_MASTERS:
            return [(50, 50), (1, 1)]
        case BandLeague.BUSINESSMEN:
            return [(50, 50), (1, 1)]
        case BandLeague.INDUSTRIALISTS:
            return [(50, 50), (1, 1)]
        case BandLeague.MAGNATES:
            return [(50, 50), (1, 1)]
        case BandLeague.MONOPOLISTS:
            return [(50, 50), (1, 1)]


def get_map_image_path(league: BandLeague):
    folder_path = os.path.join(os.getcwd(), 'resources', 'bands')
    extension = '.jpg'
    image_name = ''

    match league:
        case BandLeague.GAMBLERS:
            image_name = 'gamblers'
        case BandLeague.CARD_MASTERS:
            image_name = 'card_masters'
        case BandLeague.BUSINESSMEN:
            image_name = 'businessmen'
        case BandLeague.INDUSTRIALISTS:
            image_name = 'industrialists'
        case BandLeague.MAGNATES:
            image_name = 'magnates'
        case BandLeague.MONOPOLISTS:
            image_name = 'monopolists'

    return os.path.join(folder_path, f"{image_name}{extension}")


def get_bands_map(band_names: list[str], band_league: BandLeague) -> BufferedInputFile:
    map_img_path = get_map_image_path(band_league)
    band_names = band_names + ['Мистер Н']*(6-len(band_names))
    print(band_names)

    with Image.open(map_img_path) as map_image:
        bands_map = map_image

        draw = ImageDraw.Draw(bands_map)

        for band_name, position in zip(band_names, get_positions(band_league)):
            font_size = 80

            font = ImageFont.truetype("resources/fonts/Eina01-Bold.ttf", size=font_size, encoding='UTF-8')
            draw.text(
                xy=position, text=band_name,
                fill=(255, 255, 255),
                align='center',
                font=font
            )

        img_buffer = io.BytesIO()
        bands_map.save(img_buffer, format='PNG')

        image_bytes = img_buffer.getvalue()
        buffered_image = BufferedInputFile(image_bytes, filename=f'Карта')
        img_buffer.close()
        return buffered_image

