import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, Chat
from datetime import datetime
from handlers.exam import cmd_exam, ExamStates

class DummyMessage:
    def __init__(self, user_id=123, full_name="Тестовый"):
        self.from_user = User(id=user_id, is_bot=False, first_name=full_name)
        self.chat = Chat(id=user_id, type="private")
        self.text = "/exam"
        self.date = datetime.now()

    async def answer(self, text, **kwargs):
        print("Exam запущен:", text)

@pytest.mark.asyncio
async def test_cmd_exam_sets_correct_state():
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=("user", 123))

    message = DummyMessage()
    await cmd_exam(message, state)

    current = await state.get_state()
    assert current == ExamStates.choosing.state