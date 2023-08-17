from aiogram.fsm.state import StatesGroup, State


class PlayingStates(StatesGroup):
    wait_for_move = State()
