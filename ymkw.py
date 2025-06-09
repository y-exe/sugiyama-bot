# ========================== IMPORTS ==========================
import os
import discord
from discord.ext import commands
import google.generativeai as genai
from google.generativeai import types as genai_types
import datetime
import asyncio
import aiohttp
import urllib.parse
import json
import io
import random
from PIL import Image, ImageOps
import numpy as np
import math
import subprocess
from dotenv import load_dotenv

# ========================== CONFIGURATION & INITIALIZATION ==========================
load_dotenv(os.path.join(os.path.dirname(__file__), ".env")) 

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_DISCORD_BOT_TOKEN_PLACEHOLDER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_PLACEHOLDER")

BOT_COMMAND_PREFIX = "!"
SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), "bot_settings.json")
allowed_channels = set()
JST = datetime.timezone(datetime.timedelta(hours=9), 'JST')

MAX_FILE_SIZE_BYTES = int(4.8 * 1024 * 1024)
MIN_IMAGE_DIMENSION = 300
TEMPLATES_BASE_PATH = os.path.join(os.path.dirname(__file__), "assets", "watermark_templates")
TEMPLATES_DATA = [
    {"name": "POCO F3.png", "user_ratio_str": "3/4", "target_size": (3000, 4000)},
    {"name": "GalaxyS23 2.png", "user_ratio_str": "563/1000", "target_size": (2252, 4000)},
    {"name": "IPHONE 11 PRO MAX.png", "user_ratio_str": "672/605", "target_size": (4032, 3630)},
    {"name": "motorola eage 50s pro.png", "user_ratio_str": "4/3", "target_size": (4096, 3072)},
    {"name": "XIAOMI 15 Ultra 2.png", "user_ratio_str": "320/277", "target_size": (1280, 1108)},
    {"name": "Galaxy S23.png", "user_ratio_str": "1000/563", "target_size": (4000, 2252)},
    {"name": "XIAOMI13.png", "user_ratio_str": "512/329", "target_size": (4096, 2632)},
    {"name": "Vivo X200 Pro.png", "user_ratio_str": "512/329", "target_size": (4096, 2632)},
    {"name": "OPPO Find X5 2.png", "user_ratio_str": "512/439", "target_size": (4096, 3512)},
    {"name": "OPPO Find X5.png", "user_ratio_str": "3/4", "target_size": (1080, 1440)}
]

GREEN_SQUARE = "<:o_0:1380626312976138400>"
BLACK_STONE  = "<:o_2:1380626308383510548>"
WHITE_STONE  = "<:o_1:1380626310551830580>"
MARKERS = ["0️⃣","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","<:o_A:1380638761288859820>","<:o_B:1380638762941419722>","<:o_C:1380638764782850080>","<:o_D:1380638769216225321>","<:o_E:1380638771178897559>","<:o_F:1380638773926301726>","<:o_G:1380638776103010365>","<:o_H:1380643990784966898>","<:o_I:1380644006093918248>","<:o_J:1380644004181577849>","<:o_K:1380644001652281374>","<:o_L:1380643998841966612>","<:o_M:1380643995855622254>","<:o_N:1380643993431314432>","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"]
active_games = {}
othello_recruitments = {}

GEMINI_TEXT_MODEL_NAME = 'gemini-1.5-flash-latest'
GEMINI_IMAGE_GENERATION_MODEL_ID = "gemini-2.0-flash-preview-image-generation" 
RVC_PROJECT_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "RVC_Project"))
RVC_MODEL_DIR_IN_PROJECT = os.path.join("assets", "weights")
RVC_MODEL_NAME_WITH_EXT = "RVC.pth" # RVCのモデル名にしてください
RVC_INFER_SCRIPT_SUBPATH = os.path.join("tools", "infer_cli.py") 
RVC_FIXED_TRANSPOSE = 0
RVC_INPUT_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio", "input")
RVC_OUTPUT_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio", "output")

for t_data in TEMPLATES_DATA:
    try:
        parts = t_data['user_ratio_str'].split('/')
        if len(parts) == 2 and float(parts[1]) != 0: t_data['match_ratio_wh'] = float(parts[0]) / float(parts[1])
        else: raise ValueError("Invalid ratio format")
    except Exception as e:
        print(f"Warning: Template '{t_data['name']}' ratio parsing error: {e}"); t_data['match_ratio_wh'] = 1.0

gemini_text_model = None; GEMINI_API_UNAVAILABLE = False
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_PLACEHOLDER":
    try: genai.configure(api_key=GEMINI_API_KEY); gemini_text_model = genai.GenerativeModel(GEMINI_TEXT_MODEL_NAME)
    except Exception as e: print(f"Gemini API initialization failed: {e}"); GEMINI_API_UNAVAILABLE = True
else: print("Warning: GEMINI_API_KEY is not set or is a placeholder. Gemini features will be unavailable."); GEMINI_API_UNAVAILABLE = True

intents = discord.Intents.default(); intents.message_content = True; intents.reactions = True
bot = commands.Bot(command_prefix=BOT_COMMAND_PREFIX, intents=intents, help_command=None)

