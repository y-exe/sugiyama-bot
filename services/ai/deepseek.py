# services/ai/deepseek.py
import aiohttp
import json
from core.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

async def generate_deepseek_text_response(prompt_content: str, temperature: float = 1.0) -> str:
    """DeepSeek APIを使用してテキストを生成する共通関数"""
    if not DEEPSEEK_API_KEY:
        return "Error: DeepSeek API key is not configured."

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "あなたは役に立つ日本語のアシスタントです。"},
            {"role": "user", "content": prompt_content}
        ],
        "temperature": temperature,
        "stream": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DEEPSEEK_BASE_URL, json=payload, headers=headers, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    return f"DeepSeek API Error: {response.status} - {error_text}"
    except Exception as e:
        return f"DeepSeek Connection Error: {e}"

async def generate_summary_with_ai(text: str, num_points: int = 3) -> str:
    """文章を箇条書きで要約する"""
    prompt = f"以下の文章を日本語で{num_points}個の短い箇条書きに要約してください:\n\n{text}"
    return await generate_deepseek_text_response(prompt)