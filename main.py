import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers.common import register_common
from handlers.train import register_train
from handlers.exam import register_exam

# Логирование
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

def get_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Тренировка")],
            [KeyboardButton(text="📝 Контрольная")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="📊 Статистика")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

async def cmd_start(message: Message):
    await message.answer(
        (
            "👋 *Добро пожаловать в бот «Тренировка ОГЭ по русскому языку» от студии «Лексикон»!*\n\n"
            "Мы поможем вам отточить навык пунктуации для Задания № 5:\n"
            "• *Тире*\n"
            "• *Двоеточие*\n"
            "• *Кавычки*\n"
            "• *Запятая*\n\n"
            "🎯 Нажмите «Тренировка» или введите /train, чтобы попрактиковаться по темам.\n"
            "📝 После уверенной тренировки переходите в режим «Контрольная» (/exam) и проверьте себя на случайных заданиях.\n\n"
            "ℹ️ *Команды:* /train, /exam, /help, /stats"
        ),
        parse_mode="Markdown",
        reply_markup=get_main_kb()
    )

def main():
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Стартовый хендлер
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.message.register(cmd_start, lambda m: m.text == "Начать")

    # Регистрируем остальные
    register_common(dp)
    register_train(dp)
    register_exam(dp)

    logger.info(f"{settings.bot_name} запущен")
    dp.run_polling(bot)

if __name__ == "__main__":
    main()
