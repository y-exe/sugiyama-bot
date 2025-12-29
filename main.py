# main.py
import sys
import asyncio
from bot import bot
from core.config import DISCORD_BOT_TOKEN
from core.state import state
from data.settings_manager import settings_manager
from data.points_manager import points_manager
from services.network.weather_api import fetch_weather_city_codes

async def start_up():
    print("[System]startup")
    
    settings_manager.load_settings()

    p_count = len(points_manager.game_points)
    
    state.weather_city_id_map = await fetch_weather_city_codes()
    
    
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("エラー: .env ファイルに DISCORD_BOT_TOKEN が設定されていません。")
        sys.exit(1)
    
    try:
        asyncio.run(start_up())
    except KeyboardInterrupt:
        print("\n[System]stopped")
    except Exception as e:
        print(f"致命的なエラーが発生しました: {e}")