os.makedirs(RVC_INPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(RVC_OUTPUT_AUDIO_DIR, exist_ok=True)

# ================================= GAME LOGIC (OTHELLO) =================================
EMPTY = 0; BLACK = 1; WHITE = 2; BOARD_SIZE = 8
class OthelloGame:
    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.board[3][3] = WHITE; self.board[3][4] = BLACK
        self.board[4][3] = BLACK; self.board[4][4] = WHITE
        self.current_player = BLACK
        self.valid_moves_with_markers = {}
        self.game_over = False; self.winner = None; self.last_pass = False
    def is_on_board(self, r, c): return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE
    def get_flips(self, r_s, c_s, p):
        if not self.is_on_board(r_s, c_s) or self.board[r_s][c_s] != EMPTY: return []
        op = WHITE if p == BLACK else BLACK; ttf = []
        for dr, dc in [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
            r, c = r_s + dr, c_s + dc; cpf = []
            while self.is_on_board(r, c) and self.board[r][c] == op: cpf.append((r, c)); r += dr; c += dc
            if self.is_on_board(r, c) and self.board[r][c] == p and cpf: ttf.extend(cpf)
        return ttf
    def calculate_valid_moves(self, p):
        self.valid_moves_with_markers.clear(); mi = 0; current_valid_coords = []
        for r_idx in range(BOARD_SIZE):
            for c_idx in range(BOARD_SIZE):
                if self.board[r_idx][c_idx] == EMPTY and self.get_flips(r_idx, c_idx, p):
                    current_valid_coords.append((r_idx, c_idx))
                    if mi < len(MARKERS): self.valid_moves_with_markers[(r_idx, c_idx)] = MARKERS[mi]; mi += 1
        return current_valid_coords
    def make_move(self, r, c, p):
        if not self.is_on_board(r, c) or self.board[r][c] != EMPTY: return False
        ttf = self.get_flips(r, c, p)
        if not ttf: return False
        self.board[r][c] = p
        for fr, fc in ttf: self.board[fr][fc] = p
        self.last_pass = False; return True
    def switch_player(self): self.current_player = WHITE if self.current_player == BLACK else BLACK
    def check_game_status(self):
        if self.calculate_valid_moves(self.current_player): self.last_pass = False; return
        if self.last_pass: self.game_over = True
        else:
            self.last_pass = True; self.switch_player()
            if not self.calculate_valid_moves(self.current_player): self.game_over = True
        if self.game_over: self.determine_winner()
    def determine_winner(self):
        bs = sum(r.count(BLACK) for r in self.board); ws = sum(r.count(WHITE) for r in self.board)
        if bs > ws: self.winner = BLACK
        elif ws > bs: self.winner = WHITE
        else: self.winner = EMPTY

# =================================== HELPER FUNCTIONS ===================================
def load_settings():
    global allowed_channels
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                d = json.load(f); allowed_channels = set(d.get("allowed_channels", []))
        else: allowed_channels = set(); save_settings()
    except Exception as e: print(f"Settings load error: {e}."); allowed_channels = set()

def save_settings():
    d = {"allowed_channels": list(allowed_channels)}
    try:
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Settings save error: {e}")

async def _resize_image_if_too_large(
    image_fp: io.BytesIO, target_format: str, max_size_bytes: int = MAX_FILE_SIZE_BYTES,
    min_dimension: int = MIN_IMAGE_DIMENSION, initial_aggressiveness: float = 0.9,
    subsequent_resize_factor: float = 0.85, max_iterations: int = 7
) -> tuple[io.BytesIO | None, bool]:
    image_fp.seek(0, io.SEEK_END); current_size = image_fp.tell(); image_fp.seek(0)
    if current_size <= max_size_bytes: return image_fp, False
    current_fp_to_process = image_fp; resized_overall = False
    for iteration in range(max_iterations):
        current_fp_to_process.seek(0)
        try:
            img = Image.open(current_fp_to_process); original_width, original_height = img.width, img.height
            if min(original_width, original_height) <= min_dimension: break
            current_fp_to_process.seek(0, io.SEEK_END); current_iteration_size = current_fp_to_process.tell(); current_fp_to_process.seek(0)
            resize_this_iteration_factor = subsequent_resize_factor
            if iteration == 0 and current_iteration_size > max_size_bytes:
                area_ratio = max_size_bytes / current_iteration_size
                dimension_ratio_estimate = math.sqrt(area_ratio) * initial_aggressiveness
                resize_this_iteration_factor = max(0.1, min(dimension_ratio_estimate, 0.95))
            new_width = int(original_width * resize_this_iteration_factor); new_height = int(original_height * resize_this_iteration_factor)
            if new_width < min_dimension or new_height < min_dimension:
                aspect_ratio = original_width / original_height
                if new_width < min_dimension: new_width = min_dimension; new_height = int(new_width / aspect_ratio)
                if new_height < min_dimension: new_height = min_dimension; new_width = int(new_height * aspect_ratio)
                new_width = max(new_width, 1); new_height = max(new_height, 1)
                if new_width == original_width and new_height == original_height: break
            output_fp = io.BytesIO()
            if target_format.upper() == "GIF":
                frames = []; duration = img.info.get('duration', 100); loop = img.info.get('loop', 0)
                try:
                    img.seek(0)
                    while True:
                        frame_copy = img.copy(); frame_copy.thumbnail((new_width, new_height), Image.Resampling.LANCZOS); frames.append(frame_copy)
                        img.seek(img.tell() + 1)
                except EOFError: pass
                if not frames: break
                frames[0].save(output_fp, format="GIF", save_all=True, append_images=frames[1:], duration=duration, loop=loop, disposal=2, optimize=True)
            else:
                resized_img = img.copy(); resized_img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS); resized_img.save(output_fp, format=target_format.upper(), compress_level=7, optimize=True)
            output_fp.seek(0, io.SEEK_END); new_size = output_fp.tell(); output_fp.seek(0)
            if current_fp_to_process != image_fp: current_fp_to_process.close()
            current_fp_to_process = output_fp; resized_overall = True
            if new_size <= max_size_bytes: return current_fp_to_process, resized_overall
        except Exception:
            if current_fp_to_process != image_fp: current_fp_to_process.close()
            return image_fp, False
    return current_fp_to_process, resized_overall

def _process_and_composite_image(img_bytes: bytes, tmpl_data: dict) -> io.BytesIO | None:
    try:
        base_image = Image.open(io.BytesIO(img_bytes)); tw, th = tmpl_data['target_size']
        proc_base = ImageOps.fit(base_image, (tw, th), Image.Resampling.LANCZOS)
        overlay_p = os.path.join(TEMPLATES_BASE_PATH, tmpl_data['name'])
        if not os.path.exists(overlay_p): return None
        overlay = Image.open(overlay_p).convert("RGBA").resize((tw, th), Image.Resampling.LANCZOS)
        if proc_base.mode != 'RGBA': proc_base = proc_base.convert('RGBA')
        final = Image.alpha_composite(proc_base, overlay)
        buf = io.BytesIO(); final.save(buf, "PNG"); buf.seek(0); return buf
    except Exception: return None

def _create_gaming_gif(img_bytes: bytes, duration_ms: int = 50, max_size: tuple = (256, 256)) -> io.BytesIO:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    img.thumbnail(max_size, Image.Resampling.LANCZOS); frames = []
    for i in range(36):
        h, s, v = img.convert("HSV").split()
        h_array = np.array(h, dtype=np.int16)
        hue_shift_amount = int((i * 10) * (255.0 / 360.0))
        shifted_h_array = np.mod(h_array + hue_shift_amount, 256).astype(np.uint8)
        shifted_h_image = Image.fromarray(shifted_h_array, 'L')
        gaming_frame_hsv = Image.merge("HSV", (shifted_h_image, s, v))
        frames.append(gaming_frame_hsv.convert("RGBA"))
    output_buffer = io.BytesIO()
    frames[0].save(output_buffer, format="GIF", save_all=True, append_images=frames[1:], duration=duration_ms, loop=0, disposal=2)
    output_buffer.seek(0); return output_buffer

async def generate_gemini_text_response(prompt_parts: list) -> str:
    global GEMINI_API_UNAVAILABLE
    if not gemini_text_model or GEMINI_API_UNAVAILABLE: return "Error: Gemini Text API is not available."
    try:
        response = await asyncio.to_thread(gemini_text_model.generate_content, prompt_parts, request_options={'timeout': 120})
        if hasattr(response, 'text') and response.text: return response.text
        elif response.candidates: return f"Could not generate response. Reason: {response.candidates[0].finish_reason}"
        elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason: return f"Prompt blocked. Reason: {response.prompt_feedback.block_reason}"
        else: return "Could not generate response. Unexpected format."
    except Exception as e: return f"Gemini Text API Error: {type(e).__name__} - {e}"

async def generate_gemini_image_edit_response_with_client(prompt_text: str, image_pil: Image.Image) -> tuple[io.BytesIO | None, str | None]:
    global GEMINI_API_UNAVAILABLE
    if GEMINI_API_UNAVAILABLE: return None, "Error: Gemini API is not available."
    try:
        client = genai.Client(); contents_for_model = [(prompt_text,), image_pil]
        generation_config = genai_types.GenerateContentConfig(response_modalities=['TEXT', 'IMAGE'])
        response = await asyncio.to_thread(client.models.generate_content, model=GEMINI_IMAGE_GENERATION_MODEL_ID, contents=contents_for_model, generation_config=generation_config)
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            text_response_parts = []; edited_image_fp = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text is not None: text_response_parts.append(part.text)
                elif hasattr(part, 'inline_data') and part.inline_data is not None and hasattr(part.inline_data, 'data'):
                    try: Image.open(io.BytesIO(part.inline_data.data)); edited_image_fp = io.BytesIO(part.inline_data.data)
                    except Exception: pass
            return edited_image_fp, "\n".join(text_response_parts) if text_response_parts else None
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason: return None, f"Prompt blocked. Reason: {response.prompt_feedback.block_reason}"
        return None, "Failed to retrieve edited image (unexpected response format)."
    except Exception as e: return None, f"Gemini Image API Error: {type(e).__name__} - {e}"

async def generate_summary_with_gemini(text: str, num_points: int = 3) -> str:
    prompt = f"Summarize the following into {num_points} short bullet points:\n\n{text}"
    return await generate_gemini_text_response([prompt])

async def send_board_message_text(channel: discord.TextChannel, game_session: dict, game_message_id: int, is_first_turn: bool = False):
    game = game_session["game"]; game.calculate_valid_moves(game.current_player)
    p1_id = game_session["players"].get(BLACK); p2_id = game_session["players"].get(WHITE)
    current_player_id = game_session["players"].get(game.current_player)
    try: p1_user = await bot.fetch_user(p1_id)
    except discord.NotFound: p1_user = None
    try: p2_user = await bot.fetch_user(p2_id)
    except discord.NotFound: p2_user = None
    try: current_player_user = await bot.fetch_user(current_player_id)
    except discord.NotFound: current_player_user = None
    p1_mention = p1_user.mention if p1_user else f"Player 1 ({p1_id})"; p2_mention = p2_user.mention if p2_user else f"Player 2 ({p2_id})"
    current_player_mention = current_player_user.mention if current_player_user else f"Player ({current_player_id})"
    content_lines = [f"<サーバー内対戦>", ""]; board_str = ""
    for r_idx in range(BOARD_SIZE):
        for c_idx in range(BOARD_SIZE):
            coord = (r_idx, c_idx)
            if coord in game.valid_moves_with_markers: board_str += game.valid_moves_with_markers[coord]
            elif game.board[r_idx][c_idx] == BLACK: board_str += BLACK_STONE
            elif game.board[r_idx][c_idx] == WHITE: board_str += WHITE_STONE
            else: board_str += GREEN_SQUARE
        board_str += "\n"
    content_lines.append(f"{board_str.strip()}")
    black_score = sum(row.count(BLACK) for row in game.board); white_score = sum(row.count(WHITE) for row in game.board)
    black_player_mention = p1_mention if p1_id == game_session["players"][BLACK] else p2_mention
    white_player_mention = p2_mention if p2_id == game_session["players"][WHITE] else p1_mention
    content_lines.append(f"{BLACK_STONE} {black_player_mention} vs {WHITE_STONE} {white_player_mention}")
    content_lines.append(f"スコア: {BLACK_STONE} {black_score} - {WHITE_STONE} {white_score}"); content_lines.append(f"手番: {current_player_mention}")
    final_content = "\n".join(content_lines); message_to_update: discord.Message = None
    if game_message_id:
        try: message_to_update = await channel.fetch_message(game_message_id)
        except (discord.NotFound, discord.HTTPException): pass
    if game.game_over:
        winner_text = "引き分け"; winner_id = game_session["players"].get(game.winner)
        if winner_id:
            winner_user = None
            try: winner_user = await bot.fetch_user(winner_id)
            except discord.NotFound: pass
            if winner_user and game.winner != EMPTY: winner_text = f"{BLACK_STONE if game.winner == BLACK else WHITE_STONE} {winner_user.mention} の勝ち！"
        game_over_lines = [f"<サーバー内対戦>", "",f"{board_str.strip()}",f"{BLACK_STONE} {black_player_mention} vs {WHITE_STONE} {white_player_mention}",f"スコア: {BLACK_STONE} {black_score} - {WHITE_STONE} {white_score}",f"**ゲーム終了！ {winner_text}**"]
        final_content = "\n".join(game_over_lines)
        if message_to_update:
            try: await message_to_update.edit(content=final_content); await message_to_update.clear_reactions()
            except discord.HTTPException: pass
        else:
            try: await channel.send(content=final_content)
            except discord.HTTPException: pass
        if game_message_id in active_games: del active_games[game_message_id]
        return
    if message_to_update:
        try: await message_to_update.edit(content=final_content)
        except discord.HTTPException: return
    else:
        try:
            message_to_update = await channel.send(content=final_content); active_games[message_to_update.id] = game_session
            if game_message_id in active_games and game_message_id != message_to_update.id: del active_games[game_message_id]
        except discord.HTTPException: return
    if message_to_update:
        current_reactions = [str(r.emoji) for r in message_to_update.reactions if r.me]; new_markers = list(game.valid_moves_with_markers.values())
        if is_first_turn:
            try: await message_to_update.clear_reactions()
            except (discord.Forbidden, discord.HTTPException): pass
            current_reactions = []
        to_remove = [e for e in current_reactions if e not in new_markers]; to_add = [e for e in new_markers if e not in current_reactions]
        await asyncio.gather(*[message_to_update.remove_reaction(e, bot.user) for e in to_remove], return_exceptions=True)
        await asyncio.gather(*[message_to_update.add_reaction(e) for e in to_add], return_exceptions=True)

def get_initial_board_text():
    temp_game = OthelloGame(); board_str = ""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if temp_game.board[r][c] == BLACK: board_str += BLACK_STONE
            elif temp_game.board[r][c] == WHITE: board_str += WHITE_STONE
            else: board_str += GREEN_SQUARE
        board_str += "\n"
    return board_str.strip()

# =============================== DISCORD EVENT HANDLERS ===============================
@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name} ({bot.user.id})'); load_settings()
    print(f"Settings loaded. Allowed channels: {len(allowed_channels)}")
    gemini_status = "Not Available"
    if not GEMINI_API_UNAVAILABLE: gemini_status = f"Available (Text: {GEMINI_TEXT_MODEL_NAME}, Image Gen: {GEMINI_IMAGE_GENERATION_MODEL_ID})"
    print(f"Gemini API Status: {gemini_status}"); print("--- RVC Checks ---")
    rvc_infer_script_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    if not os.path.exists(rvc_infer_script_full_path): print(f"警告: RVC推論スクリプトが見つかりません: {rvc_infer_script_full_path}")
    else: print(f"RVC推論スクリプトを確認: {rvc_infer_script_full_path}")
    rvc_model_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    if not os.path.exists(rvc_model_full_path): print(f"警告: RVCモデル '{RVC_MODEL_NAME_WITH_EXT}' が見つかりません: {rvc_model_full_path}")
    else: print(f"RVCモデル '{RVC_MODEL_NAME_WITH_EXT}' を確認: {rvc_model_full_path}")
    print("------------------")
    try: synced = await bot.tree.sync(); print(f'Synced {len(synced)} slash commands.')
    except Exception as e: print(f"Slash command sync failed: {e}")
    await bot.change_presence(activity=discord.Game(name="杉山啓太Bot")); print("Bot is ready.")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot or not message.guild: return
    if message.content.startswith(bot.command_prefix):
        cmd_name = message.content[len(bot.command_prefix):].split(' ', 1)[0].lower()
        cmd_obj = bot.get_command(cmd_name)
        allowed_everywhere = ['setchannel'] # 'voice' もチャンネル制限の対象にするため、リストから削除
        if cmd_obj and cmd_obj.name not in allowed_everywhere and message.channel.id not in allowed_channels:
            print(f"Command '{cmd_obj.name}' blocked in channel {message.channel.id} (not in allowed_channels)")
            return
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user == bot.user: return
    message = reaction.message; message_id = message.id
    if message_id in othello_recruitments:
        rec_info = othello_recruitments[message_id]; host_id = rec_info["host_id"]
        if str(reaction.emoji) == "❌" and user.id == host_id:
            if message_id in othello_recruitments: del othello_recruitments[message_id]
            try: await message.edit(content=f"{user.mention}が募集を取り消しました。", view=None); await message.clear_reactions()
            except discord.HTTPException: pass
            return
        if str(reaction.emoji) == "✅" and user.id != host_id:
            if rec_info.get("opponent_id"):
                try: await reaction.remove(user)
                except discord.HTTPException: pass
                return
            rec_info["opponent_id"] = user.id
            if message_id in othello_recruitments: del othello_recruitments[message_id]
            players_list = [host_id, user.id]; random.shuffle(players_list)
            players = {BLACK: players_list[0], WHITE: players_list[1]}
            active_games[message_id] = {"game": OthelloGame(), "players": players, "host_id": host_id, "channel_id": message.channel.id}
            await send_board_message_text(message.channel, active_games[message_id], message_id, is_first_turn=True)
        elif user.id != host_id:
             try: await reaction.remove(user)
             except discord.HTTPException: pass
        return
    if message_id in active_games:
        game_session = active_games[message_id]; game = game_session["game"]
        players_ids = list(game_session["players"].values())
        if user.id not in players_ids or game.game_over:
            try: await reaction.remove(user)
            except discord.HTTPException: pass
            return
        if user.id != game_session["players"].get(game.current_player):
            try: await reaction.remove(user)
            except discord.HTTPException: pass
            return
        chosen_move = next((coord for coord, marker in game.valid_moves_with_markers.items() if str(reaction.emoji) == marker), None)
        if chosen_move:
            if game.make_move(chosen_move[0], chosen_move[1], game.current_player):
                game.switch_player(); game.check_game_status()
                await send_board_message_text(message.channel, game_session, message_id)
        try: await reaction.remove(user)
        except discord.HTTPException: pass

