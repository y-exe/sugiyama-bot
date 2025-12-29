# services/image/choyen.py
import urllib.parse

def get_5000choyen_url(top_text: str, bottom_text: str, hoshii: bool = False, rainbow: bool = False) -> str:
    """5000兆円ジェネレーターAPIのURLを生成する"""
    params = {
        "top": top_text,
        "bottom": bottom_text,
        "hoshii": "true" if hoshii else "false",
        "rainbow": "true" if rainbow else "false"
    }
    query = urllib.parse.urlencode(params)
    return f"https://gsapi.cbrx.io/image?{query}"