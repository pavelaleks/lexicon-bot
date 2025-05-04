# services/tasks.py

import csv
import random
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Optional

from config import settings

# Путь к CSV-файлу с заданиями (колонки: Topic, Question, Answer)
TASKS_CSV = Path(settings.tasks_path)

@lru_cache(maxsize=1)
def _read_tasks() -> List[Dict[str, str]]:
    """
    Считывает все задания из CSV и кеширует результат.
    CSV должен содержать столбцы:
      - Topic    (название темы: Тире, Двоеточие, Кавычки, Запятая)
      - Question (текст задания, например номер и сам текст)
      - Answer   (правильные цифры через запятую, например "1,3")
    """
    with TASKS_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def get_tasks(topic: Optional[str] = None, count: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Возвращает список заданий.
    :param topic: если указана, фильтрует по теме (Topic)
    :param count: если указано, возвращает не более count заданий
    """
    tasks = _read_tasks()
    if topic:
        tasks = [t for t in tasks if t.get("Topic") == topic]
    random.shuffle(tasks)
    if count:
        return tasks[:count]
    return tasks

def get_unique_topics() -> List[str]:
    """
    Возвращает отсортированный список всех уникальных тем из файла.
    """
    tasks = _read_tasks()
    return sorted({t["Topic"] for t in tasks if t.get("Topic")})