# ================================== DISCORD COMMANDS ==================================
# !help
@bot.command(name="help")
async def help_prefix(ctx: commands.Context):
    embed = discord.Embed(title="杉山啓太Bot コマンド一覧", color=discord.Color.blue())
    cmds = [
        ("!watermark", "添付画像にウォーターマークを合成。"),
        ("/imakita", "過去30分のチャットを3行で要約。(実行者のみ)"),
        ("!5000 [上] [下] (hoshii) (rainbow)", "「5000兆円欲しい！」画像を生成。"),
        ("!image [プロンプト]", "添付画像とプロンプトでAIが画像を編集/生成。"),
        ("!gaming", "添付画像をゲーミング風GIFに変換。"),
        ("!othello (@相手)", "オセロの対戦相手を募集します。相手を指定すると即時対戦開始。"),
        ("!voice", "添付音声の声をRVCで変換。（モデル固定）"),
        ("!help", "このヘルプを表示。")
    ]
    for name, value in cmds: embed.add_field(name=name, value=value, inline=False)
    status = "Available" if not GEMINI_API_UNAVAILABLE else "Not Available"
    embed.set_footer(text=f"Gemini API Status: {status}")
    await ctx.send(embed=embed)

# !setchannel
@bot.command(name="setchannel")
@commands.has_permissions(administrator=True)
async def setchannel_prefix(ctx: commands.Context):
    cid = ctx.channel.id
    if cid in allowed_channels:
        allowed_channels.remove(cid); await ctx.send(f"このチャンネルでの通常コマンド利用を**禁止**しました。")
    else:
        allowed_channels.add(cid); await ctx.send(f"このチャンネルでの通常コマンド利用を**許可**しました。")
    save_settings()

