from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


from core.models import async_session
from core.crud import create_user, get_tasks_by_user, create_task, delete_task, get_stat, get_done_tasks_by_user, update_task, get_user_by_tg_id, get_task_by_id
from kb.kb import cancel_kb, main_kb, done_task_kb, not_done_task_kb, edit_task_kb
import locale

from other.dateparser import parse_datetime

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

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

r = Router()


@r.message(CommandStart())
async def start(message: Message):
    await message.answer('Привет! Это таск трекер, вот доступные команды\n'
                         '/get_task - получить задачи\n'
                         '/get_done_task - посмотреть выполненные задачи\n'
                         '/create_task - создать задачу\n'
                         '/delete_task id - удалить задачу\n'
                         '/get_stat - статистика выполненных/просроченных задач', reply_markup=main_kb)
    # Добавление нового пользователя
    async with async_session() as session:
        if get_user_by_tg_id is None:
            await create_user(session=session, tg_id=message.from_user.id, user_name=message.from_user.first_name)


@r.message(Command('help'))
async def help(message: Message):
    await message.answer('Это таск трекер, вот доступные команды\n'
                         '/get_task - получить задачи\n'
                         '/get_done_task - посмотреть выполненные задачи\n'
                         '/create_task - создать задачу\n'
                         '/delete_task id - удалить задачу\n'
                         '/get_stat - статистика выполненных/просроченных задач', reply_markup=main_kb)


@r.callback_query(F.data == "cancel")
async def cancel_handler(callback_query, state: FSMContext):
    await state.clear()
    await callback_query.message.edit_text("Действие отменено. Напишите /help для получения информации по командам")
    await callback_query.answer()


@r.callback_query(F.data.startswith("done:"))
async def done_handler(callback_query):
    task_id = int(callback_query.data.split(":")[1])
    async with async_session() as session:
        await update_task(session=session, task_id=task_id , is_done=True)
    await callback_query.message.edit_text("Задача отмечена как выполненная!")
    await callback_query.answer()

@r.callback_query(F.data.startswith("edit:"))
async def edit_task(callback_query, state: FSMContext):
    task_id = int(callback_query.data.split(":")[1])
    await state.update_data(task_id=task_id)
    async with async_session() as session:
        task = await get_task_by_id(session=session, task_id=task_id)
    await callback_query.message.edit_text(f"{task.title} : {task.description}\nВремя окончания {'бессрочно' if task.time_end is None else task.time_end}\n\nЧто необходимо изменить?", reply_markup=edit_task_kb())
    await state.set_state(Edit.choose)

@r.callback_query(Edit.choose, F.data == 'title')
async def edit_title(callback_query, state: FSMContext):
    await callback_query.message.edit_text('Введите заголовок', reply_markup=cancel_kb)
    await state.set_state(Edit.enter_title)

@r.message(Edit.enter_title)
async def edit_title(message: Message, state: FSMContext):
    title = message.text
    data = await state.get_data()
    task_id = data.get('task_id')
    async with async_session() as session:
        await update_task(session=session, task_id=task_id, title=title)
        task = await get_task_by_id(session=session, task_id=task_id)
    await message.answer('Заголовок обновлен!')
    await message.answer(f"{task.title} : {task.description}\nВремя окончания {'бессрочно' if task.time_end is None else task.time_end}\n\nЧто необходимо изменить?", reply_markup=edit_task_kb())
    await state.set_state(Edit.choose)
    
@r.callback_query(Edit.choose, F.data == "descr")
async def edit_descr(callback_query, state: FSMContext):
    await callback_query.message.edit_text('Введите описание', reply_markup=cancel_kb)
    await state.set_state(Edit.enter_descr)

@r.message(Edit.enter_descr)
async def edit_descr(message: Message, state: FSMContext):
    descr = message.text
    data = await state.get_data()
    task_id = data.get('task_id')
    async with async_session() as session:
        await update_task(session=session, task_id=task_id, description=descr)
        task = await get_task_by_id(session=session, task_id=task_id)
    await message.answer('Описание обновлено!')
    await message.answer(f"{task.title} : {task.description}\nВремя окончания {'бессрочно' if task.time_end is None else task.time_end}\n\nЧто необходимо изменить?", reply_markup=edit_task_kb())
    await state.set_state(Edit.choose)

@r.callback_query(Edit.choose, F.data == "notif")
async def edit_notif(callback_query, state: FSMContext):
    await callback_query.message.edit_text('Напишите когда напомнить о таске', reply_markup=cancel_kb)
    await state.set_state(Edit.enter_endtime)


