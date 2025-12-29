# data/points_manager.py
import json
import os
from core.config import POINTS_FILE, LOGIN_DATA_FILE

class PointsManager:
    def __init__(self):
        self.game_points = self._load_json(POINTS_FILE)
        self.login_bonus_data = self._load_json(LOGIN_DATA_FILE)

    def _load_json(self, path):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_all(self):
        with open(POINTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.game_points, f, indent=4, ensure_ascii=False)
        with open(LOGIN_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.login_bonus_data, f, indent=4, ensure_ascii=False)

    def get_points(self, user_id: int) -> int:
        return self.game_points.get(str(user_id), 0)

    def update_points(self, user_id: int, amount: int):
        uid_str = str(user_id)
        current = self.game_points.get(uid_str, 0)
        self.game_points[uid_str] = current + amount
        self.save_all()

    def get_rank(self, user_id: int, bot_id: int) -> int:
        # Botを除外したランキング計算
        human_players = {pid: p for pid, p in self.game_points.items() if int(pid) != bot_id}
        if str(user_id) not in human_players:
            return -1
        sorted_players = sorted(human_players.items(), key=lambda item: item[1], reverse=True)
        try:
            rank = [p[0] for p in sorted_players].index(str(user_id)) + 1
            return rank
        except ValueError:
            return -1

# インスタンスのエクスポート
points_manager = PointsManager()