# scripts/xlsx_to_csv.py
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
XLSX = BASE_DIR / "data" / "tasks.xlsx"
CSV  = BASE_DIR / "data" / "tasks.csv"

def main():
    df = pd.read_excel(XLSX, engine="openpyxl", dtype={"Answer": str})
    df = df[["Topic", "Question", "Answer"]]
    df.to_csv(CSV, index=False, encoding="utf-8")
    print("✅ Сконвертировано:", CSV)

if __name__ == "__main__":
    main()
