# handlers/__init__.py

from .common import register_common
from .train import register_train
from .exam import register_exam

__all__ = ["register_handlers"]

def register_handlers(dp):
    """
    Регистрирует все хэндлеры в диспетчере dp
    """
    register_common(dp)
    register_train(dp)
    register_exam(dp)
