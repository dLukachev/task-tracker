import os
from dotenv import load_dotenv
from aiogram.client.bot import Bot 

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError('BOT_TOKEN not found in .env') 

bot = Bot(token=BOT_TOKEN)