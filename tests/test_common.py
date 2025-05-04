import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, User
from handlers.common import handle_out_of_state

class DummyCallback:
    def __init__(self):
        self.data = "num:1"
        self.from_user = User(id=123, is_bot=False, first_name="User")
        self.message = None

    async def answer(self, text=None, show_alert=False):
        print("ALERT:", text)
        self.alert_text = text

@pytest.mark.asyncio
async def test_handle_out_of_state_shows_warning(capsys):
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=("user", 123))
    cb = DummyCallback()
    await handle_out_of_state(cb, state)
    captured = capsys.readouterr()
    assert "Сначала выберите режим" in captured.out