# services/network/exchange_api.py
import aiohttp
from core.config import EXCHANGE_RATE_API_URL

async def get_exchange_rates():
    """最新の為替レートを取得する"""
    async with aiohttp.ClientSession() as session:
        async with session.get(EXCHANGE_RATE_API_URL) as response:
            if response.status == 200:
                return await response.json()
            return None