@setchannel_prefix.error
async def setchannel_error(ctx, error):
    if isinstance(error, commands.MissingPermissions): await ctx.send("管理者権限が必要です。")
    else: await ctx.send(f"エラー: {error}")

# !watermark
@bot.command(name="watermark")
async def watermark_prefix(ctx: commands.Context):
    if not ctx.message.attachments: return await ctx.send("画像を添付してください。")
    att = ctx.message.attachments[0]
    if not att.content_type or not att.content_type.startswith("image/"): return await ctx.send("画像ファイルを添付してください。")
    if not TEMPLATES_DATA: return await ctx.send("エラー: ウォーターマークのテンプレートが設定されていません。")
    async with ctx.typing():
        img_b = await att.read()
        try: up_img = Image.open(io.BytesIO(img_b)); uw, uh = up_img.size
        except Exception as e: return await ctx.send(f"画像読み込み失敗: {e}")
        if uw == 0 or uh == 0: return await ctx.send("無効な画像サイズです。")
        up_r = uw / uh; best_t = []; min_d = float('inf')
        for t_i in TEMPLATES_DATA:
            if 'match_ratio_wh' not in t_i or not os.path.exists(os.path.join(TEMPLATES_BASE_PATH, t_i['name'])): continue
            d = abs(t_i['match_ratio_wh'] - up_r)
            if d < min_d: min_d, best_t = d, [t_i]
            elif d == min_d: best_t.append(t_i)
        if not best_t: return await ctx.send("アスペクト比が合うテンプレートが見つかりませんでした。")
        sel_t = random.choice(best_t)
        final_b = await asyncio.to_thread(_process_and_composite_image, img_b, sel_t)
        if final_b:
            final_b, resized = await _resize_image_if_too_large(final_b, "PNG")
            if final_b is None: return await ctx.send("ウォーターマーク画像の処理中にエラーが発生しました。")
            final_b.seek(0, io.SEEK_END); file_size = final_b.tell(); final_b.seek(0)
            if file_size > MAX_FILE_SIZE_BYTES: return await ctx.send(f"加工後画像のファイルサイズが大きすぎます。")
            out_fname = f"wm_{os.path.splitext(att.filename)[0]}.png"
            await ctx.send(f"加工完了！ (使用: {sel_t['name']}){' (リサイズ済)' if resized else ''}", file=discord.File(fp=final_b, filename=out_fname))
        else: await ctx.send("画像の加工に失敗しました。")

