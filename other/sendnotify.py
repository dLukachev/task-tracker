from core.bot import bot

async def send_alert(user_id, title):
    await bot.send_message(chat_id=user_id, text=f'Задача "{title}" просрочена! Выполните как можно скорее.'
)
