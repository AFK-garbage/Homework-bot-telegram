from aiogram.fsm.state import State, StatesGroup

class ModeratorStates(StatesGroup):
    waiting_for_password = State()
    waiting_for_new_moderator_id = State()
    waiting_for_new_moderator_password = State()