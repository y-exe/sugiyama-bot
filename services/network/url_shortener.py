# services/network/url_shortener.py
import aiohttp
import urllib.parse
from core.config import AMAZON_SHORTURL_ENDPOINT

async def shorten_amazon_url(long_url: str):
    """Amazon Associates APIを利用して短縮URLを生成する"""
    parsed = urllib.parse.urlparse(long_url)
    # marketplace_id: 6は日本
    m_id = "6" if "amazon.co.jp" in parsed.netloc else "1"
    params = {
        "longUrl": urllib.parse.quote_plus(long_url),
        "marketplaceId": m_id
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{AMAZON_SHORTURL_ENDPOINT}?{urllib.parse.urlencode(params, safe='/:')}", headers=headers) as response:
            if response.status == 200:
                return await response.json()
            return None