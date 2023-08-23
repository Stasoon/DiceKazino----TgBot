from typing import List, Generator

from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.functions import Count

from .models import Game, User
from .users import get_user_or_none
from src.misc import GameStatus, GameType


# Create
async def create_game(creator_telegram_id: int, max_players: int, game_type: GameType, bet: float) -> Game:
    status = GameStatus.ACTIVE if max_players == 1 else GameStatus.WAIT_FOR_PLAYERS
    creator_user = await get_user_or_none(telegram_id=creator_telegram_id)

    game = await Game.create(
        max_players=max_players,
        type=game_type.value,
        status=status.value,
        bet=bet
    )
    await game.players.add(creator_user)
    return game


# Get
async def get_game_obj(game_number: int) -> Game:
    game = await Game.get(number=game_number)
    return game


async def get_creator_of_game(game: Game) -> User:
    return await game.players.all().first()


async def get_players_of_game(game: Game) -> List[User]:
    return await game.players.all()


async def get_player_ids_of_game(game: Game):
    return await game.players.all().values_list('telegram_id', flat=True)


async def get_total_games_count() -> int:
    return await Game.all().count()


async def is_game_full(game: Game) -> bool:
    players = await get_players_of_game(game)
    return True if len(players) >= game.max_players else False


async def get_available_games(user_telegram_id: int) -> list[Game]:
    return await Game.filter(status=GameStatus.WAIT_FOR_PLAYERS).exclude(players__telegram_id=user_telegram_id)


async def get_user_participated_games(telegram_id: int) -> list[Game]:
    try:
        user = await User.get(telegram_id=telegram_id)
        participated_games = await user.games_participated.all()
        return participated_games
    except DoesNotExist:
        return []


async def get_user_active_game(telegram_id: int) -> Game | None:
    user = await User.get_or_none(telegram_id=telegram_id)
    await user.fetch_related('games_participated')
    game = await user.games_participated.filter(
        (Q(status=GameStatus.ACTIVE) | Q(status=GameStatus.WAIT_FOR_PLAYERS)) & Q(players=user)
    ).all().first()

    return game if game else None


async def get_top_players(limit: int = 10) -> Generator:
    top_players = await User.annotate(winnings_count=Count('games_won')).order_by('-winnings_count').limit(limit)

    return ({'telegram_id': player.telegram_id, 'name': player.name, 'winnings_count': player.winnings_count}
            for player in top_players if player.winnings_count > 0)


# Update
async def finish_game(game_number: int, winner_telegram_id: int = None) -> None:
    game = await Game.get(number=game_number)

    winner_user = await get_user_or_none(telegram_id=winner_telegram_id) if winner_telegram_id else None
    game.winner = winner_user
    game.status = GameStatus.FINISHED.value
    await game.save()


async def add_user_to_game(telegram_id: int, game_number: int) -> None:
    user = await User.get(telegram_id=telegram_id)
    game = await Game.get(number=game_number)

    await game.players.add(user)
    if await is_game_full(game):
        game.status = GameStatus.ACTIVE

    await game.save()
