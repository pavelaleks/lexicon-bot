import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User

from handlers.exam import _finish_exam, ExamStates


class DummyMessage:
    async def answer(self, text, parse_mode=None):
        print("БОТ:", text)


class DummyCallback:
    def __init__(self):
        self.from_user = User(id=123, is_bot=False, first_name="Тест")
        self.message = DummyMessage()


@pytest.mark.asyncio
async def test_finish_exam_shows_mistakes(capsys):
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=("user", 123))

    tasks = [
        {"Question": "Q1", "Answer": "1", "Topic": "Тире"},
        {"Question": "Q2", "Answer": "2", "Topic": "Запятая"},
    ]
    answers = [set(["1"]), set(["3"])]  # Один правильный, один — ошибка
    deadline = 9999999999

    await state.update_data(tasks=tasks, answers=answers, deadline=deadline)
    cb = DummyCallback()
    await _finish_exam(cb, state)

    captured = capsys.readouterr()
    assert "Ошибки были в темах" in captured.out
    assert "Запятая" in captured.out
