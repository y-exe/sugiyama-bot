# services/ai/voicevox.py
import aiohttp
import io
from core.config import VOICEVOX_API_KEY, VOICEVOX_API_BASE_URL

async def generate_voicevox_audio(text: str, speaker_id: int) -> io.BytesIO | None:
    """VoiceVox APIを叩いてwavデータのストリームを返す"""
    if not VOICEVOX_API_KEY or VOICEVOX_API_KEY == "YOUR_VOICEVOX_API_KEY_PLACEHOLDER":
        print("VoiceVox API key is not set.")
        return None

    params = {
        "text": text,
        "speaker": str(speaker_id),
        "key": VOICEVOX_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(VOICEVOX_API_BASE_URL, params=params, timeout=60) as resp:
                if resp.status == 200 and resp.content_type in ('audio/wav', 'audio/x-wav'):
                    data = await resp.read()
                    return io.BytesIO(data)
                else:
                    print(f"VoiceVox API Failed: Status {resp.status}")
                    return None
    except Exception as e:
        print(f"VoiceVox Request Error: {e}")
        return None