# !5000
@bot.command(name="5000")
async def five_k_choyen_prefix(ctx: commands.Context, top_text: str = None, bottom_text: str = None, *options: str):
    if top_text is None or bottom_text is None: return await ctx.send("上下の文字列を指定してください。\n例: `!5000 すごい やった`")
    params = {"top": top_text, "bottom": bottom_text, "hoshii": "true" if "hoshii" in options else "false", "rainbow": "true" if "rainbow" in options else "false"}
    url = f"https://gsapi.cbrx.io/image?{urllib.parse.urlencode(params)}"
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as s, s.get(url) as r:
                if r.status == 200:
                    embed = discord.Embed(title="5000兆円欲しい！", color=discord.Color.gold()).set_image(url=url)
                    await ctx.send(embed=embed)
                else: await ctx.send(f"画像生成失敗 (APIステータス: {r.status})")
        except Exception as e: await ctx.send(f"画像生成中にエラー: {e}")

# !image
@bot.command(name="image")
async def image_prefix(ctx: commands.Context, *, prompt: str = None):
    if not ctx.message.attachments: return await ctx.send("画像を添付してください。")
    if not prompt or not prompt.strip(): return await ctx.send("AIへの指示（プロンプト）を入力してください。")
    attachment = ctx.message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image/"): return await ctx.send("画像ファイルを添付してください。")
    async with ctx.typing():
        image_bytes = await attachment.read()
        try: input_pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e: return await ctx.send(f"添付画像の読み込みに失敗しました: {e}")
        edited_image_fp, response_text = await generate_gemini_image_edit_response_with_client(prompt, input_pil_image)
        if edited_image_fp:
            edited_image_fp, resized = await _resize_image_if_too_large(edited_image_fp, "PNG")
            if edited_image_fp is None: return await ctx.send(f"画像処理中にエラーが発生しました。\nAIコメント: {response_text or 'なし'}")
            edited_image_fp.seek(0, io.SEEK_END); file_size = edited_image_fp.tell(); edited_image_fp.seek(0)
            if file_size > MAX_FILE_SIZE_BYTES: return await ctx.send(f"生成画像のファイルサイズが大きすぎます。")
            out_fname = f"edited_{os.path.splitext(attachment.filename)[0]}.png"
            msg = f"プロンプト「{prompt}」で画像編集/生成しました！{' (リサイズ済)' if resized else ''}"
            if response_text: msg += f"\nAIコメント:\n```\n{response_text}\n```"
            await ctx.send(msg, file=discord.File(fp=edited_image_fp, filename=out_fname))
        else: await ctx.send(f"画像編集・生成失敗。\n詳細:\n```\n{response_text or '不明なエラー'}\n```")

