from aiogram.fsm.state import StatesGroup, State


class AdminStates:
    class MailingPostCreating(StatesGroup):
        wait_for_content_message = State()
        wait_for_button_data = State()
        wait_for_confirm = State()


class UserStates:
    class EnterBet(StatesGroup):
        wait_for_bet_amount = State()

    class EnterEvenUnevenBet(StatesGroup):
        wait_for_bet = State()

    class AutoDeposit(StatesGroup):
        wait_for_amount = State()

    class HalfAutoDeposit(StatesGroup):
        wait_for_amount = State()
        wait_for_screen = State()

    class HalfAutoWithdraw(StatesGroup):
        wait_for_amount = State()
        wait_for_requisites = State()
        wait_for_confirm = State()
