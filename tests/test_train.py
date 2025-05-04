# tests/test_train.py

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, Chat, Message
from datetime import datetime
from handlers.train import cmd_train, TrainStates

class DummyMessage:
    """Мок сообщения для симуляции пользователя"""
    def __init__(self, user_id=123, full_name="Тестовый Пользователь", text="/train"):
        self.from_user = User(id=user_id, is_bot=False, first_name=full_name, last_name=None, username=None)
        self.chat = Chat(id=user_id, type="private")
        self.text = text
        self.date = datetime.now()

    async def answer(self, text, **kwargs):
        print("Бот ответил:", text)

@pytest.mark.asyncio
async def test_cmd_train_sets_correct_state():
    # Инициализация FSM
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=("user", 123))

    message = DummyMessage()
    await cmd_train(message, state)

    current_state = await state.get_state()
    assert current_state == TrainStates.choosing_topic.state
