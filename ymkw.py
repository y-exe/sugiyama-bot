# ========================== IMPORTS ==========================
import os
import sys
import discord
from discord.ext import commands, tasks
import google.generativeai as genai
from google.generativeai import types as genai_types
# from google.api_core import exceptions as google_api_exceptions # Currently unused
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
import traceback

# ========================== CONFIGURATION & INITIALIZATION ==========================
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_DISCORD_BOT_TOKEN_PLACEHOLDER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_PLACEHOLDER")
WEATHER_API_BASE_URL = "https://weather.tsukumijima.net/api/forecast/city/"
EXCHANGE_RATE_API_URL = "https://exchange-rate-api.krnk.org/api/rate"
SHORTURL_API_URL = "https://x.gd/api/shorten"
SHORTURL_API_KEY = os.getenv("SHORTURL_API_KEY", "YOUR_XGD_API_KEY_PLACEHOLDER")


BOT_COMMAND_PREFIX_DUMMY = "!@#$%^&NONE_PREFIX_SUGIYAMA_BOT" # commands.Bot初期化用ダミー
SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), "bot_settings.json")
OTHELLO_POINTS_FILE_PATH = os.path.join(os.path.dirname(__file__), "othello_points.json")
allowed_channels = set()
othello_points = {}
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
LEAVE_GAME_EMOJI = "❌"
MARKERS = ["0️⃣","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","<:o_A:1380638761288859820>","<:o_B:1380638762941419722>","<:o_C:1380638764782850080>","<:o_D:1380638769216225321>","<:o_E:1380638771178897559>","<:o_F:1380638773926301726>","<:o_G:1380638776103010365>","<:o_H:1380643990784966898>","<:o_I:1380644006093918248>","<:o_J:1380644004181577849>","<:o_K:1380644001652281374>","<:o_L:1380643998841966612>","<:o_M:1380643995855622254>","<:o_N:1380643993431314432>","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"]
active_games = {}
othello_recruitments = {}
OTHELLO_AFK_TIMEOUT_SECONDS = 180

GEMINI_TEXT_MODEL_NAME = 'models/gemini-1.5-flash'

RVC_PROJECT_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "RVC_Project"))
RVC_MODEL_DIR_IN_PROJECT = os.path.join("assets", "weights")
RVC_MODEL_NAME_WITH_EXT = "ymkw.pth"
RVC_INFER_SCRIPT_SUBPATH = os.path.join("tools", "infer_cli.py")
RVC_FIXED_TRANSPOSE = 0
RVC_INPUT_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio", "input")
RVC_OUTPUT_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio", "output")

USER_BADGES_EMOJI = {
    "staff": "👑", "partner": "🤝", "hypesquad": "🎉",
    "bug_hunter_level_1": "🐛", "bug_hunter_level_2": "🐞",
    "early_verified_bot_developer": "🔧", "verified_bot": "🤖",
    "early_supporter": "💎", "active_developer": "👨‍💻",
    # 他の discord.PublicUserFlags に対応するものを追加できます
    "hypesquad_bravery": "<:bravery:123>", "hypesquad_brilliance": "<:brilliance:123>", "hypesquad_balance": "<:balance:123>",
    "premium_promo_dismissed": "", # 通常表示しない
    "system": "", # 通常表示しない
    "has_had_discord_since_basically_forever": "", # 古参フラグ (表示するかは任意)
    "team_user": "", # 通常表示しない
    "verified_email": "", # 通常表示しない
    "bot_http_interactions": "", # 通常表示しない
    "spammer": "🚫", # スパマー(表示するかは任意)
    "discord_certified_moderator": "🛡️"
}


for t_data in TEMPLATES_DATA:
    try:
        parts = t_data['user_ratio_str'].split('/')
        if len(parts) == 2 and float(parts[1]) != 0: t_data['match_ratio_wh'] = float(parts[0]) / float(parts[1])
        else: raise ValueError("Invalid ratio format")
    except Exception as e:
        print(f"Warning: Template '{t_data['name']}' ratio parsing error: {e}"); t_data['match_ratio_wh'] = 1.0

gemini_text_model_instance = None
GEMINI_API_UNAVAILABLE = False

print("--- Gemini API Initialization Attempt (Text Model Only) ---")
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_PLACEHOLDER":
    print(f"Using GEMINI_API_KEY: {GEMINI_API_KEY[:5]}... (first 5 chars of key)")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("genai.configure() successful.")
        gemini_text_model_instance = genai.GenerativeModel(GEMINI_TEXT_MODEL_NAME)
        print(f"gemini_text_model_instance for '{GEMINI_TEXT_MODEL_NAME}' created: {gemini_text_model_instance is not None}")
        if not gemini_text_model_instance:
            print("ERROR: Gemini text model instance failed to initialize.")
            GEMINI_API_UNAVAILABLE = True
        else:
            print(f"Gemini Text Model ('{GEMINI_TEXT_MODEL_NAME}') initialized successfully.")
    except Exception as e:
        print(f"ERROR: Gemini API (Text Model) initialization failed with an exception: {type(e).__name__} - {e}")
        traceback.print_exc()
        GEMINI_API_UNAVAILABLE = True
else:
    print("WARNING: GEMINI_API_KEY is not set in .env or is still the placeholder value. Gemini text features will be unavailable.")
    GEMINI_API_UNAVAILABLE = True
print("--- End of Gemini API Initialization Attempt ---")

intents = discord.Intents.default(); intents.message_content = True; intents.reactions = True; intents.members = True
bot = commands.Bot(command_prefix=BOT_COMMAND_PREFIX_DUMMY, intents=intents, help_command=None) # ダミープレフィックス使用

