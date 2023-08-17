from tortoise.exceptions import DoesNotExist

from .models import PlayerMove, Game, User


# Create
async def add_player_move(game: Game, player_telegram_id: int, move: int):
    try:
        player = await User.get(telegram_id=player_telegram_id)
        player_move = PlayerMove(game=game, player=player, value=move)
        await player_move.save()
    except DoesNotExist:
        pass


# Read
async def get_game_moves(game: Game) -> list[PlayerMove]:
    moves = await PlayerMove.filter(game=game).all()
    return moves


# Delete
async def delete_game_moves(game: Game):
    try:
        await PlayerMove.filter(game=game).delete()
    except DoesNotExist:
        pass