# !gaming
@bot.command(name="gaming")
async def gaming_prefix(ctx: commands.Context):
    if not ctx.message.attachments: return await ctx.send("画像を添付してください。")
    attachment = ctx.message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image/"): return await ctx.send("画像ファイルを添付してください。")
    async with ctx.typing():
        image_bytes = await attachment.read()
        try:
            gif_buffer = await asyncio.to_thread(_create_gaming_gif, image_bytes)
            gif_buffer, resized = await _resize_image_if_too_large(gif_buffer, "GIF")
            if gif_buffer is None: return await ctx.send(f"ゲーミングGIFの処理中にエラーが発生しました。")
            gif_buffer.seek(0, io.SEEK_END); file_size = gif_buffer.tell(); gif_buffer.seek(0)
            if file_size > MAX_FILE_SIZE_BYTES: return await ctx.send(f"生成GIFのファイルサイズが大きすぎます。")
            out_fname = f"gaming_{os.path.splitext(attachment.filename)[0]}.gif"
            await ctx.send(f"ゲーミング風GIFを生成しました！{' (リサイズ済)' if resized else ''}", file=discord.File(fp=gif_buffer, filename=out_fname))
        except Exception as e: await ctx.send(f"ゲーミングGIFの生成中にエラー: {e}")

# !othello
@bot.command(name="othello")
async def othello_recruit(ctx: commands.Context, opponent: discord.Member = None):
    host_id = ctx.author.id
    if opponent and opponent != ctx.author and not opponent.bot:
        players_list = [host_id, opponent.id]; random.shuffle(players_list)
        players = {BLACK: players_list[0], WHITE: players_list[1]}
        game_session = {"game": OthelloGame(), "players": players, "host_id": host_id, "channel_id": ctx.channel.id}
        try:
            msg = await ctx.send("対戦を開始します...")
            active_games[msg.id] = game_session
            await send_board_message_text(ctx.channel, game_session, msg.id, is_first_turn=True)
        except discord.HTTPException as e: print(f"Othello direct match creation failed: {e}")
        return
    message_content = (f"<サーバー内対戦>\n\n{get_initial_board_text()}\n\n{ctx.author.mention} さんが対戦相手を募集しています。\n対戦を受ける場合は ✅ でリアクションしてください。\n（募集者は ❌ で募集を取り消せます）")
    try:
        msg = await ctx.send(message_content)
        await msg.add_reaction("✅"); await msg.add_reaction("❌")
        othello_recruitments[msg.id] = {"host_id": host_id, "channel_id": ctx.channel.id}
    except Exception as e: print(f"Othello recruitment message failed: {e}")