@r.message(Edit.enter_endtime)
async def edit_notif(message: Message, state: FSMContext):
    date = message.text
    dt = await parse_datetime(date)

    if dt is None:
        await message.answer('Не удалось распознать дату, напишите, пожалуйста, в виде\n31.12.2025 14:30\nзавтра в 15:00\nчерез 2 часа\n2025-12-31 14:30')

    data = await state.get_data()
    task_id = data.get('task_id')

    async with async_session() as session:
        await update_task(session=session, task_id=task_id, time_end=dt)
        task = await get_task_by_id(session=session, task_id=task_id)
    
    await message.answer('Время окончания обновлено!')
    await message.answer(f"{task.title} : {task.description}\nВремя окончания {'бессрочно' if task.time_end is None else task.time_end}\n\nЧто необходимо изменить?", reply_markup=edit_task_kb())
    await state.set_state(Edit.choose)


@r.callback_query(F.data.startswith("not_done:"))
async def done_handler(callback_query):
    task_id = int(callback_query.data.split(":")[1])
    async with async_session() as session:
        await update_task(session=session, task_id=task_id , is_done=False)
    await callback_query.message.edit_text("Задача отмечена как невыполненная!")
    await callback_query.answer()


@r.message(Command('get_task'))
async def get_task(message: Message):
    async with async_session() as session:
        tasks = await get_tasks_by_user(session=session, user_id=message.from_user.id)

    if not tasks:
        await message.answer('У тебя нет задач.')
        return

    await message.answer(f'Вот твои задачи:')
    
    for item in tasks:
        task = (f'Номер таски {item.id}\n{item.title} : {item.description}\nДата создания {f"{item.create_time.strftime('%-d %B в %H:%M') if item.create_time is not None else 'бессрочно'}"}\nВыполнить до {f"{item.time_end.strftime('%-d %B в %H:%M') if item.time_end is not None else 'бессрочно'}"}\n\n')
        if item.is_done:
            continue
        await message.answer(task, reply_markup=done_task_kb(item.id))


@r.message(Command('get_done_task'))
async def get_done_task(message: Message):
    async with async_session() as session:
        tasks = await get_done_tasks_by_user(session=session, user_id=message.from_user.id)
    
    if not tasks:
        await message.answer(f'У вас нет выполненных задач!')
        return

    await message.answer(f'Вот выполненные задачи:')

    for item in tasks:
        await message.answer(f'Номер таски {item.id}\n{item.title} : {item.description}\nДата создания {f"{item.create_time.strftime('%-d %B в %H:%M') if item.create_time is not None else 'бессрочно'}"}\n\n', reply_markup=not_done_task_kb(item.id))


@r.message(Command('create_task'))
async def def_create_task(message: Message, state: FSMContext):
    await message.answer('Введи заголовок таски', reply_markup=cancel_kb)
    await state.set_state(Form.enter_title)


@r.message(Form.enter_title)
async def enter_title(message: Message, state: FSMContext):
    await message.answer('Введи описание таски', reply_markup=cancel_kb)
    await state.update_data(title = message.text)
    await state.set_state(Form.enter_description)


@r.message(Form.enter_description)
async def enter_description(message: Message, state: FSMContext):
    await state.update_data(description = message.text)
    
    data = await state.get_data()

    async with async_session() as session:
        await create_task(session=session, user_id=message.from_user.id, title=data.get('title'), description=data.get('description'))
    
    await state.clear()

    await message.answer(f'Создано!')
    await get_task(message)


@r.message(Command('delete_task'))
async def def_delete_task(message: Message, state: FSMContext):
    await message.answer('Напиши только номер(а) задач(и) для удаления\n'
                         'Если нужно удалить сразу несколько, то напишите айди просто через пробел, например: 1 44 912 33', reply_markup=cancel_kb)
    await state.set_state(Form.del_task)


@r.message(Form.del_task)
async def del_task_in_state(message: Message, state: FSMContext):

    mes = message.text
    tasks = mes.split()
    async with async_session() as session:
        for item in tasks:
            task = await delete_task(session=session, task_id=item)
    
    if task:
        await message.answer('Успешно!')
    else:
        await message.answer('Таска не найдена')
    
    await state.clear()


@r.message(Command('get_stat'))
async def get_st(message: Message):
    async with async_session() as session:
        r_t, r_f = await get_stat(session=session, user_id=message.from_user.id)
    await message.answer(f'Выполнено {r_t}, не выполнено {r_f}')