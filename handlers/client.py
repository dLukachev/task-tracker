from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.database.models import async_session
from core.database.crud import create_user, create_task, delete_task, get_stat, get_done_tasks_by_user, update_task, get_user_by_tg_id, get_task_by_id, get_unfulfilled_tasks_by_user
from kb.kb import cancel_kb, main_kb, done_task_kb, not_done_task_kb, edit_task_kb, skip_kb, confirm_delete
from handlers.states_class import Form, Edit
from other.dateparser import parse_datetime
import locale

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

r = Router()

@r.message(CommandStart())
async def start(message: Message):
    await message.answer('Привет! Это таск трекер, вот доступные команды\n'
                         '/get_task - получить задачи\n'
                         '/get_done_task - посмотреть выполненные задачи\n'
                         '/create_task - создать задачу\n'
                         '/get_stat - статистика выполненных/просроченных задач', reply_markup=main_kb)
    # Добавление нового пользователя
    async with async_session() as session:
        if get_user_by_tg_id is None:
            await create_user(session=session, tg_id=message.from_user.id, user_name=message.from_user.first_name)

# ----------- Получить список всех задач -----------

@r.message(Command('get_task'))
async def get_task(message: Message):
    async with async_session() as session:
        tasks = await get_unfulfilled_tasks_by_user(session=session, user_id=message.from_user.id)

    if not tasks:
        await message.answer('У тебя нет задач.')
        return

    await message.answer(f'Вот твои задачи:')
    
    for item in tasks:
        task = (f'{item.title} : {item.description}\nДата создания {f"{item.create_time.strftime('%-d %B в %H:%M') if item.create_time is not None else 'бессрочно'}"}\nВыполнить до {f"{item.time_end.strftime('%-d %B в %H:%M') if item.time_end is not None else 'бессрочно'}"}\n\n')
        await message.answer(task, reply_markup=done_task_kb(item.id))

# ----------- Получить список всех задач -----------

# ----------- Получить список только выполенных задач -----------

@r.message(Command('get_done_task'))
async def get_done_task(message: Message):
    async with async_session() as session:
        tasks = await get_done_tasks_by_user(session=session, user_id=message.from_user.id)
    
    if not tasks:
        await message.answer(f'У вас нет выполненных задач!')
        return

    await message.answer(f'Вот выполненные задачи:')

    for item in tasks:
        await message.answer(f'{item.title} : {item.description}\nДата создания {f"{item.create_time.strftime('%-d %B в %H:%M') if item.create_time is not None else 'бессрочно'}"}\n\n', reply_markup=not_done_task_kb(item.id))

# ----------- Получить список только выполенных задач -----------

# ----------- Получить статистику по задачам -----------

@r.message(Command('get_stat'))
async def get_st(message: Message):
    async with async_session() as session:
        t_true, t_false = await get_stat(session=session, user_id=message.from_user.id)
    await message.answer(f'Выполнено {t_true}, не выполнено {t_false}')

# ----------- Создать таску -----------

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
    await message.answer('Введите время для напоминания о таске', reply_markup=skip_kb)
    await state.update_data(description = message.text)
    await state.set_state(Form.enter_endtime)


@r.message(Form.enter_endtime)
async def enter_endtime(message: Message, state: FSMContext):
    if message.text == 'Не напоминать':
        await state.update_data(time_end = None)
    else:
        dt = await parse_datetime(message.text)
        
        if dt is None:
            await message.answer("Неверный формат даты, попробуйте снова")
            return
        
        await state.update_data(time_end = dt)

    data = await state.get_data()
    async with async_session() as session:
        await create_task(session=session, user_id=message.from_user.id, title=data.get('title'), description=data.get('description'), time_end=data.get('time_end'))
    await state.clear()
    await message.answer(f'Создано!', reply_markup=main_kb)
    await get_task(message)

# ----------- Создать таску -----------

# ----------- Изменить таску -----------

