#!/usr/bin/env python3
# scripts/update_tasks_from_yandex.py

import os
import csv
import requests
from pathlib import Path

# -------------------------------------------------------------------
# Настройте:
# 1) Скопируйте ссылку на экспорт вашей Яндекс-таблицы в CSV (см. ниже)
# 2) Задайте эту ссылку в переменной окружения YANDEX_CSV_URL
# -------------------------------------------------------------------
YANDEX_CSV_URL = os.getenv("YANDEX_CSV_URL")

if not YANDEX_CSV_URL:
    print("❌ Пожалуйста, задайте URL таблицы через переменную YANDEX_CSV_URL")
    print("   export YANDEX_CSV_URL='https://docs.yandex.ru/spreadsheets/export?format=csv&table=...'")
    exit(1)

def fetch_remote_csv(url: str) -> list[str]:
    """
    Скачивает CSV и возвращает список строк.
    """
    resp = requests.get(url)
    resp.raise_for_status()
    text = resp.text
    # Разбираем по строкам, сохраняя переносы
    return text.splitlines()

def build_tasks_csv(lines: list[str], out_path: Path):
    """
    Парсит входной CSV и записывает только три колонки: Topic,Question,Answer
    """
    reader = csv.DictReader(lines)
    expected = {"Topic", "Question", "Answer"}
    if set(reader.fieldnames or []) != expected:
        raise ValueError(
            f"Ожидались колонки {expected}, а пришли {reader.fieldnames}"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        # Шапка
        writer.writerow(["Topic", "Question", "Answer"])
        for row in reader:
            topic    = row["Topic"].strip()
            question = row["Question"].strip()
            answer   = row["Answer"].strip()
            if topic and question and answer:
                writer.writerow([topic, question, answer])

    print(f"✅ Обновлён {out_path}")

def main():
    print("🔄 Загружаем CSV из Яндекс-таблицы…")
    lines = fetch_remote_csv(YANDEX_CSV_URL)
    build_tasks_csv(lines, Path("data/tasks.csv"))

if __name__ == "__main__":
    main()
