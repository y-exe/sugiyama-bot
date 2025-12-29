# services/image/text_gen.py
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core.config import FONTS_DIR
import os

def generate_styled_text_image(text_to_render: str, font_path: str, mode_params: dict, is_square: bool = False):
    font_size = 110
    font = ImageFont.truetype(font_path, font_size)
    lines = text_to_render.split(',')
    spacing = mode_params.get('spacing', 0)

    line_images = []
    max_line_width = 0
    total_line_height = 0
    
    for line in lines:
        line_width = int(sum(font.getlength(c) for c in line) + max(0, len(line) - 1) * spacing)
        if line_width <= 0: continue
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        
        line_img = Image.new("L", (line_width, line_height))
        draw = ImageDraw.Draw(line_img)
        
        curr_x = 0
        for char in line:
            char_bbox = font.getbbox(char)
            draw.text((curr_x - char_bbox[0], -bbox[1]), char, font=font, fill=255)
            curr_x += font.getlength(char) + spacing
        
        line_images.append(line_img)
        max_line_width = max(max_line_width, line_img.width)
        total_line_height += line_img.height

    text_mask = Image.new("L", (max_line_width, total_line_height))
    curr_y = 0
    for img in line_images:
        x_pos = (max_line_width - img.width) // 2
        text_mask.paste(img, (x_pos, curr_y))
        curr_y += img.height

    if is_square:
        bbox = text_mask.getbbox()
        if bbox:
            padding = mode_params.get('padding', 15)
            size = 500 - padding * 2
            # Image.LANCZOS に変更
            text_mask = text_mask.crop(bbox).resize((size, size), Image.LANCZOS)

    inner_t = mode_params['inner_thickness']
    outer_t = mode_params.get('outer_thickness', 0)
    pad = inner_t + outer_t + 5
    
    padded_mask = Image.new("L", (text_mask.width + pad*2, text_mask.height + pad*2))
    padded_mask.paste(text_mask, (pad, pad))
    
    inner_mask = padded_mask.filter(ImageFilter.MaxFilter(inner_t * 2 + 1))
    final_img = Image.new("RGBA", inner_mask.size, (0, 0, 0, 0))
    
    if outer_t > 0:
        outer_mask = padded_mask.filter(ImageFilter.MaxFilter((inner_t + outer_t) * 2 + 1))
        final_img.paste(Image.new("RGBA", inner_mask.size, mode_params['outer_color']), (0, 0), outer_mask)
        
    final_img.paste(Image.new("RGBA", inner_mask.size, mode_params['inner_color']), (0, 0), inner_mask)
    final_img.paste(Image.new("RGBA", inner_mask.size, mode_params['text_color']), (0, 0), padded_mask)
    
    bbox = final_img.getbbox()
    return final_img.crop(bbox) if bbox else final_img