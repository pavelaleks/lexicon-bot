import json
import os
from typing import Dict

STATS_FILE = "stats.json"

def _load_data():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

async def get_stats(user_id: int = None) -> Dict:
    data = _load_data()

    if user_id is None:
        return data.get("global", {})

    return data.get("users", {}).get(str(user_id), {})

async def persist_stats(stats: Dict, user_id: int = None) -> None:
    data = _load_data()

    if user_id is None:
        data["global"] = stats
    else:
        if "users" not in data:
            data["users"] = {}
        data["users"][str(user_id)] = stats

    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