@r.callback_query(F.data.startswith("edit:"))
async def edit_task(callback_query, state: FSMContext):
    task_id = int(callback_query.data.split(":")[1])
    await state.update_data(task_id=task_id)
    async with async_session() as session:
        task = await get_task_by_id(session=session, task_id=task_id)
    await callback_query.message.edit_text(f"{task.title} : {task.description}\nВыполнить до {f"{task.time_end.strftime('%-d %B в %H:%M') if task.time_end is not None else 'бессрочно'}"}\n\nЧто необходимо изменить?", reply_markup=edit_task_kb())
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
    await message.answer(f"{task.title} : {task.description}\nВыполнить до {f"{task.time_end.strftime('%-d %B в %H:%M') if task.time_end is not None else 'бессрочно'}"}\n\nЧто необходимо изменить?", reply_markup=edit_task_kb())
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
    await message.answer(f"{task.title} : {task.description}\nВыполнить до {f"{task.time_end.strftime('%-d %B в %H:%M') if task.time_end is not None else 'бессрочно'}"}\n\nЧто необходимо изменить?", reply_markup=edit_task_kb())
    await state.set_state(Edit.choose)

@r.callback_query(Edit.choose, F.data == "notif")
async def edit_notif(callback_query, state: FSMContext):
    await callback_query.message.edit_text('Напишите когда напомнить о таске', reply_markup=cancel_kb)
    await state.set_state(Edit.enter_endtime)


@r.message(Edit.enter_endtime)
async def edit_notif(message: Message, state: FSMContext):
    date = message.text
    dt = await parse_datetime(date)

    print(dt)

    if dt is None:
        await message.answer('Не удалось распознать дату, напишите, пожалуйста, в виде\n\n31.12.2025 14:30\nзавтра в 15:00\nчерез 2 часа')

    data = await state.get_data()
    task_id = data.get('task_id')

    async with async_session() as session:
        await update_task(session=session, task_id=task_id, time_end=dt, user_id=message.from_user.id)
        task = await get_task_by_id(session=session, task_id=task_id)
    
    await message.answer('Время окончания обновлено!')
    await message.answer(f"{task.title} : {task.description}\nВыполнить до {f"{task.time_end.strftime('%-d %B в %H:%M') if task.time_end is not None else 'бессрочно'}"}\n\nЧто необходимо изменить?", reply_markup=edit_task_kb())
    await state.set_state(Edit.choose)

# ----------- Изменить таску -----------

# ----------- Удалить таску -----------

@r.callback_query(F.data.startswith("delete:"))
async def del_task_in_state(callback_query):

    try:
        task_id = int(callback_query.data.split(":")[1])
    except:
        task_id = int(callback_query.data.split("::")[1])
        async with async_session() as session:
            task = await get_task_by_id(session=session, task_id=task_id)
        await callback_query.message.edit_text(f'Номер таски {task.id}\n{task.title} : {task.description}\nДата создания {f"{task.create_time.strftime('%-d %B в %H:%M') if task.create_time is not None else 'бессрочно'}"}\nВыполнить до {f"{task.time_end.strftime('%-d %B в %H:%M') if task.time_end is not None else 'бессрочно'}"}', reply_markup=done_task_kb(task_id))
        return
    
    async with async_session() as session:
        task = await delete_task(session=session, task_id=task_id)
    
    await callback_query.message.edit_text('Успешно.')

# ----------- Удалить таску -----------

# ----------- Сделать таску выполненной -----------

@r.callback_query(F.data.startswith("done:"))
async def done_handler(callback_query):
    task_id = int(callback_query.data.split(":")[1])
    async with async_session() as session:
        await update_task(session=session, task_id=task_id , is_done=True)
    await callback_query.message.edit_text("Задача отмечена как выполненная!")
    await callback_query.answer()

# ----------- Сделать таску выполненной -----------

# ----------- Сделать таску не выполненной -----------

@r.callback_query(F.data.startswith("not_done:"))
async def done_handler(callback_query):
    task_id = int(callback_query.data.split(":")[1])
    async with async_session() as session:
        await update_task(session=session, task_id=task_id , is_done=False)
    await callback_query.message.edit_text("Задача отмечена как невыполненная!")
    await callback_query.answer()

# ----------- Сделать таску не выполненной -----------

# ----------- Подтвердить удаление -----------

@r.callback_query(F.data.startswith("confirm:"))
async def def_delete_task(callback_query):
    task_id = int(callback_query.data.split(":")[1])
    await callback_query.message.edit_text('Вы уверены что хотите удалить задачу? Ее больше не восстановить!', reply_markup=confirm_delete(task_id))

# ----------- Подтвердить удаление -----------


# ----------- Отмена -----------

@r.callback_query(F.data == "cancel")
async def cancel_handler(callback_query, state: FSMContext):
    await state.clear()
    await callback_query.message.edit_text("Действие отменено.")
    await callback_query.answer()

# ----------- Отмена -----------
