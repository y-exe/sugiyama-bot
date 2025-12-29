# services/image/base_worker.py
import io
import math
import os
import asyncio
import subprocess
from PIL import Image
from core.config import MAX_FILE_SIZE, WAIFU2X_PATH

async def resize_if_too_large(image_fp: io.BytesIO, target_format: str) -> tuple[io.BytesIO, bool]:
    """Pillowのバージョンに依存しない形式に修正"""
    image_fp.seek(0, io.SEEK_END)
    current_size = image_fp.tell()
    image_fp.seek(0)
    
    if current_size <= MAX_FILE_SIZE:
        return image_fp, False

    current_fp = image_fp
    resized = False
    min_dim = 300
    
    for iteration in range(7):
        current_fp.seek(0)
        img = Image.open(current_fp)
        w, h = img.width, img.height
        if min(w, h) <= min_dim: break

        current_fp.seek(0, io.SEEK_END)
        iter_size = current_fp.tell()
        
        factor = 0.85
        if iteration == 0:
            factor = max(0.1, min(math.sqrt(MAX_FILE_SIZE / iter_size) * 0.9, 0.95))
        
        new_w, new_h = int(w * factor), int(h * factor)
        output_fp = io.BytesIO()

        if target_format.upper() == 'GIF':
            frames = []
            durations = []
            loop = img.info.get('loop', 0)
            try:
                while True:
                    frame = img.copy().convert("RGBA")
                    # Image.LANCZOS に変更
                    frame.thumbnail((new_w, new_h), Image.LANCZOS)
                    frames.append(frame)
                    durations.append(img.info.get('duration', 100))
                    img.seek(img.tell() + 1)
            except EOFError: pass
            frames[0].save(output_fp, format="GIF", save_all=True, append_images=frames[1:], duration=durations, loop=loop, disposal=2, optimize=True)
        else:
            resized_img = img.copy()
            # Image.LANCZOS に変更
            resized_img.thumbnail((new_w, new_h), Image.LANCZOS)
            params = {'optimize': True}
            if target_format.upper() == 'JPEG': params['quality'] = 85
            elif target_format.upper() == 'PNG': params['compress_level'] = 7
            resized_img.save(output_fp, format=target_format.upper(), **params)

        output_fp.seek(0, io.SEEK_END)
        if output_fp.tell() <= MAX_FILE_SIZE:
            return output_fp, True
        
        current_fp = output_fp
        resized = True

    return current_fp, resized

async def run_waifu2x(input_path: str, output_path: str) -> bool:
    if not WAIFU2X_PATH or not os.path.exists(WAIFU2X_PATH):
        return False
    command = [WAIFU2X_PATH, "-i", input_path, "-o", output_path, "-m", "noise_scale", "-n", "1", "-s", "2.0"]
    process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.communicate()
    return process.returncode == 0