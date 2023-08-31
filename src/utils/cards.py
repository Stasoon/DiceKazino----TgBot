import random
from dataclasses import dataclass
from typing import Generator, Any


@dataclass
class Card:
    value: str
    suit: str


def get_shuffled_deck(decks_cont: int = 1) -> Generator[Card, Any, Any]:
    """Возвращает генератор (колоду) с объектами Card.  \n
    decks_count - сколько колод использовать"""
    suits = ("Ч", "Б", "П", "К")  # Червы, Бубы, Пики, Кресты
    values = (*[str(i) for i in range(2, 10 + 1)], "В", "Д", "К", "Т")

    deck = [Card(value, suit) for value in values for suit in suits] * decks_cont
    random.shuffle(deck)

    return (card for card in deck)