# /imakita
@bot.tree.command(name="imakita", description="過去30分のチャットを3行で要約します。")
async def imakita_slash(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.followup.send("このコマンドはテキストチャンネルでのみ使用できます。", ephemeral=True)
    after_time = discord.utils.utcnow() - datetime.timedelta(minutes=30)
    c_list = [f"{m.author.display_name}: {m.content}" async for m in interaction.channel.history(limit=200, after=after_time) if m.author != bot.user and not m.author.bot and m.content]
    if not c_list: return await interaction.followup.send("過去30分にメッセージはありませんでした。", ephemeral=True)
    summary = await generate_summary_with_gemini("\n".join(reversed(c_list)), 3)
    msg = f"**今北産業:**\n{summary}" if not summary.startswith("Error:") else f"要約エラー:\n{summary}"
    await interaction.followup.send(msg, ephemeral=True)

# !voice
@bot.command(name="voice")
async def rvc_voice_convert_command(ctx: commands.Context):
    if not ctx.message.attachments:
        await ctx.send("音声ファイルを添付してください。"); return
    attachment = ctx.message.attachments[0]
    if not (attachment.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a'))):
        await ctx.send("サポートされている音声ファイル形式は .wav, .mp3, .flac, .m4a です。"); return
    rvc_infer_script_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    rvc_model_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    rvc_index_file_name_no_ext, _ = os.path.splitext(RVC_MODEL_NAME_WITH_EXT)
    rvc_index_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, f"{rvc_index_file_name_no_ext}.index")
    if not os.path.exists(rvc_infer_script_full_path):
        await ctx.send("エラー: RVC推論スクリプトが見つかりません。Bot管理者に連絡してください。"); print(f"Voice command error: RVC inference script not found at {rvc_infer_script_full_path}"); return
    if not os.path.exists(rvc_model_full_path):
        await ctx.send(f"エラー: RVCモデル '{RVC_MODEL_NAME_WITH_EXT}' が見つかりません。Bot管理者に連絡してください。"); print(f"Voice command error: RVC model not found at {rvc_model_full_path}"); return
    processing_message = await ctx.send("音声変換を開始します... 💻\n**CPUで処理しているため、音声の長さによっては完了まで数分かかる場合があります。**\nしばらくお待ちください... ⏳")
    base_filename, file_extension = os.path.splitext(attachment.filename)
    timestamp = datetime.datetime.now(JST).strftime("%Y%m%d%H%M%S%f"); unique_id = f"{ctx.author.id}_{ctx.message.id}_{timestamp}"
    input_filename_rvc = f"input_{unique_id}{file_extension}"; output_filename_rvc = f"output_{unique_id}{file_extension}"
    input_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_INPUT_AUDIO_DIR, input_filename_rvc))
    output_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_OUTPUT_AUDIO_DIR, output_filename_rvc))
    try:
        await attachment.save(input_filepath_abs_rvc)
        python_executable_in_rvc_venv = os.path.join(RVC_PROJECT_ROOT_PATH, "venv", "Scripts", "python.exe")
        effective_python_executable = "python"
        if os.path.exists(python_executable_in_rvc_venv): effective_python_executable = python_executable_in_rvc_venv; print(f"RVC用Python実行ファイル: {effective_python_executable}")
        else: print(f"警告: RVCプロジェクト内の仮想環境Pythonが見つかりません ({python_executable_in_rvc_venv})。システムのPythonで実行試行。")
        command = [effective_python_executable, rvc_infer_script_full_path, "--f0up_key", str(RVC_FIXED_TRANSPOSE), "--input_path", input_filepath_abs_rvc, "--opt_path", output_filepath_abs_rvc, "--model_name", RVC_MODEL_NAME_WITH_EXT,]
        if os.path.exists(rvc_index_full_path): command.extend(["--feature_path", rvc_index_full_path]) # Assuming --feature_path for index
        print(f"実行コマンド (RVC): {' '.join(command)}")
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=RVC_PROJECT_ROOT_PATH)
        stdout_bytes, stderr_bytes = await process.communicate()
        stdout_str = stdout_bytes.decode('utf-8', errors='ignore').strip(); stderr_str = stderr_bytes.decode('utf-8', errors='ignore').strip()
        if stdout_str: print(f"--- RVC STDOUT ---\n{stdout_str}\n------------------")
        if stderr_str: print(f"--- RVC STDERR ---\n{stderr_str}\n------------------")
        if process.returncode != 0:
            print(f"RVCプロセスがエラーコード {process.returncode} で終了しました。"); await processing_message.edit(content=f"音声変換中にエラーが発生しました。\nBotのログを確認してください。"); return
        if os.path.exists(output_filepath_abs_rvc) and os.path.getsize(output_filepath_abs_rvc) > 0:
            await processing_message.edit(content="音声変換が完了しました！ ✨"); await ctx.send(file=discord.File(output_filepath_abs_rvc, filename=output_filename_rvc))
        else:
            await processing_message.edit(content="変換は成功しましたが、出力ファイルが見つかりませんでした。"); print(f"RVC出力ファイルが見つからないか、サイズが0です: {output_filepath_abs_rvc}")
    except Exception as e:
        await processing_message.edit(content=f"予期せぬエラーが発生しました: {e}"); print(f"予期せぬエラー (rvc_voice_convert_command): {e}"); import traceback; traceback.print_exc()
    finally:
        if os.path.exists(input_filepath_abs_rvc):
            try: os.remove(input_filepath_abs_rvc)
            except Exception as e_rem: print(f"入力一時ファイルの削除に失敗: {e_rem}")
        if os.path.exists(output_filepath_abs_rvc):
            try: os.remove(output_filepath_abs_rvc)
            except Exception as e_rem: print(f"出力一時ファイルの削除に失敗: {e_rem}")

