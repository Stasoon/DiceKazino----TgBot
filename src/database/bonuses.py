import string
import random
from decimal import Decimal

from tortoise.exceptions import IntegrityError

from .models import Bonus


def __generate_activation_code(length=6):
    """Генерирует код активации """
    characters = f'{string.ascii_letters}{string.digits}'  # Все заглавные буквы и цифры
    code = ''.join(random.choice(characters) for _ in range(length))
    return code


# Create
async def create_bonus(amount: float, activations_count: int = 50, activation_code: str = None) -> bool:
    """Создать новый бонус. Если activation_code не указано, будет сгенерирован рандомно."""
    amount = Decimal(amount)

    # Если активационный код не указан, генерируем рандомно
    if not activation_code:
        # Создаём новый код до тех пор, пока он будет не занят
        while True:
            activation_code = __generate_activation_code()
            if await check_activation_code_not_occupied(activation_code):
                break

    # Пытаемся создать бонус
    try:
        await Bonus.create(
            amount=amount, activation_code=activation_code,
            available_activations_count=activations_count
        )
    # Если возникает ошибка уникальности, возвращаем False
    except IntegrityError:
        return False
    return True


# Read
async def check_activation_code_not_occupied(code_to_check) -> bool:
    bonus = await Bonus.get_or_none(activation_code=code_to_check)
    return bonus is None


async def get_bonus_by_activation_code_or_none(code: str) -> Bonus | None:
    return await Bonus.get_or_none(activation_code=code)


# Update
# async def increase_activations_count_of_bonus(bonus: Bonus):
#     # Если количество активаций бонуса превышено, делаем бонус неактивным
#     if bonus.activations_count == bonus.available_activations_count:
#         bonus.is_active = False
#     # Иначе увеличиваем количество активаций
#     else:
#         bonus.activations_count += 1
#     await bonus.save()


# Delete
async def delete_bonus(bonus: Bonus):
    await bonus.delete()
