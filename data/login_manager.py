# data/login_manager.py
import json
import os
import datetime
from core.config import LOGIN_DATA_FILE, JST

class LoginManager:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(LOGIN_DATA_FILE):
            try:
                with open(LOGIN_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def save(self):
        with open(LOGIN_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def check_and_get_bonus(self, user_id: int, rank: int) -> dict:
        uid = str(user_id)
        now = datetime.datetime.now(JST)
        today_str = now.strftime("%Y-%m-%d")
        
        user_info = self.data.get(uid, {"last_login": "2000-01-01", "consecutive_days": 0})
        if user_info.get("last_login") == today_str:
            return None

        # 日数計算
        last_date = datetime.datetime.strptime(user_info["last_login"], "%Y-%m-%d").date()
        if last_date == now.date() - datetime.timedelta(days=1):
            consecutive = (user_info["consecutive_days"] % 10) + 1
        else:
            consecutive = 1

        # 元の計算式
        base = 30
        rank_bonus = 30 if rank == 1 else 20 if 2 <= rank <= 3 else 10 if 4 <= rank <= 10 else 0
        con_bonus = (consecutive - 1) * 10
        total = max(30, base + rank_bonus + con_bonus)

        self.data[uid] = {"last_login": today_str, "consecutive_days": consecutive}
        self.save()
        return {"points": total, "days": consecutive}

login_manager = LoginManager()