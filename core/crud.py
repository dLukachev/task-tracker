# crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.models import User, Task 
from datetime import datetime
from other.scheduler import scheduler
from other.sendnotify import send_alert

# --- USER CRUD ---

async def get_user_by_tg_id(session: AsyncSession, tg_id: int):
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, tg_id: int, user_name: str):
    user = User(tg_id=tg_id, user_name=user_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_or_create_user(session: AsyncSession, tg_id: int, user_name: str):
    user = await get_user_by_tg_id(session, tg_id)
    if user is None:
        user = await create_user(session, tg_id, user_name)
    return user

# --- TASK CRUD ---

async def create_task(
    session: AsyncSession,
    user_id: int,
    title: str,
    description: str = None,
    time_end: datetime = None
):
    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        time_end=time_end,
        create_time=datetime.now()
    )
    
    if time_end is not None:
        s = scheduler.add_job(send_alert, 'date', run_date=time_end, args=[user_id, title])
        print(f'Отладка = {s}')

    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task

async def get_task_by_id(session: AsyncSession, task_id: int):
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()

async def get_tasks_by_user(session: AsyncSession, user_id: int):
    result = await session.execute(select(Task).where(Task.user_id == user_id))
    return result.scalars().all()

async def get_unfulfilled_tasks_by_user(session: AsyncSession, user_id: int):
    result = await session.execute(select(Task).where(Task.user_id == user_id, Task.is_done == False))
    return result.scalars().all()

async def get_done_tasks_by_user(session: AsyncSession, user_id: int):
    result = await session.execute(select(Task).where(Task.user_id == user_id, Task.is_done == True))
    return result.scalars().all()

async def update_task(
    session: AsyncSession,
    task_id: int,
    title: str = None,
    description: str = None,
    is_done: bool = None,
    time_end: datetime = None
):
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return None
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if is_done is not None:
        task.is_done = is_done
    if time_end is not None:
        task.time_end = time_end
    await session.commit()
    await session.refresh(task)
    return task

async def delete_task(session: AsyncSession, task_id: int):
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return False
    await session.delete(task)
    await session.commit()
    return True


async def get_stat(session: AsyncSession, user_id: int):
    result_t = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.is_done == True)
    )
    result_f = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.is_done == False)
    )
    done_tasks = result_t.scalars().all()
    undone_tasks = result_f.scalars().all()
    return len(done_tasks), len(undone_tasks)