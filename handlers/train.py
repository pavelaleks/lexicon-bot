import logging
from aiogram import types, Dispatcher, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as AIOButton

from services.tasks import get_tasks
from services.stats import get_stats, persist_stats
from handlers.common import cmd_help, cmd_stats, handle_out_of_state
from aiogram.filters import StateFilter

logger = logging.getLogger(__name__)

TOPICS = ["Тире", "Двоеточие", "Кавычки", "Запятая"]

class TrainStates(StatesGroup):
    choosing_topic = State()
    answering = State()
    awaiting_next = State()

def topics_kb_inline() -> InlineKeyboardMarkup:
    keyboard = [[AIOButton(text=t, callback_data=f"topic:{t}")] for t in TOPICS]
    keyboard.append([
        AIOButton(text="📊 Статистика", callback_data="stats:show")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def post_train_kb_inline() -> InlineKeyboardMarkup:
    keyboard = [
        [AIOButton(text="➡️ Следующее", callback_data="train:next")],
        [AIOButton(text="📊 Статистика", callback_data="stats:show")],
        [AIOButton(text="❓ Помощь", callback_data="help:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def cmd_train(message: types.Message, state: FSMContext):
    await state.clear()
    user_name = message.from_user.full_name or message.from_user.username or "ученик"
    await message.answer(f"🎯 {user_name}, выберите тему для тренировки Задания 5 ОГЭ:", reply_markup=topics_kb_inline())
    await state.set_state(TrainStates.choosing_topic)

async def handle_topic_callback(callback: types.CallbackQuery, state: FSMContext):
    topic = callback.data.split(":", 1)[1]
    tasks = get_tasks(topic=topic)
    if not tasks:
        await callback.message.edit_text("По этой теме нет заданий.", reply_markup=topics_kb_inline())
        return

    await state.update_data(tasks=tasks, index=0, topic=topic, selected=[])
    await _send_question(callback.message, state)
    await callback.answer()

async def _send_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    idx = data["index"] + 1
    total = len(data["tasks"])
    task = data["tasks"][data["index"]]

    text = (
        f"*Задание 5*. Тема: {data['topic']} ({idx}/{total})\n\n"
        f"_Нажмите цифры, где должен стоять нужный пунктуационный знак._\n\n"
        f"{task['Question'].strip()}"
    )

    buttons = [AIOButton(text=str(i), callback_data=f"num:{i}") for i in range(1, 11)]
    rows = [buttons[i:i + 5] for i in range(0, 10, 5)]
    rows.append([AIOButton(text="✅ Проверить", callback_data="check")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await state.set_state(TrainStates.answering)
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

async def handle_num(callback: types.CallbackQuery, state: FSMContext):
    if not await state.get_state() == TrainStates.answering:
        await callback.answer("Сначала выберите тему и задание.", show_alert=True)
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

async def handle_check(callback: types.CallbackQuery, state: FSMContext):
    if not await state.get_state() == TrainStates.answering:
        await callback.answer("Сначала выберите задание.", show_alert=True)
        return

    data = await state.get_data()
    selected = set(data.get("selected", []))
    correct = set(map(str.strip, data["tasks"][data["index"]]["Answer"].split(",")))

    if sorted(selected) == sorted(correct):
        result = "✅ *Правильно!*"
    else:
        result = f"❌ *Неверно.*\nПравильный ответ: `{', '.join(sorted(correct))}`"

    user_id = callback.from_user.id
    stats = await get_stats(user_id)
    stats["train_done"] = stats.get("train_done", 0) + 1
    await persist_stats(stats, user_id)

    await callback.message.answer(result, parse_mode="Markdown", reply_markup=post_train_kb_inline())
    await state.set_state(TrainStates.awaiting_next)
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

async def handle_posttrain_callback(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    action = callback.data.split(":", 1)[1]

    if action == "next":
        new_idx = data["index"] + 1
        if new_idx < len(data["tasks"]):
            await state.update_data(index=new_idx, selected=[])
            await _send_question(callback.message, state)
        else:
            await callback.message.answer("❗️ Задания на тему закончились. Выберите другую тему.", reply_markup=topics_kb_inline())
            await state.set_state(TrainStates.choosing_topic)

    await callback.answer()

async def stats_callback(callback: types.CallbackQuery):
    await cmd_stats(callback.message)
    await callback.answer()

def register_train(dp: Dispatcher):
    dp.message.register(cmd_train, Command(commands=["train"]))
    dp.message.register(cmd_train, F.text == "🎯 Тренировка")
    dp.callback_query.register(handle_topic_callback, F.data.startswith("topic:"))
    dp.callback_query.register(handle_num, F.data.startswith("num:"), TrainStates.answering)
    dp.callback_query.register(handle_check, F.data == "check", TrainStates.answering)
    dp.callback_query.register(handle_posttrain_callback, F.data.startswith("train:"))
    dp.callback_query.register(stats_callback, F.data == "stats:show")

    # Перехват некорректных нажатий вне нужного состояния
    dp.callback_query.register(handle_out_of_state, F.data.startswith("num:"), StateFilter(None))
    dp.callback_query.register(handle_out_of_state, F.data == "check", StateFilter(None))
