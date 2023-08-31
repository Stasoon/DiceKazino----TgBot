from tortoise.exceptions import DoesNotExist

from .models import PlayerMove, Game


# Create
async def add_player_move_if_not_moved(game: Game, player_telegram_id: int, move_value: int) -> None:
    await PlayerMove.get_or_create(game=game, player_id=player_telegram_id, defaults={'value': move_value})


# Read
async def get_game_moves(game: Game) -> list[PlayerMove]:
    moves = await PlayerMove.filter(game=game).all()
    return moves


# Delete
async def delete_game_moves(game: Game) -> None:
    try:
        await PlayerMove.filter(game=game).delete()
    except DoesNotExist:
        pass
