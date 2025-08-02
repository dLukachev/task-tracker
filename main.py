import logging, asyncio
from aiogram import Dispatcher
from handlers.client import r
from core.database.init_base import init_db
from other.scheduler import scheduler

from core.bot import bot

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

dp = Dispatcher()

async def main():
    dp.include_router(r)
    await init_db()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())