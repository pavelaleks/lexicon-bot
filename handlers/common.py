from typing import Union

from aiogram import types, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.stats import get_stats

# --- Получение имени пользователя ---
def get_username(user: types.User) -> str:
    return (
        user.full_name
        or user.username
        or f"пользователь {user.id}"
    )

# --- Справка ---
async def cmd_help(message: types.Message):
    name = get_username(message.from_user)
    text = (
        f"❓ *Помощь для {name}*\n\n"
        "Бот поможет вам потренироваться для Задания 5 ОГЭ: выбирайте режим и решайте задания!\n\n"
        "*🧩 Режим «Тренировка»* — команда /train или кнопка «🎯 Тренировка»:\n"
        "1. Выберите тему (например, «Тире»).\n"
        "2. Прочитайте задание.\n"
        "3. Нажимайте цифры — это позиции, где должен стоять знак препинания.\n"
        "4. Жмите ✅ «Проверить», чтобы увидеть ответ.\n"
        "5. Затем — «Следующее» или «К темам».\n\n"
        "*📝 Режим «Контрольная»* — команда /exam или кнопка «📝 Контрольная»:\n"
        "1. Выберите: 5, 10, 20 или 50 заданий.\n"
        "2. Выполняйте их подряд, у вас ограниченное время.\n"
        "3. В конце бот покажет результат, процент правильных ответов и темы, где были ошибки.\n\n"
        "📌 *Команды:*\n"
        "• /train — режим тренировки по темам\n"
        "• /exam — контрольная на время\n"
        "• /help — справка и инструкции (вы здесь!)\n"
        "• /stats — посмотреть статистику\n"
        "• /start — запуск бота с начала\n\n"
        "Удачи в подготовке! 🚀"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 К тренировке", callback_data="go:train")],
        [InlineKeyboardButton(text="📝 К контрольной", callback_data="go:exam")]
    ])

    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

# --- Статистика ---
async def cmd_stats(event: Union[types.Message, types.CallbackQuery]):
    user = event.from_user
    user_id = user.id
    display_name = get_username(user)

    stats = await get_stats(user_id=user_id)
    train_done = stats.get("train_done", 0)
    exam_done = stats.get("exam_done", 0)

    text = (
        f"📊 *Статистика для {display_name}:*\n\n"
        f"• Тренировок пройдено: {train_done}\n"
        f"• Контрольных завершено: {exam_done}\n\n"
        "Продолжайте в том же духе! 💪"
    )

    if isinstance(event, types.Message):
        await event.answer(text, parse_mode="Markdown")
    else:
        await event.message.answer(text, parse_mode="Markdown")
        await event.answer()

# --- Обработка inline-кнопок ---
async def help_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "go:train":
        from handlers.train import cmd_train
        await cmd_train(callback.message, state)
    elif callback.data == "go:exam":
        from handlers.exam import cmd_exam
        await cmd_exam(callback.message, state)
    elif callback.data == "help:menu":
        await cmd_help(callback.message)
    elif callback.data == "stats:show":
        await cmd_stats(callback)
    else:
        await callback.answer("Неизвестный раздел.")

# --- Регистрация ---
def register_common(dp: Dispatcher):
    dp.message.register(cmd_help, Command(commands=["help"]))
    dp.message.register(cmd_help, F.text == "❓ Помощь")
    dp.message.register(cmd_stats, Command(commands=["stats"]))
    dp.message.register(cmd_stats, F.text == "📊 Статистика")
    dp.callback_query.register(help_callback, F.data.startswith("go:"))
    dp.callback_query.register(help_callback, F.data == "help:menu")
    dp.callback_query.register(help_callback, F.data == "stats:show")

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

async def handle_out_of_state(callback: CallbackQuery, state: FSMContext):
    await callback.answer(
        "⚠️ Сначала выберите режим: «Тренировка» или «Контрольная».\n\n"
        "Нажмите /start или одну из кнопок меню, чтобы начать заново.",
        show_alert=True
    )