# =================================== BOT EXECUTION ====================================
if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_PLACEHOLDER" or not DISCORD_BOT_TOKEN:
        print("致命的なエラー: DISCORD_BOT_TOKEN が .env ファイルに設定されていないか、プレースホルダーのままです。")
        print(f"{os.path.join(os.path.dirname(__file__), '.env')} ファイルを作成し、DISCORD_BOT_TOKEN=\"あなたのトークン\" と記述してください。")
        exit(1)
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_PLACEHOLDER" or not GEMINI_API_KEY:
        print("警告: GEMINI_API_KEY が .env ファイルに設定されていないか、プレースホルダーのままです。Gemini関連機能は利用できません。")
    try: import numpy
    except ImportError: print("警告: 'numpy' がインストールされていません。'!gaming' コマンドが動作しない可能性があります。\n仮想環境で `pip install numpy` を実行してください。")
    try: from PIL import Image
    except ImportError: print("警告: 'Pillow' がインストールされていません。画像処理関連のコマンドが動作しません。\n仮想環境で `pip install Pillow` を実行してください。")
    print("Botを起動します...")
    try: bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure: print("エラー: Discord Botトークンが無効です。トークンを確認してください。")
    except Exception as e: print(f"Bot実行中に予期せぬエラーが発生しました: {e}"); import traceback; traceback.print_exc()
