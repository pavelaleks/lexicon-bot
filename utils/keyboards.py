# utils/keyboards.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Тренировка")],
            [KeyboardButton(text="📝 Контрольная")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="📊 Статистика")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def topics_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=topic)] for topic in ["Тире", "Двоеточие", "Кавычки", "Запятая"]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def post_train_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Следующее")],
            [KeyboardButton(text="К темам")],
            [KeyboardButton(text="Правила")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def post_exam_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Повторить контрольную")],
            [KeyboardButton(text="В тренировку")],
            [KeyboardButton(text="Правила")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
