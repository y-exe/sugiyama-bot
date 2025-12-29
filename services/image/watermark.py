# services/image/watermark.py
import io
import os
from PIL import Image, ImageOps
from core.config import TEMPLATES_DIR

def process_and_composite_image(img_bytes: bytes, tmpl_data: dict) -> io.BytesIO | None:
    try:
        base_image = Image.open(io.BytesIO(img_bytes))
        target_w, target_h = tmpl_data['target_size']
        
        # Image.LANCZOS に変更
        processed = ImageOps.fit(base_image, (target_w, target_h), Image.LANCZOS)
        
        overlay_path = os.path.join(TEMPLATES_DIR, tmpl_data['name'])
        if not os.path.exists(overlay_path):
            return None
            
        overlay = Image.open(overlay_path).convert("RGBA")
        
        if overlay.size != (target_w, target_h):
            # Image.LANCZOS に変更
            overlay = overlay.resize((target_w, target_h), Image.LANCZOS)
            
        if processed.mode != 'RGBA':
            processed = processed.convert('RGBA')
            
        final = Image.alpha_composite(processed, overlay)
        
        buf = io.BytesIO()
        final.save(buf, "PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Error: {e}")
        return None