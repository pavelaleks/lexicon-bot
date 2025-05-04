import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, CallbackQuery
from datetime import datetime
from handlers.train import handle_num, TrainStates

class DummyCallback:
    def __init__(self, data="num:1", user_id=123):
        self.data = data
        self.from_user = User(id=user_id, is_bot=False, first_name="Test")
        self.message = None

    async def answer(self, text=None, show_alert=False):
        print("Ответ callback:", text)

@pytest.mark.asyncio
async def test_handle_num_outside_of_answering_state(capsys):
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=("user", 123))
    await state.set_state(TrainStates.choosing_topic)  # не answering

    cb = DummyCallback()
    await handle_num(cb, state)

    captured = capsys.readouterr()
    assert "Сначала выберите тему" in captured.out