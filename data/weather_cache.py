# data/weather_cache.py
import json
import os
import aiohttp
import xml.etree.ElementTree as ET
from core.config import CITY_CODES_FILE, PRIMARY_AREA_XML_URL

class WeatherCache:
    @staticmethod
    def load_local():
        """ローカルのJSONから都市コードを読み込む"""
        if os.path.exists(CITY_CODES_FILE):
            try:
                with open(CITY_CODES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @staticmethod
    async def update_from_api():
        """つくもAPIのXMLから最新の都市情報を取得して保存する"""
        temp_map = {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PRIMARY_AREA_XML_URL) as response:
                    if response.status == 200:
                        xml_text = await response.text()
                        root = ET.fromstring(xml_text)
                        for pref in root.findall('.//pref'):
                            pref_title = pref.get('title')
                            for city in pref.findall('.//city'):
                                city_title = city.get('title')
                                city_id = city.get('id')
                                if city_title and city_id:
                                    temp_map[city_title] = city_id
                                    if pref_title and pref_title != city_title:
                                        temp_map[f"{pref_title}{city_title}"] = city_id
                        
                        # ファイルに保存
                        with open(CITY_CODES_FILE, 'w', encoding='utf-8') as f:
                            json.dump(temp_map, f, ensure_ascii=False, indent=2)
                        return temp_map
        except Exception as e:
            print(f"Weather Update Error: {e}")
        return temp_map