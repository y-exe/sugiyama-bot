# core/state.py
from collections import deque

class GlobalState:
    def __init__(self):
        # 進行中のゲーム管理
        self.active_games = {}                # オセロ用
        self.active_janken_games = {}        # じゃんけん用
        self.active_connectfour_games = {}   # 四目並べ用
        self.active_highlow_games = {}       # ハイロー用
        
        # 設定データ
        self.allowed_channels = set()
        self.weather_city_id_map = {}
        
        # レートリミット
        self.imakita_request_timestamps = deque()

# インスタンスのエクスポート
state = GlobalState()