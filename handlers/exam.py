import logging
import time
import re

from aiogram import types, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as AIOButton

from services.tasks import get_tasks
from services.stats import get_stats, persist_stats
from handlers.common import cmd_stats, cmd_help, handle_out_of_state

logger = logging.getLogger(__name__)

class ExamStates(StatesGroup):
    choosing = State()
    answering = State()
    awaiting_next = State()

EXAM_OPTIONS = {
    "5 заданий": 5 * 60,
    "10 заданий": 8 * 60,
    "20 заданий": 15 * 60,
    "50 заданий": 30 * 60,
}

def exam_kb_inline() -> InlineKeyboardMarkup:
    keyboard = [
        [AIOButton(text=opt, callback_data=f"exam_start:{opt}")] for opt in EXAM_OPTIONS.keys()
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def post_exam_kb_inline() -> InlineKeyboardMarkup:
    keyboard = [
        [AIOButton(text="🔁 Повторить контрольную", callback_data="go:exam")],
        [AIOButton(text="🎯 К тренировке", callback_data="go:train")],
        [AIOButton(text="📊 Статистика", callback_data="stats:show"),
         AIOButton(text="❓ Помощь", callback_data="help:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def number_kb_inline() -> InlineKeyboardMarkup:
    buttons = [AIOButton(text=str(i), callback_data=f"num:{i}") for i in range(1, 11)]
    rows = [buttons[i:i + 5] for i in range(0, 10, 5)]
    rows.append([AIOButton(text="✅ Проверить", callback_data="check")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def escape_md_user_input(text: str) -> str:
    """
    Экранирует только пользовательский ввод, безопасно для Markdown
    """
    return re.sub(r'([\\*_`\[\]()~>#+\-=|{}.!])', r'\\\1', text)

async def cmd_exam(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"📝 {message.from_user.full_name or message.from_user.username}, выберите количество заданий:",
        reply_markup=exam_kb_inline()
    )
    await state.set_state(ExamStates.choosing)

async def handle_exam_choice(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split(":", 1)[1]
    count = int(choice.split()[0])
    tasks = get_tasks(count=count)
    if not tasks:
        await callback.message.edit_text("Не удалось загрузить задания.")
        return

    deadline = time.time() + EXAM_OPTIONS[choice]
    await state.update_data(tasks=tasks, index=0, answers=[], deadline=deadline, selected=[])
    await _send_question(callback.message, state)
    await callback.answer()

async def _send_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    idx = data["index"] + 1
    total = len(data["tasks"])
    task = data["tasks"][data["index"]]
    topic = task.get("Topic", "Тема не указана")

    now = time.time()
    remaining = max(0, int(data["deadline"] - now))
    minutes, seconds = divmod(remaining, 60)
    timer_str = f"{minutes:02}:{seconds:02}"

    text = (
        f"📝 Контрольная: задание {idx}/{total}\n"
        f"📚 Тема: {topic}\n"
        f"⏳ Осталось времени: {timer_str}\n\n"
        "Укажите номера позиций, где должен стоять знак препинания:\n\n"
        f"{task['Question']}"
    )

    await state.set_state(ExamStates.answering)
    await message.answer(text, reply_markup=number_kb_inline())

async def handle_exam_num(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state != ExamStates.answering.state:
        await callback.answer("Сначала выберите задание.", show_alert=True)
        return

    num = callback.data.split(":", 1)[1]
    data = await state.get_data()
    sel = set(data.get("selected", []))
    if num in sel:
        sel.remove(num)
    else:
        sel.add(num)
    await state.update_data(selected=list(sel))
    try:
        await callback.answer(f"Выбрано: {', '.join(sorted(sel)) or 'ничего'}")
    except TelegramBadRequest:
        pass

async def handle_exam_check(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state != ExamStates.answering.state:
        await callback.answer("Сначала выберите задание.", show_alert=True)
        return

    data = await state.get_data()
    selected = set(data.get("selected", []))
    correct = set(map(str.strip, data["tasks"][data["index"]]["Answer"].split(",")))

    if sorted(selected) == sorted(correct):
        result = "✅ *Правильно!*"
    else:
        result = f"❌ *Неверно.*\nПравильный ответ: `{', '.join(sorted(correct))}`"

    answers = data.get("answers", [])
    answers.append(selected)
    await state.update_data(answers=answers)

    await callback.message.answer(result, parse_mode="Markdown")

    new_idx = data["index"] + 1
    if new_idx < len(data["tasks"]):
        await state.update_data(index=new_idx, selected=[])
        await _send_question(callback.message, state)
    else:
        await _finish_exam(callback, state)

    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

async def _finish_exam(callback: types.CallbackQuery, state: FSMContext, timed_out: bool = False):
    user = callback.from_user
    message = callback.message

    user_id = user.id
    name = escape_md_user_input(user.full_name or user.username or "Ученик")

    data = await state.get_data()
    tasks = data["tasks"]
    answers = data.get("answers", [])
    total = len(tasks)
    correct_count = 0
    incorrect_topics = []

    for task, user_set in zip(tasks, answers):
        correct_set = set(map(str.strip, task["Answer"].split(",")))
        if user_set == correct_set:
            correct_count += 1
        else:
            topic = task.get("Topic", "Тема не указана")
            incorrect_topics.append(topic)

    stats = await get_stats(user_id)
    stats["exam_done"] = stats.get("exam_done", 0) + 1
    await persist_stats(stats, user_id)

    score = int((correct_count / total) * 100)
    grade = "✅ Отлично!" if score >= 90 else "👍 Хорошо!" if score >= 70 else "📚 Надо ещё потренироваться."

    now = time.time()
    total_time = int(now - (data.get("deadline", now) - EXAM_OPTIONS.get(f"{total} заданий", 0)))
    minutes, seconds = divmod(total_time, 60)
    time_str = f"{minutes} мин {seconds} сек"

    note = "⏳ Вы не уложились во время.\n" if timed_out else ""

    mistake_block = ""
    if incorrect_topics:
        topics_list = ", ".join(sorted(set(incorrect_topics)))
        topics_list = escape_md_user_input(topics_list)
        mistake_block = (
            f"\n❗ Ошибки были в темах: {topics_list}.\n"
            f"👉 Рекомендуем потренироваться с этими темами в режиме /train."
        )

    text = (
        f"📝 *Контрольная завершена!*\n"
        f"{note}{name}, ваш результат: *{correct_count} из {total}* ({score}%)\n"
        f"⏱ Затраченное время: {time_str}\n"
        f"{grade}{mistake_block}"
    )

    await message.answer(text, parse_mode="Markdown")
    await state.set_state(ExamStates.awaiting_next)

async def stats_callback(callback: types.CallbackQuery):
    await cmd_stats(callback)
    await callback.answer()

def register_exam(dp: Dispatcher):
    dp.message.register(cmd_exam, Command(commands=["exam"]))
    dp.message.register(cmd_exam, F.text == "📝 Контрольная")

    dp.callback_query.register(handle_exam_choice, F.data.startswith("exam_start:"))
    dp.callback_query.register(handle_exam_num, F.data.startswith("num:"), ExamStates.answering)
    dp.callback_query.register(handle_exam_check, F.data == "check", ExamStates.answering)

    dp.callback_query.register(cmd_stats, F.data == "stats:show")
    dp.callback_query.register(handle_out_of_state, F.data.startswith("num:"), StateFilter(None))
    dp.callback_query.register(handle_out_of_state, F.data == "check", StateFilter(None))
