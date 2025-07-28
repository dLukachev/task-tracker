from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


cancel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ]
)

def done_task_kb(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выполнено", callback_data=f"done:{task_id}")],
            [InlineKeyboardButton(text="Изменить", callback_data=f"edit:{task_id}")]
        ]
    )

def edit_task_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заголовок", callback_data=f"title")],
            [InlineKeyboardButton(text="Описание", callback_data=f"descr")],
            [InlineKeyboardButton(text="Напоминание", callback_data=f"notif")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )

def not_done_task_kb(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Не выполнено", callback_data=f"not_done:{task_id}")]
        ]
    )

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/get_task"),KeyboardButton(text="/get_done_task")],
        [KeyboardButton(text="/create_task"),KeyboardButton(text="/delete_task")],
        [KeyboardButton(text='/get_stat')]
    ],
    resize_keyboard=True, one_time_keyboard=True
)

skip_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Не напоминать")]
    ],
    resize_keyboard=True, one_time_keyboard=True
)