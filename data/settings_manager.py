# data/settings_manager.py
import json
import os
from core.config import SETTINGS_FILE
from core.state import state

class SettingsManager:
    @staticmethod
    def load_settings():
        """JSONから許可されたチャンネルを読み込み、stateに反映する"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    state.allowed_channels = set(data.get("allowed_channels", []))
                    print(f"[Settings] {len(state.allowed_channels)} 個の許可チャンネルを読み込みました。")
            except Exception as e:
                print(f"[Settings] 設定の読み込み中にエラーが発生しました: {e}")
                state.allowed_channels = set()
        else:
            print("[Settings] 設定ファイルが見つかりません。新規作成の準備をします。")
            state.allowed_channels = set()

    @staticmethod
    def save_settings():
        """現在のstate.allowed_channelsをJSONファイルに保存する"""
        try:
            data = {"allowed_channels": list(state.allowed_channels)}
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("[Settings] 設定を JSON に保存しました。")
        except Exception as e:
            print(f"[Settings] 設定の保存中にエラーが発生しました: {e}")

settings_manager = SettingsManager()