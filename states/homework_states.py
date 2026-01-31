from aiogram.fsm.state import State, StatesGroup

class HomeworkStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_task = State()
    waiting_for_deadline = State()
    waiting_for_files = State()