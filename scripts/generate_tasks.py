# scripts/generate_tasks.py

import csv
import re
from pathlib import Path

# Пути к файлам
BASE_DIR = Path(__file__).parent.parent
ORIG_CSV = BASE_DIR / 'data' / 'punctuation_examples_fixed.csv'
OUT_CSV  = BASE_DIR / 'data' / 'tasks.csv'

# Наши «целевые» знаки
PUNCTUATION_LIST = [',', ':', '—']
PUNCTUATION      = set(PUNCTUATION_LIST)
# Для фильтрации строк без ни одного нужного знака
pattern = re.compile(r"[{}]".format("".join(re.escape(p) for p in PUNCTUATION_LIST)))


def compute_insert_positions_and_text(answer: str) -> tuple[str, list[int]]:
    """
    Возвращает:
      - clean_text: исходная строка без запятых, двоеточий и тире,
        причём все пробелы коллапсируются и нет ведущих/концевых пробелов.
      - positions: список индексов в clean_text, куда надо вставлять
        по порядку те самые знаки.
    """
    clean_chars = []
    positions   = []

    for ch in answer:
        if ch in PUNCTUATION:
            # запоминаем текущую длину clean_chars как позицию для вставки
            positions.append(len(clean_chars))
        elif ch.isspace():
            # добавляем ровно один пробел, если до этого не стоял пробел
            if clean_chars and clean_chars[-1] != ' ':
                clean_chars.append(' ')
        else:
            clean_chars.append(ch)

    # убираем завершающий пробел, если он есть
    if clean_chars and clean_chars[-1] == ' ':
        clean_chars.pop()

    clean_text = "".join(clean_chars)
    return clean_text, positions


def generate_tasks():
    ORIG_CSV.parent.mkdir(parents=True, exist_ok=True)

    with ORIG_CSV.open('r', encoding='utf-8') as fin, \
         OUT_CSV.open('w', encoding='utf-8', newline='') as fout:

        reader = csv.DictReader(fin)
        fieldnames = ['ID', 'Topic', 'Text', 'InsertPositions', 'Answer', 'Explanation']
        writer = csv.DictWriter(fout, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for idx, raw in enumerate(reader, start=1):
            answer      = raw.get('Text',        '').strip()
            explanation = raw.get('Explanation', '').strip()
            topic       = raw.get('Topic',       '').strip()

            # пропускаем полностью пустые строки
            if not (answer and explanation and topic):
                print(f"⚠️ Пропущена строка (что-то пустое): {raw}")
                continue

            # пропускаем примеры без ни одного нашего знака
            if not pattern.search(answer):
                print(f"⚠️ Нет нужных знаков: {answer}")
                continue

            text, positions = compute_insert_positions_and_text(answer)

            writer.writerow({
                'ID':              idx,
                'Topic':           topic,
                'Text':            text,
                'InsertPositions': ",".join(map(str, positions)),
                'Answer':          answer,
                'Explanation':     explanation,
            })

    print(f"\n✅ Задачи успешно сгенерированы: {OUT_CSV}")


if __name__ == '__main__':
    generate_tasks()
