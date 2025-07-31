import os, logging, asyncio
from dotenv import load_dotenv
from aiogram.client.bot import Bot
from aiogram import Dispatcher
from handlers.client import r
from core.create import init_db
from other.scheduler import scheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError('BOT_TOKEN not found in .env') 

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()

async def main():
    dp.include_router(r)
    await dp.start_polling(bot)

async def shu():
    scheduler.start()

if __name__ == '__main__':
    asyncio.run(shu())
    asyncio.run(main())
    asyncio.run(init_db())