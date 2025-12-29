# services/image/text_special.py
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import numpy as np

def generate_text4_hd(text: str, font_path: str):
    scale = 4
    font = ImageFont.truetype(font_path, 110 * scale)
    spacing = -15 * scale
    
    text_w = int(sum(font.getlength(c) for c in text) + max(0, len(text)-1) * spacing)
    bbox = font.getbbox(text)
    text_h = bbox[3] - bbox[1]
    
    pad = text_h
    padded_img = Image.new("RGBA", (text_w + pad*2, text_h + pad*2), (0,0,0,0))
    draw = ImageDraw.Draw(padded_img)
    
    curr_x = pad
    for char in text:
        c_bbox = font.getbbox(char)
        draw.text((curr_x - c_bbox[0], pad - bbox[1]), char, font=font, fill="#f984f2")
        curr_x += font.getlength(char) + spacing

    # Image.BICUBIC に変更
    transformed = padded_img.transform(padded_img.size, Image.AFFINE, (1, 0.2, 0, 0, 1, 0), resample=Image.BICUBIC)
    transformed = transformed.rotate(-5.5, expand=True, resample=Image.BICUBIC)
    
    cropped = transformed.crop(transformed.getbbox())
    # Image.LANCZOS に変更
    resized = cropped.resize((500-24, 500-24), Image.LANCZOS)
    
    final = Image.new("RGBA", (500, 500), (0,0,0,0))
    final.paste(resized, ((500-resized.width)//2, (500-resized.height)//2))
    
    mask = final.getchannel('A').filter(ImageFilter.MaxFilter(25))
    res = Image.new("RGBA", (500, 500), (0,0,0,0))
    res.paste((255,255,255,255), (0,0), mask)
    res.paste(final, (0,0), final)
    return res

def generate_text5_gradient(text: str, font_path: str):
    font = ImageFont.truetype(font_path, 110)
    spacing = -15
    text_w = int(sum(font.getlength(c) for c in text) + max(0, len(text)-1) * spacing)
    bbox = font.getbbox(text)
    text_h = bbox[3] - bbox[1]

    mask = Image.new("L", (text_w, text_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    curr_x = 0
    for char in text:
        c_bbox = font.getbbox(char)
        draw_mask.text((curr_x - c_bbox[0], -bbox[1]), char, font=font, fill=255)
        curr_x += font.getlength(char) + spacing

    colors = ["#fd57d8", "#fb0af2", "#fa01fd", "#fd31f1", "#fc91b0", "#fdfa38", "#e8ee38",
              "#d0f457", "#6af097", "#6ee9b4", "#9ad0f2", "#9997fd", "#8d81fb", "#883cfe"]
    rgbs = [ImageColor.getrgb(c) for c in colors]
    
    grad = Image.new("RGBA", (text_w, text_h))
    draw_grad = ImageDraw.Draw(grad)
    for y in range(text_h):
        prog = y / (text_h - 1)
        idx = prog * (len(rgbs)-1)
        i1, i2 = int(idx), min(int(idx)+1, len(rgbs)-1)
        b = idx - i1
        color = tuple(int(rgbs[i1][k]*(1-b) + rgbs[i2][k]*b) for k in range(3))
        draw_grad.line([(0, y), (text_w, y)], fill=color)
        
    res = Image.new("RGBA", (text_w, text_h))
    res.paste(grad, (0,0), mask)
    # Image.LANCZOS に変更
    return res.resize((500, 500), Image.LANCZOS)