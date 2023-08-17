from enum import IntEnum


class GameStatus(IntEnum):
    WAIT_FOR_PLAYERS = 0
    ACTIVE = 1
    FINISHED = 2
    CANCELED = 3

    def __str__(self):
        return '0 - Wait for players' \
               '1 - Active' \
               '2 - Finished' \
               '3 - Canceled'
