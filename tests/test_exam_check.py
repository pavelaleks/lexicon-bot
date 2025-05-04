import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User
from handlers.exam import handle_exam_check, ExamStates

class DummyMessage:
    def __init__(self):
        self.from_user = User(id=123, is_bot=False, first_name="Тест")
        self.chat = type("Chat", (), {"id": 123, "type": "private"})()

    async def answer(self, text, **kwargs):
        print("Ответ бота:", text)

class DummyCallback:
    def __init__(self, data="check"):
        self.data = data
        self.from_user = User(id=123, is_bot=False, first_name="Тест")
        self.message = DummyMessage()

    async def answer(self, text=None, show_alert=False):
        print("ALERT:", text)

@pytest.mark.asyncio
async def test_handle_exam_check_correct_and_incorrect(capsys):
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=("user", 123))

    tasks = [{"Question": "Пунктуация?", "Answer": "1", "Topic": "Тире"}]
    cb = DummyCallback()

    # ✅ Корректный ответ
    await state.update_data(tasks=tasks, index=0, selected=["1"], answers=[], deadline=9999999999)
    await state.set_state(ExamStates.answering)
    await handle_exam_check(cb, state)
    captured = capsys.readouterr()
    assert "Правильно" in captured.out or "✅" in captured.out

    # ❌ Некорректный ответ
    await state.update_data(tasks=tasks, index=0, selected=["2"], answers=[], deadline=9999999999)
    await state.set_state(ExamStates.answering)  # 💡 нужно вернуть состояние обратно
    await handle_exam_check(cb, state)
    captured = capsys.readouterr()
    assert "Неверно" in captured.out or "❌" in captured.out
