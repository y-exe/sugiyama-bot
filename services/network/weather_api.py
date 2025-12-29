# services/network/weather_api.py
import aiohttp
import xml.etree.ElementTree as ET
import json
import os
from core.config import WEATHER_API_BASE_URL, PRIMARY_AREA_XML_URL, CITY_CODES_FILE
from services.ai.deepseek import generate_deepseek_text_response

async def fetch_weather_city_codes():
    """つくもAPIから日本の全都市コードを取得し、マップを作成する"""
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
                                # 「東京都東京」のように県名＋市名でも引けるようにする
                                if pref_title and pref_title != city_title:
                                    temp_map[f"{pref_title}{city_title}"] = city_id
                    
                    # キャッシュ保存
                    with open(CITY_CODES_FILE, 'w', encoding='utf-8') as f:
                        json.dump(temp_map, f, ensure_ascii=False, indent=2)
                        
    except Exception as e:
        print(f"Error fetching city codes: {e}")
    return temp_map

async def get_city_id_fuzzy(city_name_query: str, city_id_map: dict) -> str | None:
    """地名からIDを取得。見つからない場合はDeepSeekに推論させる"""
    # 完全一致・小文字一致チェック
    query = city_name_query.lower()
    for name, cid in city_id_map.items():
        if query == name.lower():
            return cid

    # DeepSeekによる補完 (API利用可能な場合)
    # 上限150件に絞ってリストを提供
    city_list_excerpt = "\n".join([f"- {name} (ID: {cid})" for name, cid in list(city_id_map.items())[:150]])
    prompt = (f"日本の地名「{city_name_query}」に最も近いと思われる都市のIDを、以下のリストから一つだけ選んで、そのID（数字6桁）のみを返してください。例 : 博多 → 400010\n"
              f"余計な説明は不要です。数字のみを回答してください。同じ名前の都市名が違うIDの場所にある場合は有名な方返してください\n"
              f"リストに適切なIDがない場合は「不明」と返してください。\n\n"
              f"リスト:\n{city_list_excerpt}\n\n"
              f"地名: {city_name_query}\nID:")
    
    response = await generate_deepseek_text_response(prompt, temperature=0.1)
    clean_id = response.strip()
    if clean_id.isdigit() and any(cid == clean_id for cid in city_id_map.values()):
        return clean_id
    
    return None

async def get_weather_forecast(city_id: str):
    """指定されたIDの天気予報を取得する"""
    url = f"{WEATHER_API_BASE_URL}{city_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None