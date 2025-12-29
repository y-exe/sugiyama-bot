# services/image/gaming_gif.py
import io
import numpy as np
from PIL import Image

def create_gaming_gif(img_bytes: bytes, duration_ms: int = 50, max_size: tuple = (256, 256)) -> io.BytesIO | None:
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        # Image.LANCZOS に変更
        img.thumbnail(max_size, Image.LANCZOS)
        
        frames = []
        for i in range(36):
            h, s, v = img.convert("HSV").split()
            h_array = np.array(h, dtype=np.int16)
            shift_val = int((i * 10) * (255.0 / 360.0))
            shifted_h = Image.fromarray(np.mod(h_array + shift_val, 256).astype(np.uint8), 'L')
            frames.append(Image.merge("HSV", (shifted_h, s, v)).convert("RGBA"))
            
        buf = io.BytesIO()
        frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=duration_ms, loop=0, disposal=2, optimize=True)
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Error: {e}")
        return None