os.makedirs(RVC_INPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(RVC_OUTPUT_AUDIO_DIR, exist_ok=True)

# ================================= GAME LOGIC (OTHELLO) =================================
EMPTY = 0; BLACK = 1; WHITE = 2; BOARD_SIZE = 8
class OthelloGame:
    _next_game_id = 1
    _used_game_ids = set()

    def __init__(self, player_black_id, player_white_id, channel_id):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.board[3][3] = WHITE; self.board[3][4] = BLACK
        self.board[4][3] = BLACK; self.board[4][4] = WHITE
        self.current_player_color = BLACK
        self.players = {BLACK: player_black_id, WHITE: player_white_id}
        self.valid_moves_with_markers = {}
        self.game_over = False
        self.winner_color = None
        self.last_pass_by_color = None
        self.message_id = None
        self.channel_id = channel_id
        self.last_move_time = datetime.datetime.now(JST)
        self.game_id = self._assign_game_id()
        self.afk_task = None

    @classmethod
    def _assign_game_id(cls):
        gid = 1
        while gid in cls._used_game_ids:
            gid += 1
        cls._used_game_ids.add(gid)
        return gid

    @classmethod
    def _release_game_id(cls, gid):
        if gid in cls._used_game_ids:
            cls._used_game_ids.remove(gid)

    def is_on_board(self, r, c): return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE
    def get_flips(self, r_s, c_s, p_color): # Renamed p to p_color
        if not self.is_on_board(r_s, c_s) or self.board[r_s][c_s] != EMPTY: return []
        op_color = WHITE if p_color == BLACK else BLACK; ttf = [] # Renamed op to op_color
        for dr, dc in [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
            r, c = r_s + dr, c_s + dc; cpf = []
            while self.is_on_board(r, c) and self.board[r][c] == op_color: cpf.append((r, c)); r += dr; c += dc
            if self.is_on_board(r, c) and self.board[r][c] == p_color and cpf: ttf.extend(cpf)
        return ttf
    def calculate_valid_moves(self, p_color): # Renamed p to p_color
        self.valid_moves_with_markers.clear(); mi = 0; current_valid_coords = []
        for r_idx in range(BOARD_SIZE):
            for c_idx in range(BOARD_SIZE):
                if self.board[r_idx][c_idx] == EMPTY and self.get_flips(r_idx, c_idx, p_color):
                    current_valid_coords.append((r_idx, c_idx))
                    if mi < len(MARKERS): self.valid_moves_with_markers[(r_idx, c_idx)] = MARKERS[mi]; mi += 1
        return current_valid_coords
    def make_move(self, r, c, p_color): # Renamed p to p_color
        if not self.is_on_board(r, c) or self.board[r][c] != EMPTY: return False
        ttf = self.get_flips(r, c, p_color)
        if not ttf: return False
        self.board[r][c] = p_color
        for fr, fc in ttf: self.board[fr][fc] = p_color
        self.last_pass_by_color = None; self.last_move_time = datetime.datetime.now(JST); return True
    def switch_player(self): self.current_player_color = WHITE if self.current_player_color == BLACK else BLACK
    def check_game_status(self):
        if self.calculate_valid_moves(self.current_player_color): self.last_pass_by_color = None; return
        if self.last_pass_by_color == self.current_player_color: self.game_over = True
        else:
            self.last_pass_by_color = self.current_player_color; self.switch_player()
            if not self.calculate_valid_moves(self.current_player_color): self.game_over = True
        if self.game_over: self.determine_winner()
    def determine_winner(self):
        bs = sum(r.count(BLACK) for r in self.board); ws = sum(r.count(WHITE) for r in self.board)
        if bs > ws: self.winner_color = BLACK
        elif ws > bs: self.winner_color = WHITE
        else: self.winner_color = EMPTY
    def get_current_player_id(self): return self.players.get(self.current_player_color)
    def get_opponent_player_id(self): return self.players.get(WHITE if self.current_player_color == BLACK else BLACK)

# =================================== HELPER FUNCTIONS ===================================
def load_settings():
    global allowed_channels
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                d = json.load(f); allowed_channels = set(d.get("allowed_channels", []))
        else: allowed_channels = set(); save_settings()
    except Exception as e: print(f"Settings load error: {e}. (File: {SETTINGS_FILE_PATH})"); allowed_channels = set()

def save_settings():
    d = {"allowed_channels": list(allowed_channels)}
    try:
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Settings save error: {e}")

def load_othello_points():
    global othello_points
    try:
        if os.path.exists(OTHELLO_POINTS_FILE_PATH):
            with open(OTHELLO_POINTS_FILE_PATH, 'r', encoding='utf-8') as f:
                othello_points = json.load(f)
        else: othello_points = {}; save_othello_points()
    except Exception as e: print(f"Othello points load error: {e}"); othello_points = {}

def save_othello_points():
    try:
        with open(OTHELLO_POINTS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(othello_points, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Othello points save error: {e}")

def get_player_points(player_id: int) -> int:
    return othello_points.get(str(player_id), 0) # Store player_id as string in JSON

def update_player_points(player_id: int, points_change: int):
    player_id_str = str(player_id)
    current_points = othello_points.get(player_id_str, 0)
    new_points = max(0, current_points + points_change)
    othello_points[player_id_str] = new_points
    save_othello_points()


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
        except Exception as e_resize:
            print(f"Error during image resize iteration: {e_resize}")
            if current_fp_to_process != image_fp: current_fp_to_process.close()
            return image_fp, False
    return current_fp_to_process, resized_overall

def _process_and_composite_image(img_bytes: bytes, tmpl_data: dict) -> io.BytesIO | None:
    try:
        base_image = Image.open(io.BytesIO(img_bytes)); tw, th = tmpl_data['target_size']
        proc_base = ImageOps.fit(base_image, (tw, th), Image.Resampling.LANCZOS)
        overlay_p = os.path.join(TEMPLATES_BASE_PATH, tmpl_data['name'])
        if not os.path.exists(overlay_p): print(f"Overlay template not found: {overlay_p}"); return None
        overlay = Image.open(overlay_p).convert("RGBA").resize((tw, th), Image.Resampling.LANCZOS)
        if proc_base.mode != 'RGBA': proc_base = proc_base.convert('RGBA')
        final = Image.alpha_composite(proc_base, overlay)
        buf = io.BytesIO(); final.save(buf, "PNG"); buf.seek(0); return buf
    except Exception as e_composite: print(f"Error during image compositing: {e_composite}"); return None

def _create_gaming_gif(img_bytes: bytes, duration_ms: int = 50, max_size: tuple = (256, 256)) -> io.BytesIO | None:
    try:
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
    except Exception as e_gif: print(f"Error creating gaming GIF: {e_gif}"); return None

async def generate_gemini_text_response(prompt_parts: list) -> str:
    global GEMINI_API_UNAVAILABLE
    if not gemini_text_model_instance or GEMINI_API_UNAVAILABLE: return "Error: Gemini Text API is not available."
    try:
        response = await asyncio.to_thread(gemini_text_model_instance.generate_content, prompt_parts, request_options={'timeout': 120})
        if hasattr(response, 'text') and response.text: return response.text
        elif response.candidates: return f"Could not generate response. Reason: {response.candidates[0].finish_reason.name if response.candidates[0].finish_reason else 'Unknown'}"
        elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason: return f"Prompt blocked. Reason: {response.prompt_feedback.block_reason.name if response.prompt_feedback.block_reason else 'Unknown'}"
        else: print(f"Unexpected Gemini text response format: {response}"); return "Could not generate response. Unexpected format."
    except Exception as e: print(f"Gemini Text API Error: {type(e).__name__} - {e}"); traceback.print_exc(); return f"Gemini Text API Error: {type(e).__name__} - {e}"

async def generate_summary_with_gemini(text: str, num_points: int = 3) -> str:
    prompt = f"Summarize the following into {num_points} short bullet points:\n\n{text}"
    return await generate_gemini_text_response([prompt])

async def send_othello_board_message(channel: discord.TextChannel, game: OthelloGame, message_to_update: discord.Message = None, is_first_turn: bool = False, recruitment_message_content: str = None):
    if not game: return # Game object might be None if deleted
    game.calculate_valid_moves(game.current_player_color)
    p_black_id = game.players.get(BLACK); p_white_id = game.players.get(WHITE)
    current_player_id = game.get_current_player_id()
    try: p_black_user = await bot.fetch_user(p_black_id)
    except: p_black_user = None
    try: p_white_user = await bot.fetch_user(p_white_id)
    except: p_white_user = None
    try: current_player_user = await bot.fetch_user(current_player_id)
    except: current_player_user = None

    p_black_mention = f"{p_black_user.mention if p_black_user else f'ID:{p_black_id}'} (Pt: {get_player_points(p_black_id)})"
    p_white_mention = f"{p_white_user.mention if p_white_user else f'ID:{p_white_id}'} (Pt: {get_player_points(p_white_id)})"
    current_player_mention = current_player_user.mention if current_player_user else f"Player ID {current_player_id}"

    title_line = f"オセロゲーム #{game.game_id} | {BLACK_STONE} {p_black_mention} vs {WHITE_STONE} {p_white_mention}"
    content_lines = [title_line, ""] ; board_str = ""
    for r_idx in range(BOARD_SIZE):
        for c_idx in range(BOARD_SIZE):
            coord = (r_idx, c_idx)
            if not game.game_over and coord in game.valid_moves_with_markers: board_str += game.valid_moves_with_markers[coord]
            elif game.board[r_idx][c_idx] == BLACK: board_str += BLACK_STONE
            elif game.board[r_idx][c_idx] == WHITE: board_str += WHITE_STONE
            else: board_str += GREEN_SQUARE
        board_str += "\n"
    content_lines.append(f"{board_str.strip()}")
    black_score = sum(row.count(BLACK) for row in game.board); white_score = sum(row.count(WHITE) for row in game.board)
    content_lines.append(f"スコア: {BLACK_STONE} {black_score} - {WHITE_STONE} {white_score}")
    
    final_content = ""
    if game.game_over:
        winner_text = "引き分け"; points_changed_text = ""
        if game.winner_color != EMPTY:
            winner_id = game.players.get(game.winner_color)
            loser_id = game.players.get(WHITE if game.winner_color == BLACK else BLACK)
            try: winner_user = await bot.fetch_user(winner_id)
            except: winner_user = None
            winner_stone = BLACK_STONE if game.winner_color == BLACK else WHITE_STONE
            winner_text = f"{winner_stone} {(winner_user.mention if winner_user else f'ID:{winner_id}')} の勝ち！"
            score_diff = abs(black_score - white_score) if black_score != white_score else 0 # 引き分けは0点
            if winner_id and loser_id and score_diff > 0: # 勝敗がついた場合のみポイント変動
                update_player_points(winner_id, score_diff)
                update_player_points(loser_id, -score_diff)
                points_changed_text = f" ({winner_user.name if winner_user else f'ID:{winner_id}'} +{score_diff}pt, 他方 -{score_diff}pt)"
        game_over_lines = [title_line, "",f"{board_str.strip()}",f"スコア: {BLACK_STONE} {black_score} - {WHITE_STONE} {white_score}",f"**ゲーム終了！ {winner_text}**{points_changed_text}"]
        final_content = "\n".join(game_over_lines)
        if game.message_id and game.message_id in active_games:
            if active_games[game.message_id].afk_task and not active_games[game.message_id].afk_task.done():
                active_games[game.message_id].afk_task.cancel()
            OthelloGame._release_game_id(game.game_id) # game_id解放
            del active_games[game.message_id]
    elif recruitment_message_content:
        final_content = recruitment_message_content
    else:
        content_lines.append(f"手番: {current_player_mention}")
        final_content = "\n".join(content_lines)

    if message_to_update:
        try: await message_to_update.edit(content=final_content)
        except discord.HTTPException: print(f"Failed to edit othello message {message_to_update.id}")
    else: # 新規メッセージ送信
        try:
            message_to_update = await channel.send(content=final_content)
            if not recruitment_message_content: # ゲーム開始時
                game.message_id = message_to_update.id
                active_games[game.message_id] = game
        except discord.HTTPException: print(f"Failed to send othello message to channel {channel.id}"); return None
    
    if message_to_update and not game.game_over and not recruitment_message_content:
        current_reactions_on_msg = [str(r.emoji) for r in message_to_update.reactions if r.me]
        new_emojis_to_add = [LEAVE_GAME_EMOJI] + list(game.valid_moves_with_markers.values())
        
        to_remove = [e for e in current_reactions_on_msg if e not in new_emojis_to_add]
        to_add = [e for e in new_emojis_to_add if e not in current_reactions_on_msg]

        async def manage_reactions_task():
            for emoji_str in to_remove:
                try: await message_to_update.remove_reaction(emoji_str, bot.user)
                except: pass
            for emoji_str in to_add:
                try: await message_to_update.add_reaction(emoji_str)
                except: pass
        asyncio.create_task(manage_reactions_task())

    elif message_to_update and game.game_over:
         try: await message_to_update.clear_reactions()
         except (discord.Forbidden, discord.HTTPException): pass
    return message_to_update


def get_initial_board_text():
    temp_game = OthelloGame(0,0,0); temp_game.game_id = 0
    board_str = "";
    for r_idx in range(BOARD_SIZE):
        for c_idx in range(BOARD_SIZE):
            if temp_game.board[r_idx][c_idx] == BLACK: board_str += BLACK_STONE
            elif temp_game.board[r_idx][c_idx] == WHITE: board_str += WHITE_STONE
            else: board_str += GREEN_SQUARE
        board_str += "\n"
    return board_str.strip()


# =============================== DISCORD EVENT HANDLERS ===============================
@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name} ({bot.user.id})'); load_settings(); load_othello_points()
    print(f"Settings loaded. Allowed channels: {len(allowed_channels)}")
    print(f"Othello points loaded for {len(othello_points)} players.")
    gemini_status = "Not Available"
    if not GEMINI_API_UNAVAILABLE: gemini_status = f"Available (Text: {GEMINI_TEXT_MODEL_NAME})"
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
    if not cleanup_finished_games_task.is_running(): cleanup_finished_games_task.start()
    await bot.change_presence(activity=discord.Game(name="杉山啓太Bot")); print("Bot is ready.")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot or not message.guild: return

    # チャンネル制限: setchannel コマンド自体は常に許可
    if message.content.lower().startswith("setchannel"): # プレフィックスなしでsetchannelを処理
        ctx = await bot.get_context(message)
        command_obj = bot.get_command("setchannel")
        if command_obj:
            ctx.command = command_obj # 強制的にコマンドを割り当て
            await bot.invoke(ctx)
            return

    # 許可されていないチャンネルからのメッセージは無視 (スラッシュコマンドは除く)
    if message.channel.id not in allowed_channels:
        # ただし、スラッシュコマンドのインタラクションは on_message を通らないので別途制御は不要
        return

    # プレフィックスなしコマンドの処理
    content_lower = message.content.lower()
    command_parts = message.content.split(" ", 1)
    potential_command_name = command_parts[0].lower()

    command_obj = bot.get_command(potential_command_name)

    if command_obj:
        print(f"Prefix-less command '{potential_command_name}' detected from '{message.author.name}' in channel '{message.channel.name}'.")
        # commands.Context を作成してコマンドを実行
        # この方法では、引数パースはコマンド定義のパーサーに依存する
        # message.content をコマンド名で始まるように調整してコンテキストを作る
        
        # ダミープレフィックスを付けてコンテキストを再生成し、コマンドを起動
        # これにより、discord.py の引数パーサーが機能することを期待
        original_content = message.content
        message.content = BOT_COMMAND_PREFIX_DUMMY + original_content # 先頭にダミープレフィックス
        ctx = await bot.get_context(message)
        message.content = original_content # 元に戻す

        if ctx.command and ctx.command.name == command_obj.name:
            await bot.invoke(ctx)
        else:
            # うまくコンテキストが作れなかった場合 (引数パースなどが絡むと難しい)
            # 代替として、コマンド関数を直接呼び出すことを検討（引数の手動パースが必要）
            print(f"Could not invoke '{command_obj.name}' automatically. Manual call might be needed or check command parsing.")
            # 例: if command_obj.name == "totusi":
            # args = command_parts[1] if len(command_parts) > 1 else None
            # await command_obj.callback(await bot.get_context(message), text=args) # callbackを直接呼ぶ
    else:
        # 通常のメッセージ (コマンドではない)
        pass


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user == bot.user: return
    message = reaction.message; message_id = message.id

    if message_id in othello_recruitments:
        rec_info = othello_recruitments[message_id]; host_id = rec_info["host_id"]
        if str(reaction.emoji) == LEAVE_GAME_EMOJI and user.id == host_id:
            if message_id in othello_recruitments: del othello_recruitments[message_id]
            try: await message.edit(content=f"{user.mention}がオセロの募集を取り消しました。", view=None); await message.clear_reactions()
            except: pass
            return
        if str(reaction.emoji) == "✅" and user.id != host_id:
            if rec_info.get("opponent_id"):
                try: await reaction.remove(user); await user.send("この募集には既に対戦相手がいます。", delete_after=10)
                except: pass
                return
            rec_info["opponent_id"] = user.id
            if message_id in othello_recruitments: del othello_recruitments[message_id]
            players_list = [host_id, user.id]; random.shuffle(players_list)
            game = OthelloGame(player_black_id=players_list[0], player_white_id=players_list[1], channel_id=message.channel.id)
            # game.message_id は send_othello_board_message内で設定される
            await send_othello_board_message(message.channel, game, message_to_update=message, is_first_turn=True)
            if not game.game_over: game.afk_task = asyncio.create_task(othello_afk_timeout(game))
        elif user.id != host_id:
             try: await reaction.remove(user)
             except: pass
        return

    if message_id in active_games:
        game = active_games.get(message_id) # .get() を使う方が安全
        if not game: return # ゲームが何らかの理由で消えていたら何もしない

        if user.id not in game.players.values() or game.game_over:
            try: await reaction.remove(user)
            except: pass
            return
        
        if str(reaction.emoji) == LEAVE_GAME_EMOJI:
            if user.id in game.players.values():
                opponent_id = next(pid for color, pid in game.players.items() if pid != user.id) #相手を見つける
                
                game.game_over = True
                game.winner_color = next(color for color, pid in game.players.items() if pid == opponent_id) #離脱しなかった方

                try:
                    winner_user = await bot.fetch_user(opponent_id)
                    loser_user = await bot.fetch_user(user.id)
                    await message.channel.send(f"{loser_user.mention} がゲーム #{game.game_id} から離脱しました。{winner_user.mention} の勝利です！")
                except Exception as e_fetch: print(f"Error fetching users on leave: {e_fetch}")

                await send_othello_board_message(message.channel, game, message_to_update=message)
            try: await reaction.remove(user)
            except: pass
            return

        if user.id != game.get_current_player_id():
            try: await reaction.remove(user); await user.send("あなたの手番ではありません。", delete_after=5)
            except: pass
            return

        chosen_move = next((coord for coord, marker_emoji in game.valid_moves_with_markers.items() if str(reaction.emoji) == marker_emoji), None)
        if chosen_move:
            if game.make_move(chosen_move[0], chosen_move[1], game.current_player_color):
                if game.afk_task and not game.afk_task.done(): game.afk_task.cancel()
                game.switch_player()
                game.check_game_status()
                await send_othello_board_message(message.channel, game, message_to_update=message)
                if not game.game_over: game.afk_task = asyncio.create_task(othello_afk_timeout(game))
        try: await reaction.remove(user)
        except: pass

async def othello_afk_timeout(game: OthelloGame):
    await asyncio.sleep(OTHELLO_AFK_TIMEOUT_SECONDS)
    if game.message_id in active_games and active_games[game.message_id] == game and not game.game_over:
        print(f"Othello Game #{game.game_id}: AFK timeout for player {game.get_current_player_id()}")
        game.game_over = True
        # AFKしたプレイヤーの相手を見つける
        afk_player_color = game.current_player_color
        winner_player_color = WHITE if afk_player_color == BLACK else BLACK
        game.winner_color = winner_player_color
        
        try:
            channel = await bot.fetch_channel(game.channel_id)
            message = await channel.fetch_message(game.message_id)
            afk_player_id = game.players[afk_player_color]
            winner_player_id = game.players[winner_player_color]

            afk_player_user = await bot.fetch_user(afk_player_id)
            winner_player_user = await bot.fetch_user(winner_player_id)
            await channel.send(f"ゲーム #{game.game_id}: {afk_player_user.mention} が時間切れになりました。{winner_player_user.mention} の勝利です！")
            await send_othello_board_message(channel, game, message_to_update=message)
        except Exception as e:
            print(f"Error handling AFK timeout for game {game.game_id}: {e}")
            traceback.print_exc()


@tasks.loop(minutes=5)
async def cleanup_finished_games_task(): # Renamed to avoid conflict
    games_to_remove_ids = []
    for msg_id, game_obj in list(active_games.items()): # Iterate over a copy
        if game_obj.game_over:
            games_to_remove_ids.append(msg_id)
            if game_obj.afk_task and not game_obj.afk_task.done():
                game_obj.afk_task.cancel()
            OthelloGame._release_game_id(game_obj.game_id)
    
    for msg_id in games_to_remove_ids:
        if msg_id in active_games: # Check again, as it might have been removed by AFK timeout
            del active_games[msg_id]

    if games_to_remove_ids:
        print(f"Cleaned up {len(games_to_remove_ids)} finished othello games from active_games.")


# ================================== DISCORD COMMANDS ==================================
# !help (Commented out)
# @bot.command(name="help")
# async def help_prefix(ctx: commands.Context):
    # ... (Help command implementation)

# setchannel (Prefix-less handled in on_message)
@bot.command(name="setchannel")
@commands.has_permissions(administrator=True)
async def setchannel_command(ctx: commands.Context): # Renamed to avoid conflict if decorator used
    cid = ctx.channel.id
    if cid in allowed_channels:
        allowed_channels.remove(cid); await ctx.send(f"このチャンネルでのコマンド利用を**禁止**しました。")
    else:
        allowed_channels.add(cid); await ctx.send(f"このチャンネルでのコマンド利用を**許可**しました。")
    save_settings()

@setchannel_command.error # Match the new function name
async def setchannel_command_error(ctx, error): # Renamed
    if isinstance(error, commands.MissingPermissions): await ctx.send("管理者権限が必要です。")
    else: await ctx.send(f"エラー: {error}")

# watermark
@bot.command(name="watermark")
async def watermark_command(ctx: commands.Context, *args): # Use *args to accept content after command name
    if not ctx.message.attachments: return await ctx.send("画像を添付してください。")
    att = ctx.message.attachments[0]
    # ... (rest of the watermark logic from previous code)
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


# 5000
@bot.command(name="5000")
async def five_k_choyen_command(ctx: commands.Context, top_text: str = None, bottom_text: str = None, *options: str):
    # For prefix-less, args need to be parsed from message content if not using sophisticated on_message parsing
    # Assuming on_message will pass the rest of the content as a single string, or try to use converter
    # For now, let's assume the default discord.py parsing with dummy prefix handles it.
    # If top_text or bottom_text are not parsed correctly by the framework due to no prefix,
    # we'd need to get them from ctx.message.content.split() after "5000"
    
    # Simplified: if called via on_message + invoke, framework might handle args
    # If not, we need to parse message.content here if it's from a prefix-less call in on_message
    content_parts = ctx.message.content.split()
    if len(content_parts) < 3 and (top_text is None or bottom_text is None) : # Basic check
         # Try to parse from content if not automatically parsed
        if len(content_parts) >=3 and content_parts[0].lower() == "5000":
            top_text = content_parts[1]
            bottom_text = content_parts[2]
            options = tuple(content_parts[3:])
        else:
            return await ctx.send("上下の文字列を指定してください。\n例: `5000 すごい やった`")


    if top_text is None or bottom_text is None: return await ctx.send("上下の文字列を指定してください。\n例: `5000 すごい やった`")
    
    actual_options = []
    # Re-parse options if they were passed as *options by the framework
    # or extract from message content if needed
    if not options and len(ctx.message.content.split()) > 3 and ctx.message.content.split()[0].lower() == "5000":
        actual_options = [opt.lower() for opt in ctx.message.content.split()[3:]]
    elif options:
        actual_options = [opt.lower() for opt in options]


    params = {"top": top_text, "bottom": bottom_text, 
              "hoshii": "true" if "hoshii" in actual_options else "false", 
              "rainbow": "true" if "rainbow" in actual_options else "false"}
    url = f"https://gsapi.cbrx.io/image?{urllib.parse.urlencode(params)}"
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as s, s.get(url) as r:
                if r.status == 200:
                    embed = discord.Embed(title="5000兆円欲しい！", color=discord.Color.gold()).set_image(url=url)
                    await ctx.send(embed=embed)
                else: await ctx.send(f"画像生成失敗 (APIステータス: {r.status})")
        except Exception as e: await ctx.send(f"画像生成中にエラー: {e}")

# gaming
@bot.command(name="gaming")
async def gaming_command(ctx: commands.Context, *args): # Accept *args
    if not ctx.message.attachments: return await ctx.send("画像を添付してください。")
    # ... (rest of the gaming logic from previous code)
    attachment = ctx.message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image/"): return await ctx.send("画像ファイルを添付してください。")
    async with ctx.typing():
        image_bytes = await attachment.read()
        try:
            gif_buffer = await asyncio.to_thread(_create_gaming_gif, image_bytes)
            if gif_buffer is None: return await ctx.send("ゲーミングGIFの生成に失敗しました。")
            gif_buffer, resized = await _resize_image_if_too_large(gif_buffer, "GIF")
            if gif_buffer is None: return await ctx.send(f"ゲーミングGIFのリサイズ処理中にエラーが発生しました。")
            gif_buffer.seek(0, io.SEEK_END); file_size = gif_buffer.tell(); gif_buffer.seek(0)
            if file_size > MAX_FILE_SIZE_BYTES: return await ctx.send(f"生成GIFのファイルサイズが大きすぎます。")
            out_fname = f"gaming_{os.path.splitext(attachment.filename)[0]}.gif"
            await ctx.send(f"ゲーミング風GIFを生成しました！{' (リサイズ済)' if resized else ''}", file=discord.File(fp=gif_buffer, filename=out_fname))
        except Exception as e: await ctx.send(f"ゲーミングGIFの生成中にエラー: {e}")


# othello
@bot.command(name="othello")
async def othello_command(ctx: commands.Context, opponent_mention: str = None): # opponent is now a string
    host_id = ctx.author.id
    opponent: discord.Member = None

    if opponent_mention:
        try:
            # Try to convert mention string to Member object
            if opponent_mention.startswith("<@") and opponent_mention.endswith(">"):
                user_id = int(opponent_mention.strip("<@!>")) # Handles <@ID> and <@!ID>
                opponent = await ctx.guild.fetch_member(user_id)
            else: # Try to find by name#discriminator or just name/nick
                opponent = discord.utils.get(ctx.guild.members, name=opponent_mention)
                if not opponent:
                    opponent = discord.utils.get(ctx.guild.members, display_name=opponent_mention)

            if not opponent:
                await ctx.send(f"ユーザー「{opponent_mention}」が見つかりません。メンションまたは正確な名前で指定してください。")
                return
            if opponent == ctx.author :
                await ctx.send("自分自身とは対戦できません。")
                return
            if opponent.bot:
                await ctx.send("Botとは対戦できません。")
                return

        except ValueError: # Not a valid ID in mention
            await ctx.send(f"無効なメンション形式です: {opponent_mention}")
            return
        except discord.NotFound:
            await ctx.send(f"ユーザー「{opponent_mention}」がこのサーバーに見つかりません。")
            return
        except Exception as e:
            await ctx.send(f"相手ユーザーの指定処理中にエラー: {e}")
            return

    if opponent : # 即時対戦
        players_list = [host_id, opponent.id]; random.shuffle(players_list)
        game = OthelloGame(player_black_id=players_list[0], player_white_id=players_list[1], channel_id=ctx.channel.id)
        msg = await ctx.send(f"オセロゲーム #{game.game_id} を {ctx.author.mention} vs {opponent.mention} で開始します...")
        await send_othello_board_message(ctx.channel, game, message_to_update=msg, is_first_turn=True)
        if not game.game_over: game.afk_task = asyncio.create_task(othello_afk_timeout(game))
        return

    # 募集
    host_points = get_player_points(host_id)
    recruitment_text = (f"<サーバー内対戦> オセロ募集\n\n"
                        f"{get_initial_board_text()}\n\n"
                        f"{ctx.author.mention} (Pt: {host_points}) さんが対戦相手を募集しています。\n"
                        # f"ゲームID: (開始時に採番)\n" # IDは開始時に表示
                        f"対戦を受ける場合は ✅ でリアクションしてください。\n"
                        f"（募集者は {LEAVE_GAME_EMOJI} で募集を取り消せます）")
    try:
        msg = await ctx.send(recruitment_text)
        await msg.add_reaction("✅"); await msg.add_reaction(LEAVE_GAME_EMOJI)
        othello_recruitments[msg.id] = {"host_id": host_id, "channel_id": ctx.channel.id, "message_id": msg.id}
    except Exception as e: print(f"Othello recruitment message failed: {e}")

# othello_points
@bot.command(name="othello_points")
async def othello_points_command(ctx: commands.Context, *args): # Accept *args
    points = get_player_points(ctx.author.id)
    await ctx.send(f"{ctx.author.mention} あなたの現在のオセロポイントは {points}pt です。")


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

# voice
@bot.command(name="voice")
async def rvc_voice_convert_command(ctx: commands.Context, *args): # Accept *args
    if not ctx.message.attachments:
        await ctx.send("音声ファイルを添付してください。"); return
    # ... (rest of the voice logic from previous code)
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
        effective_python_executable = sys.executable 
        print(f"RVC用 (共有仮想環境の) Python実行ファイル: {effective_python_executable}")
        command = [effective_python_executable, rvc_infer_script_full_path, "--f0up_key", str(RVC_FIXED_TRANSPOSE), "--input_path", input_filepath_abs_rvc, "--opt_path", output_filepath_abs_rvc, "--model_name", RVC_MODEL_NAME_WITH_EXT,]
        if os.path.exists(rvc_index_full_path): command.extend(["--feature_path", rvc_index_full_path])
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
        await processing_message.edit(content=f"予期せぬエラーが発生しました: {e}"); print(f"予期せぬエラー (rvc_voice_convert_command): {e}"); traceback.print_exc()
    finally:
        if os.path.exists(input_filepath_abs_rvc):
            try: os.remove(input_filepath_abs_rvc)
            except Exception as e_rem: print(f"入力一時ファイルの削除に失敗: {e_rem}")
        if os.path.exists(output_filepath_abs_rvc):
            try: os.remove(output_filepath_abs_rvc)
            except Exception as e_rem: print(f"出力一時ファイルの削除に失敗: {e_rem}")


# ================================== NEW MISC COMMANDS ==================================
# ping
@bot.command(name="ping")
async def ping_command(ctx: commands.Context, *args):
    latency = bot.latency * 1000
    await ctx.send(f"ping＝{latency:.2f}ms")

# tenki / weather
@bot.command(name="tenki", aliases=["weather"])
async def weather_command(ctx: commands.Context, *, city_name_query: str = None): # Changed to city_name_query
    # Prefix-less: argument parsing from message content
    if city_name_query is None:
        parts = ctx.message.content.split(" ", 1)
        if len(parts) > 1:
            city_name_query = parts[1].strip()
        else:
            return await ctx.send("都市名を指定してください。例: `tenki 東京`")

    async with ctx.typing():
        city_id = None
        city_id_map = {"東京": "130010", "横浜": "140010", "大阪": "270000", "名古屋": "230010", "札幌": "016010", "福岡": "400010", "那覇": "471010", "仙台":"040010"}
        for name, id_val in city_id_map.items():
            if city_name_query in name or name in city_name_query : city_id = id_val; break
        
        if not city_id and not GEMINI_API_UNAVAILABLE:
            prompt = f"日本の天気予報APIで使える地名「{city_name_query}」を、もし曖昧なら最も代表的な都市名に修正し、その都市に対応するつくも天気APIの都市IDを調べてください。都市IDだけを数字で返してください。例: 東京なら130010"
            id_response = await generate_gemini_text_response([prompt])
            if not id_response.startswith("Error:") and id_response.strip().isdigit():
                city_id = id_response.strip(); print(f"Gemini suggested City ID for '{city_name_query}': {city_id}")
        
        if not city_id:
            await ctx.send(f"都市「{city_name_query}」の天気情報が見つかりませんでした。主要都市名で試すか、管理者に連絡してください。")
            return

        target_url = f"{WEATHER_API_BASE_URL}{city_id}" ; print(f"Fetching weather from: {target_url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("forecasts") and len(data["forecasts"]) > 0:
                            embed = discord.Embed(title=f"{data.get('location', {}).get('city', city_name_query)} の天気予報", color=discord.Color.blue())
                            embed.set_footer(text=f"情報源: {data.get('publicTimeFormatted', '')} つくも様")
                            for i, forecast in enumerate(data["forecasts"][:3]):
                                date = forecast.get("dateLabel", "不明") + f" ({forecast.get('date')[-5:]})" #日付を短縮
                                weather_telop = forecast.get("telop", "情報なし")
                                temp_max = forecast.get("temperature", {}).get("max", {}).get("celsius", "--")
                                temp_min = forecast.get("temperature", {}).get("min", {}).get("celsius", "--")
                                value_str = f"{weather_telop} (最高:{temp_max}°C / 最低:{temp_min}°C)"
                                embed.add_field(name=date, value=value_str, inline=False)
                            await ctx.send(embed=embed)
                        else: await ctx.send(f"「{city_name_query}」(ID:{city_id}) の天気予報データを取得できませんでした。")
                    else: await ctx.send(f"天気情報の取得に失敗 (HTTP: {response.status})。都市名/ID: {city_name_query}/{city_id}")
        except Exception as e: await ctx.send(f"天気情報取得エラー: {e}"); traceback.print_exc()

# info
@bot.command(name="info")
async def user_info_command(ctx: commands.Context, *, member_query: str = None): # Changed to query string
    member: discord.Member = None
    if member_query:
        try:
            if member_query.startswith("<@") and member_query.endswith(">"):
                user_id = int(member_query.strip("<@!>"))
                member = await ctx.guild.fetch_member(user_id)
            else: # Try to find by name or nick
                member = discord.utils.get(ctx.guild.members, name=member_query)
                if not member: member = discord.utils.get(ctx.guild.members, display_name=member_query)
                if not member: # Try ID directly
                    try: member_id = int(member_query); member = await ctx.guild.fetch_member(member_id)
                    except ValueError: pass # Not an ID
        except discord.NotFound: pass # Handled below
        except Exception as e_fetch: print(f"Error fetching member {member_query}: {e_fetch}")
    
    if member is None and member_query : # If query was given but member not found
        return await ctx.send(f"ユーザー「{member_query}」が見つかりません。メンション、ID、または正確な名前で指定してください。")
    elif member is None: # No query, use ctx.author
        member = ctx.author

    embed = discord.Embed(title=f"{member.display_name} の情報", color=member.color or discord.Color.default())
    if member.avatar: embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="ユーザー名", value=f"{member.name}#{member.discriminator}", inline=True)
    embed.add_field(name="ニックネーム", value=member.nick or "なし", inline=True)
    embed.add_field(name="ID", value=member.id, inline=False)
    created_at_jst = member.created_at.astimezone(JST)
    joined_at_jst = member.joined_at.astimezone(JST) if member.joined_at else None
    embed.add_field(name="アカウント作成日時", value=f"{created_at_jst.strftime('%Y年%m月%d日 %H:%M')} JST", inline=False)
    if joined_at_jst: embed.add_field(name="サーバー参加日時", value=f"{joined_at_jst.strftime('%Y年%m月%d日 %H:%M')} JST ({ (datetime.datetime.now(JST) - joined_at_jst).days }日前)", inline=False)
    roles = [role.mention for role in sorted(member.roles, key=lambda r: r.position, reverse=True) if role.name != "@everyone"]
    if roles: embed.add_field(name=f"ロール ({len(roles)})", value=" ".join(roles)[:1020] + ("..." if len(" ".join(roles)) > 1020 else ""), inline=False)
    else: embed.add_field(name="ロール", value="なし", inline=False)
    badges = []
    flags = member.public_flags
    if flags.staff: badges.append(USER_BADGES_EMOJI.get("staff", "👑"))
    if flags.partner: badges.append(USER_BADGES_EMOJI.get("partner", "🤝"))
    if flags.hypesquad: badges.append(USER_BADGES_EMOJI.get("hypesquad", "🎉"))
    if flags.bug_hunter: badges.append(USER_BADGES_EMOJI.get("bug_hunter_level_1", "🐛"))
    if flags.bug_hunter_level_2: badges.append(USER_BADGES_EMOJI.get("bug_hunter_level_2", "🐞"))
    if flags.hypesquad_bravery: badges.append(USER_BADGES_EMOJI.get("hypesquad_bravery", "⚔️"))
    if flags.hypesquad_brilliance: badges.append(USER_BADGES_EMOJI.get("hypesquad_brilliance", "💡"))
    if flags.hypesquad_balance: badges.append(USER_BADGES_EMOJI.get("hypesquad_balance", "⚖️"))
    if flags.early_supporter: badges.append(USER_BADGES_EMOJI.get("early_supporter", "💎"))
    if flags.team_user: pass # Typically not displayed
    if flags.verified_bot: badges.append(USER_BADGES_EMOJI.get("verified_bot", "🤖")) # Only for bots
    if flags.early_verified_bot_developer: badges.append(USER_BADGES_EMOJI.get("early_verified_bot_developer", "🔧"))
    if flags.discord_certified_moderator: badges.append(USER_BADGES_EMOJI.get("discord_certified_moderator", "🛡️"))
    if flags.active_developer: badges.append(USER_BADGES_EMOJI.get("active_developer", "👨‍💻"))
    if badges: embed.add_field(name="バッジ", value=" ".join(badges) or "なし", inline=False)
    else: embed.add_field(name="バッジ", value="なし", inline=False)
    if isinstance(member, discord.Member) and member.premium_since:
        boost_since_jst = member.premium_since.astimezone(JST)
        boost_duration = datetime.datetime.now(JST) - boost_since_jst
        embed.add_field(name="サーバーブースト開始日", value=f"{boost_since_jst.strftime('%Y年%m月%d日')} JST ({boost_duration.days}日前)", inline=False)
    await ctx.send(embed=embed)

# rate
@bot.command(name="rate")
async def exchange_rate_command(ctx: commands.Context, *, query: str = None): # Changed to single query string
    if not query: return await ctx.send("金額と通貨コードを指定してください。例: `rate 150 USD`")
    parts = query.split()
    if len(parts) < 2: return await ctx.send("金額と通貨コードを正しく指定してください。例: `rate 150 USD`")
    amount_str = parts[0]; currency_code = parts[1].upper()
    try: amount = float(amount_str)
    except ValueError: return await ctx.send("金額は数値で指定してください。")
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(EXCHANGE_RATE_API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates")
                        if rates and currency_code in rates and "JPY" in rates:
                            rate_to_jpy_for_usd = rates["JPY"]
                            rate_for_target_currency_to_usd = rates[currency_code]
                            amount_in_jpy = (amount / rate_for_target_currency_to_usd) * rate_to_jpy_for_usd
                            await ctx.send(f"{amount:,.2f} {currency_code} は約 **{amount_in_jpy:,.2f} 円** です。")
                        elif rates: await ctx.send(f"通貨「{currency_code}」のレートが見つからないか、JPYレートがありません。")
                        else: await ctx.send("為替レートデータを取得できませんでした。")
                    else: await ctx.send(f"為替レートAPIアクセス失敗 (HTTP: {response.status})")
        except Exception as e: await ctx.send(f"為替レート変換エラー: {e}"); traceback.print_exc()

# shorturl
@bot.command(name="shorturl")
async def shorturl_command(ctx: commands.Context, *, url_to_shorten: str = None): # Changed to single query string
    if not url_to_shorten:
        parts = ctx.message.content.split(" ", 1)
        if len(parts) > 1: url_to_shorten = parts[1].strip()
        else: return await ctx.send("短縮するURLを指定してください。")
    if not SHORTURL_API_KEY or SHORTURL_API_KEY == "YOUR_XGD_API_KEY_PLACEHOLDER":
        return await ctx.send("短縮URL機能のAPIキー未設定。")
    if not (url_to_shorten.startswith("http://") or url_to_shorten.startswith("https://")):
        url_to_shorten = "http://" + url_to_shorten
    params = {"key": SHORTURL_API_KEY, "url": url_to_shorten}
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(SHORTURL_API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.text()
                        if data.startswith("http://x.gd/") or data.startswith("https://x.gd/"): await ctx.send(f"短縮URL: {data}")
                        else: await ctx.send(f"URL短縮失敗。API応答: `{data}`")
                    else: error_text = await response.text(); await ctx.send(f"URL短縮API失敗 (HTTP: {response.status})。応答: `{error_text}`")
        except Exception as e: await ctx.send(f"URL短縮エラー: {e}"); traceback.print_exc()

# totusi
@bot.command(name="totusi")
async def totusi_command(ctx: commands.Context, *, text: str = None): # Changed to single query string
    if text is None: # Prefix-less call might make text None if not parsed from on_message
        parts = ctx.message.content.split(" ", 1)
        if len(parts) > 1: text = parts[1].strip()
        else: return await ctx.send("文字列を指定してください。例: `totusi テスト`")
    if not text: return await ctx.send("文字列を指定してください。")
    text = text.replace("　", " ")
    # For multi-byte characters, simple len() might not be ideal for visual width
    # but for this AA, character count is usually fine.
    char_count = 0
    for char_ in text:
        if unicodedata.east_asian_width(char_) in ('F', 'W', 'A'): # Fullwidth, Wide, Ambiguous
            char_count += 2
        else:
            char_count += 1
    
    # Adjust arrow length based on estimated visual width
    arrow_len = math.ceil(char_count / 2) # Each 人人 is roughly 2 chars wide
    if arrow_len < 3: arrow_len = 3 # Minimum length
    if arrow_len > 12: arrow_len = 12 # Maximum length

    line1 = "＿" + "人" * (arrow_len) + "＿"
    line2 = "＞　" + f"**{text}**" + "　＜"
    line3 = "￣" + ("Y^" * (arrow_len)) + "Y￣"
    result = f"{line1}\n{line2}\n{line3}"
    await ctx.send(result)


# =================================== BOT EXECUTION ====================================
if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_PLACEHOLDER" or not DISCORD_BOT_TOKEN:
        print("致命的なエラー: DISCORD_BOT_TOKEN が .env ファイルに設定されていないか、プレースホルダーのままです。")
        print(f"{os.path.join(os.path.dirname(__file__), '.env')} ファイルを作成し、DISCORD_BOT_TOKEN=\"あなたのトークン\" と記述してください。")
        exit(1)
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_PLACEHOLDER" or not GEMINI_API_KEY:
        print("警告: GEMINI_API_KEY が .env ファイルに設定されていないか、プレースホルダーのままです。Gemini関連機能は利用できません。")
    if SHORTURL_API_KEY == "YOUR_XGD_API_KEY_PLACEHOLDER" or not SHORTURL_API_KEY:
        print("警告: SHORTURL_API_KEY が .env ファイルに設定されていないか、プレースホルダーのままです。'shorturl' コマンドは利用できません。")
    
    missing_deps = []
    try: import numpy
    except ImportError: missing_deps.append("numpy")
    try: from PIL import Image
    except ImportError: missing_deps.append("Pillow")
    
    if missing_deps:
        print(f"警告: 以下の必須ライブラリが Bot用仮想環境 にインストールされていません: {', '.join(missing_deps)}")
        print(f"共有仮想環境 (C:\\Bot\\RVC_Project\\venv) を有効化して `pip install {' '.join(missing_deps)}` を実行してください。")

    print("Botを起動します...")
    try:
        load_othello_points()
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure: print("エラー: Discord Botトークンが無効です。トークンを確認してください。")
    except Exception as e: print(f"Bot実行中に予期せぬエラーが発生しました: {e}"); traceback.print_exc()
