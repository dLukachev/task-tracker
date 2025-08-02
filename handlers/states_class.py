from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    enter_title = State()
    enter_description = State()
    enter_endtime = State()
    del_task = State()

class Edit(StatesGroup):
    choose = State()
    enter_title = State()
    enter_descr = State()
    enter_endtime = State()