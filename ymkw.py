# ========================== IMPORTS ==========================
import os
import sys
import discord
from discord.ext import commands, tasks
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
import traceback
import unicodedata
import xml.etree.ElementTree as ET
import pytz
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError 

# ========================== CONFIGURATION & INITIALIZATION ==========================
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_BASE_URL = "https://weather.tsukumijima.net/api/forecast/city/"
PRIMARY_AREA_XML_URL = "https://weather.tsukumijima.net/primary_area.xml"
EXCHANGE_RATE_API_URL = "https://exchange-rate-api.krnk.org/api/rate"
SHORTURL_API_ENDPOINT = "https://xgd.io/V1/shorten"
SHORTURL_API_KEY = os.getenv("SHORTURL_API_KEY")
AMAZON_SHORTURL_ENDPOINT = "https://www.amazon.co.jp/associates/sitestripe/getShortUrl"


_DUMMY_PREFIX_VALUE = "!@#$%^&SUGIYAMA_BOT_DUMMY_PREFIX_XYZ_VERY_UNIQUE"
def get_dummy_prefix(bot, message):
    return _DUMMY_PREFIX_VALUE

SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), "bot_settings.json")
OTHELLO_POINTS_FILE_PATH = os.path.join(os.path.dirname(__file__), "othello_points.json")
WEATHER_CITY_CODES_FILE_PATH = os.path.join(os.path.dirname(__file__), "weather_city_codes.json")
allowed_channels = set()
othello_points = {}
weather_city_id_map = {}
JST = pytz.timezone("Asia/Tokyo")

MAX_FILE_SIZE_BYTES = int(4.8 * 1024 * 1024)
MIN_IMAGE_DIMENSION = 300
TEMPLATES_BASE_PATH = os.path.join(os.path.dirname(__file__), "assets", "watermark_templates")
TEMPLATES_DATA = [ 
    {"name": "POCO F3.png", "user_ratio_str": "3/4", "target_size": (3000, 4000)},
    {"name": "GalaxyS23 2.png", "user_ratio_str": "563/1000", "target_size": (2252, 4000)},
    {"name": "IPHONE 11 PRO MAX.png", "user_ratio_str": "672/605", "target_size": (4032, 3630)},
    {"name": "motorola eage 50s pro.png", "user_ratio_str": "4/3", "target_size": (4096, 3072)},
    {"name": "XIAOMI 15 Ultra 1.png", "user_ratio_str": "320/277", "target_size": (1280, 1108)}, 
    {"name": "Galaxy S23.png", "user_ratio_str": "1000/563", "target_size": (4000, 2252)},
    {"name": "XIAOMI13.png", "user_ratio_str": "512/329", "target_size": (4096, 2632)},
    {"name": "Vivo X200 Pro.png", "user_ratio_str": "512/329", "target_size": (4096, 2632)},
    {"name": "OPPO Find X5 2.png", "user_ratio_str": "512/439", "target_size": (4096, 3512)},
    {"name": "OPPO Find X5.png", "user_ratio_str": "3/4", "target_size": (1080, 1440)},
    {"name": "NIKON1J5.png", "user_ratio_str": "548/461", "target_size": (4384, 3688)},
    {"name": "REDMAGIC9PRO.png", "user_ratio_str": "9/13", "target_size": (3060, 4420)},
    {"name": "REDMI121.png", "user_ratio_str": "64/85", "target_size": (3072, 4080)},
    {"name": "REDMI122.png", "user_ratio_str": "85/64", "target_size": (4080, 3072)},
    {"name": "OPPOFINDX5PRO.png", "user_ratio_str": "256/363", "target_size": (3072, 4356)},
    {"name": "ONELINE.png", "user_ratio_str": "3175/2458", "target_size": (6530, 4916)},
    {"name": "NOTHINGPHONE2A.png", "user_ratio_str": "3265/2458", "target_size": (6530, 4916)}, 
    {"name": "VIVOX60TPRO2.png", "user_ratio_str": "3/4", "target_size": (3000, 4000)},
    {"name": "VIVOX60TPRO.png", "user_ratio_str": "4/3", "target_size": (4080, 3060)},
    {"name": "ONEPLUS11R5G.png", "user_ratio_str": "8/7", "target_size": (8192, 7168)},
    {"name": "XIAOMI15ULTRA 3.png", "user_ratio_str": "1151/1818", "target_size": (2302, 3636)},
    {"name": "XIAOMI15ULTRA 2.png", "user_ratio_str": "568/503", "target_size": (4544, 4024)} 
]

GREEN_SQUARE = "<:o_0:1380626312976138400>"
BLACK_STONE  = "<:o_2:1380626308383510548>"
WHITE_STONE  = "<:o_1:1380626310551830580>"
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
    "active_developer": "<:activedeveloper:1383253229189730374>",
    # "originally_known_as": "<:originally:1383252913379479603>", # No direct PublicUserFlags attribute
    "nitro": "<:nitro:1383252018532974642>",
    # "automod_rule_create": "<:automod:1383251827734089868>", # No direct PublicUserFlags attribute
    # "supports_slash_commands": "<:slashcommand:1383251808436224145>", # No direct PublicUserFlags attribute
    "hypesquad_balance": "<:balance:1383251792413851688>",
    "hypesquad_bravery": "<:bravery:1383251749623693392>",
    "hypesquad_brilliance": "<:brilliance:1383251723610624174>",
    "premium": "<:booster:1383251702144176168>", # For Nitro/Booster status
    "partner": "<:partnerserver:1383251682070364210>",
    # "has_had_quests_enabled": "<:quest:1383251665104142376>", # No direct PublicUserFlags attribute
    "early_verified_bot_developer": "<:earlyverifiedbot:1383251648348160030>",
    "bug_hunter": "<:bugHunter:1383251633567170683>", # For level 1
    "bug_hunter_level_2": "<:bugHunter:1383251633567170683>", # Using same for level 2, replace if different emoji exists
    "early_supporter": "<:earlysupporter:1383251618379727031>",
    "staff": "<:staff:1383251602680578111>",
    "discord_certified_moderator": "<:moderator:1383251587438215218>",
    "verified_bot": "✅" # Generic, if specific not found
}

TIMEZONE_MAP = {
    "JP": "Asia/Tokyo", "US": "America/New_York", "GB": "Europe/London", "EU": "Europe/Brussels",
    "DE": "Europe/Berlin", "FR": "Europe/Paris", "IT": "Europe/Rome", "CA": "America/Toronto",
    "AU": "Australia/Sydney", "CN": "Asia/Shanghai", "IN": "Asia/Kolkata", "BR": "America/Sao_Paulo",
    "RU": "Europe/Moscow", "KR": "Asia/Seoul", "ZA": "Africa/Johannesburg", "MX": "America/Mexico_City",
    "ID": "Asia/Jakarta", "TR": "Europe/Istanbul", "SA": "Asia/Riyadh", "AR": "America/Argentina/Buenos_Aires",
    "ES": "Europe/Madrid", "NL": "Europe/Amsterdam",
    "US-PST": "America/Los_Angeles", "US-CST": "America/Chicago", "US-MST": "America/Denver"
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
bot = commands.Bot(command_prefix=get_dummy_prefix, intents=intents, help_command=None)

os.makedirs(RVC_INPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(RVC_OUTPUT_AUDIO_DIR, exist_ok=True)

# ================================= GAME LOGIC (OTHELLO) & HELPERS =================================
EMPTY = 0; BLACK = 1; WHITE = 2; BOARD_SIZE = 8
class OthelloGame:
    _next_game_id_counter = 1
    _active_game_ids = set()

    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.board[3][3] = WHITE; self.board[3][4] = BLACK
        self.board[4][3] = BLACK; self.board[4][4] = WHITE
        self.current_player = BLACK
        self.valid_moves_with_markers = {}
        self.game_over = False; self.winner = None; self.last_pass = False
        self.players = {}
        self.channel_id = None
        self.last_move_time = datetime.datetime.now(JST)
        self.game_id = OthelloGame._assign_game_id_static()
        self.afk_task: asyncio.Task = None

    @staticmethod
    def _assign_game_id_static():
        gid = 1
        while gid in OthelloGame._active_game_ids: gid += 1
        OthelloGame._active_game_ids.add(gid); print(f"Assigned Game ID: {gid}"); return gid
    @staticmethod
    def _release_game_id_static(gid):
        if gid in OthelloGame._active_game_ids: OthelloGame._active_game_ids.remove(gid); print(f"Released Game ID: {gid}")

    def is_on_board(self, r, c): return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE
    def get_flips(self, r_s, c_s, p):
        if not self.is_on_board(r_s, c_s) or self.board[r_s][c_s] != EMPTY: return []
        op = WHITE if p == BLACK else BLACK; ttf = []
        for dr, dc in [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]:
            r,c = r_s+dr, c_s+dc; cpf=[]
            while self.is_on_board(r,c) and self.board[r][c]==op: cpf.append((r,c)); r+=dr; c+=dc
            if self.is_on_board(r,c) and self.board[r][c]==p and cpf: ttf.extend(cpf)
        return ttf
    def calculate_valid_moves(self, p):
        self.valid_moves_with_markers.clear(); mi=0; cvc=[]
        for r_idx in range(BOARD_SIZE):
            for c_idx in range(BOARD_SIZE):
                if self.board[r_idx][c_idx]==EMPTY and self.get_flips(r_idx,c_idx,p):
                    cvc.append((r_idx,c_idx))
                    if mi < len(MARKERS): self.valid_moves_with_markers[(r_idx,c_idx)]=MARKERS[mi]; mi+=1
        return cvc
    def make_move(self, r, c, p):
        if self.game_over: return False
        if not self.is_on_board(r,c) or self.board[r][c]!=EMPTY: return False
        ttf = self.get_flips(r,c,p)
        if not ttf: return False
        self.board[r][c]=p
        for fr,fc in ttf: self.board[fr][fc]=p
        self.last_pass=False; self.last_move_time = datetime.datetime.now(JST); return True
    def switch_player(self): self.current_player = WHITE if self.current_player==BLACK else BLACK
    def check_game_status(self):
        if self.game_over: return
        if self.calculate_valid_moves(self.current_player): self.last_pass=False; return
        if self.last_pass: self.game_over=True
        else:
            self.last_pass=True; self.switch_player()
            if not self.calculate_valid_moves(self.current_player): self.game_over=True
        if self.game_over: self.determine_winner()
    def determine_winner(self):
        bs=sum(r.count(BLACK) for r in self.board); ws=sum(r.count(WHITE) for r in self.board)
        if bs > ws: self.winner=BLACK
        elif ws > bs: self.winner=WHITE
        else: self.winner=EMPTY
    def get_current_player_id(self): return self.players.get(self.current_player)
    def get_opponent_player_id(self): return self.players.get(WHITE if self.current_player==BLACK else BLACK)

def get_initial_board_text():
    temp_game = OthelloGame(); temp_game.game_id = 0
    board_str = "";
    for r_idx in range(BOARD_SIZE):
        for c_idx in range(BOARD_SIZE):
            if temp_game.board[r_idx][c_idx] == BLACK: board_str += BLACK_STONE
            elif temp_game.board[r_idx][c_idx] == WHITE: board_str += WHITE_STONE
            else: board_str += GREEN_SQUARE
        board_str += "\n"
    return board_str.strip()

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
    except json.JSONDecodeError:
        print(f"Othello points file is empty or corrupted. Initializing fresh: {OTHELLO_POINTS_FILE_PATH}")
        othello_points = {}; save_othello_points()
    except Exception as e: print(f"Othello points load error: {e}"); othello_points = {}

def save_othello_points():
    try:
        with open(OTHELLO_POINTS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(othello_points, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Othello points save error: {e}")

def get_player_points(player_id: int) -> int:
    return othello_points.get(str(player_id), 0)

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
        elif response.candidates and response.candidates[0].finish_reason: return f"Could not generate response. Reason: {response.candidates[0].finish_reason.name}"
        elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason: return f"Prompt blocked. Reason: {response.prompt_feedback.block_reason.name}"
        else: print(f"Unexpected Gemini text response format: {response}"); return "Could not generate response. Unexpected format."
    except Exception as e: print(f"Gemini Text API Error: {type(e).__name__} - {e}"); traceback.print_exc(); return f"Gemini Text API Error: {type(e).__name__} - {e}"

async def generate_summary_with_gemini(text: str, num_points: int = 3) -> str:
    prompt = f"以下の文章を日本語で{num_points}個の短い箇条書きに要約してください:\n\n{text}"
    return await generate_gemini_text_response([prompt])

async def send_othello_board_message(channel: discord.TextChannel, game_session: dict, message_to_update: discord.Message, is_first_turn: bool = False, recruitment_message_content: str = None):
    game = game_session["game"]
    if not game.game_over:
        game.calculate_valid_moves(game.current_player)

    p_black_id = game_session["players"].get(BLACK)
    p_white_id = game_session["players"].get(WHITE)
    current_player_id_from_session = game_session["players"].get(game.current_player)

    try: p_black_user = await bot.fetch_user(p_black_id) if p_black_id else None
    except: p_black_user = None
    try: p_white_user = await bot.fetch_user(p_white_id) if p_white_id else None
    except: p_white_user = None
    try: current_player_user = await bot.fetch_user(current_player_id_from_session) if current_player_id_from_session else None
    except: current_player_user = None

    p_black_mention = f"{p_black_user.mention if p_black_user else f'Player Black (ID:{p_black_id})'} (Pt: {get_player_points(p_black_id)})"
    p_white_mention = f"{p_white_user.mention if p_white_user else f'Player White (ID:{p_white_id})'} (Pt: {get_player_points(p_white_id)})"
    current_player_mention = current_player_user.mention if current_player_user else f"Player (ID:{current_player_id_from_session})"

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
    black_score = sum(r.count(BLACK) for r in game.board); white_score = sum(r.count(WHITE) for r in game.board)
    content_lines.append(f"スコア: {BLACK_STONE} {black_score} - {WHITE_STONE} {white_score}")
    
    final_content_str = ""
    if game.game_over:
        winner_text = "引き分け"; points_changed_text = ""
        if game.winner != EMPTY:
            winner_id = game_session["players"].get(game.winner)
            loser_id = game_session["players"].get(WHITE if game.winner == BLACK else BLACK)
            try: winner_user = await bot.fetch_user(winner_id) if winner_id else None
            except: winner_user = None
            winner_stone = BLACK_STONE if game.winner == BLACK else WHITE_STONE
            winner_text = f"{winner_stone} {(winner_user.mention if winner_user else f'ID:{winner_id}')} の勝ち！"
            if not getattr(game, 'ended_by_action', False): 
                score_diff = abs(black_score - white_score) if black_score != white_score else 0
                if winner_id and loser_id and score_diff > 0:
                    update_player_points(winner_id, score_diff); update_player_points(loser_id, -score_diff)
                    points_changed_text = f" ({winner_user.name if winner_user else f'ID:{winner_id}'} +{score_diff}pt, 他方 -{score_diff}pt)"
        game_over_lines = [title_line, "",f"{board_str.strip()}",f"スコア: {BLACK_STONE} {black_score} - {WHITE_STONE} {white_score}",f"**ゲーム終了！ {winner_text}**{points_changed_text}"]
        final_content_str = "\n".join(game_over_lines)
        
        if message_to_update.id in active_games:
            game_session_data = active_games.get(message_to_update.id)
            if game_session_data:
                game_obj_to_clean = game_session_data.get("game")
                if game_obj_to_clean and game_obj_to_clean.afk_task and not game_obj_to_clean.afk_task.done():
                    game_obj_to_clean.afk_task.cancel()
                OthelloGame._release_game_id_static(game.game_id)
                del active_games[message_to_update.id]
    elif recruitment_message_content:
        final_content_str = recruitment_message_content
    else:
        content_lines.append(f"手番: {current_player_mention}")
        final_content_str = "\n".join(content_lines)

    if message_to_update:
        try: await message_to_update.edit(content=final_content_str)
        except discord.HTTPException: print(f"Failed to edit othello message {message_to_update.id}")
    
    if message_to_update and game and not game.game_over and not recruitment_message_content:
        current_bot_reactions = [str(r.emoji) for r in message_to_update.reactions if r.me]
        new_valid_markers_emojis = list(game.valid_moves_with_markers.values())

        to_add = [emoji for emoji in new_valid_markers_emojis if emoji not in current_bot_reactions]
        to_remove = [emoji for emoji in current_bot_reactions if emoji not in new_valid_markers_emojis]
        
        if is_first_turn:
            try: await message_to_update.clear_reactions()
            except (discord.Forbidden, discord.HTTPException): pass
            to_add = new_valid_markers_emojis
            to_remove = []

        async def manage_reactions_task():
            for emoji_str in to_remove:
                try: await message_to_update.remove_reaction(emoji_str, bot.user)
                except: pass
            for emoji_str in to_add:
                try: await message_to_update.add_reaction(emoji_str)
                except: pass
        asyncio.create_task(manage_reactions_task())

    elif message_to_update and game and game.game_over:
         try: await message_to_update.clear_reactions()
         except (discord.Forbidden, discord.HTTPException): pass
    return message_to_update

# =============================== DISCORD EVENT HANDLERS ===============================
async def load_weather_city_codes():
    global weather_city_id_map
    if os.path.exists(WEATHER_CITY_CODES_FILE_PATH):
        try:
            with open(WEATHER_CITY_CODES_FILE_PATH, 'r', encoding='utf-8') as f:
                weather_city_id_map = json.load(f)
            if weather_city_id_map:
                print(f"Loaded {len(weather_city_id_map)} weather city codes from local cache.")
                return
        except Exception as e: print(f"Error loading cached city codes: {e}")
    print("Fetching weather city codes from API as local cache not found or empty...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PRIMARY_AREA_XML_URL) as response:
                if response.status == 200:
                    xml_text = await response.text()
                    root = ET.fromstring(xml_text)
                    temp_map = {}
                    for pref_element in root.findall('.//pref'):
                        for city_element in pref_element.findall('.//city'):
                            city_title = city_element.get('title')
                            city_id = city_element.get('id')
                            if city_title and city_id:
                                temp_map[city_title] = city_id
                                pref_title = pref_element.get('title')
                                if pref_title and pref_title != city_title:
                                    temp_map[f"{pref_title}{city_title}"] = city_id
                    weather_city_id_map = temp_map
                    with open(WEATHER_CITY_CODES_FILE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(weather_city_id_map, f, ensure_ascii=False, indent=2)
                    print(f"Successfully fetched and cached {len(weather_city_id_map)} city codes.")
                else: print(f"Failed to fetch city codes from API: HTTP {response.status}")
    except Exception as e: print(f"Error fetching or parsing city codes from API: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name} ({bot.user.id})'); load_settings(); load_othello_points()
    await load_weather_city_codes()
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
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="help"))
    print("Bot is ready.")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot or not message.guild:
        return

    original_content = message.content
    content_lower_stripped = original_content.strip().lower()
    
    # 'setchannel' コマンドは常に処理
    if content_lower_stripped.startswith("setchannel"):
        _content_backup = message.content
        message.content = f"{get_dummy_prefix(bot, message)}setchannel"
        await bot.process_commands(message)
        message.content = _content_backup
        return

    # 許可されていないチャンネルからのメッセージは無視
    if message.channel.id not in allowed_channels:
        return

    # プレフィックスなしコマンドの処理
    command_parts = original_content.split(" ", 2) # 最大2回分割してサブコマンドまで考慮
    potential_command_name = command_parts[0].lower()
    
    # オセロのサブコマンド風呼び出しに対応
    is_othello_subcommand = False
    if potential_command_name == "othello" and len(command_parts) > 1:
        sub_command_name = command_parts[1].lower()
        if sub_command_name == "leave":
            potential_command_name = "leave"
            is_othello_subcommand = True
        elif sub_command_name == "point" or sub_command_name == "points":
            potential_command_name = "othello_points"
            is_othello_subcommand = True
        # "othello @mention" の場合は potential_command_name は "othello" のまま
    
    command_obj = bot.get_command(potential_command_name)

    if command_obj:
        print(f"Prefix-less command '{potential_command_name}' detected from '{message.author.name}'. Processing...")
        _content_backup_cmd = message.content
        
        args_for_command = ""
        if is_othello_subcommand: # othello leave, othello point の場合
            # これらのコマンドは引数を取らないので、引数部分は空
            pass
        elif potential_command_name == "othello" and len(command_parts) > 1: # othello @mention の場合
            args_for_command = command_parts[1] # メンション部分
        elif len(command_parts) > 1 : # その他のコマンドで引数がある場合
            args_for_command = command_parts[1]

        message.content = f"{get_dummy_prefix(bot, message)}{potential_command_name} {args_for_command}".strip()
        
        print(f"  Modified message content for processing: '{message.content}'")
        await bot.process_commands(message)
        message.content = _content_backup_cmd

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user == bot.user: return
    message = reaction.message; message_id = message.id

    if message_id in othello_recruitments:
        rec_info = othello_recruitments[message_id]
        host_id = rec_info["host_id"]
        if str(reaction.emoji) == "❌" and user.id == host_id:
            if message_id in othello_recruitments: del othello_recruitments[message_id]
            try:
                await message.edit(content=f"{user.mention}がオセロの募集を取り消しました。", view=None)
                await message.clear_reactions()
            except discord.HTTPException: pass
            return
        if str(reaction.emoji) == "✅" and user.id != host_id:
            if rec_info.get("opponent_id"):
                try: await reaction.remove(user)
                except discord.HTTPException: pass
                return
            rec_info["opponent_id"] = user.id
            players_list = [host_id, user.id]; random.shuffle(players_list)
            game_instance = OthelloGame()
            game_instance.players = {BLACK: players_list[0], WHITE: players_list[1]}
            game_instance.channel_id = message.channel.id
            game_session = {"game": game_instance, "players": game_instance.players, "host_id": host_id, "channel_id": message.channel.id}
            
            active_games[message_id] = game_session 
            game_instance.message_id = message_id
            if message_id in othello_recruitments: del othello_recruitments[message_id]

            await send_othello_board_message(message.channel, game_session, message_to_update=message, is_first_turn=True)
            if not game_instance.game_over: game_instance.afk_task = asyncio.create_task(othello_afk_timeout(game_instance))
        elif user.id != host_id:
             try: await reaction.remove(user)
             except discord.HTTPException: pass
        return

    if message_id in active_games:
        game_session = active_games.get(message_id)
        if not game_session: return
        game = game_session["game"]
        if user.id not in game.players.values() or game.game_over:
            try: await reaction.remove(user)
            except discord.HTTPException: pass
            return
        if user.id != game.players.get(game.current_player):
            try: await reaction.remove(user)
            except discord.HTTPException: pass
            return
        chosen_move = next((coord for coord, marker_emoji in game.valid_moves_with_markers.items() if str(reaction.emoji) == marker_emoji), None)
        if chosen_move:
            if game.make_move(chosen_move[0], chosen_move[1], game.current_player):
                if game.afk_task and not game.afk_task.done(): game.afk_task.cancel()
                game.switch_player(); game.check_game_status()
                await send_othello_board_message(message.channel, game_session, message_to_update=message)
                if not game.game_over: game.afk_task = asyncio.create_task(othello_afk_timeout(game))
        try: await reaction.remove(user)
        except discord.HTTPException: pass

async def othello_afk_timeout(game: OthelloGame):
    await asyncio.sleep(OTHELLO_AFK_TIMEOUT_SECONDS)
    game_message_id = getattr(game, 'message_id', None)
    game_session_from_active = active_games.get(game_message_id)
    if game_session_from_active and game_session_from_active.get("game") == game and not game.game_over:
        print(f"Othello Game #{game.game_id}: AFK timeout for player {game.players.get(game.current_player)}")
        
        afk_player_id = game.players.get(game.current_player)
        opponent_id = game.get_opponent_player_id() # AFKしなかった相手

        game.game_over = True
        game.winner = WHITE if game.current_player == BLACK else BLACK # AFKしなかった方が勝ち
        setattr(game, 'ended_by_action', 'afk')
        
        bs = sum(r.count(BLACK) for r in game.board)
        ws = sum(r.count(WHITE) for r in game.board)
        score_diff = abs(bs - ws)
        
        afk_player_user = await bot.fetch_user(afk_player_id) if afk_player_id else None
        winner_player_user = await bot.fetch_user(opponent_id) if opponent_id else None
        afk_mention = afk_player_user.mention if afk_player_user else f"ID:{afk_player_id}"
        winner_mention = winner_player_user.mention if winner_player_user else f"ID:{opponent_id}"
        
        point_message = ""
        if opponent_id and afk_player_id:
            # AFKした側が負け、相手が勝ち
            if game.winner == game.players.get(opponent_id): # 相手が勝っている状態（石が多い）
                update_player_points(opponent_id, score_diff)
                update_player_points(afk_player_id, -score_diff)
                point_message = f"({winner_mention} +{score_diff}pt, {afk_mention} -{score_diff}pt)"
            else: # 相手が負けている状態（石が少ない）
                update_player_points(opponent_id, math.ceil(score_diff / 2)) # 相手に石差の半分
                # AFKした側は変動なし
                point_message = f"({winner_mention} +{math.ceil(score_diff / 2)}pt)"
        
        channel = bot.get_channel(game.channel_id)
        if channel:
            await channel.send(f"ゲーム #{game.game_id}: {afk_mention} が3分以上行動しなかったため、{winner_mention} の勝利です！ {point_message}")
        
        message_to_update = None
        if channel and game.message_id:
            try: message_to_update = await channel.fetch_message(game.message_id)
            except: pass
        await send_othello_board_message(channel or None, game_session_from_active, message_to_update=message_to_update)

@tasks.loop(minutes=5)
async def cleanup_finished_games_task():
    games_to_remove_ids = []
    current_time = datetime.datetime.now(JST)
    for msg_id, game_session_data in list(active_games.items()):
        game_obj = game_session_data.get("game")
        if game_obj and game_obj.game_over and (current_time - game_obj.last_move_time > datetime.timedelta(hours=1)):
            games_to_remove_ids.append(msg_id)
            if game_obj.afk_task and not game_obj.afk_task.done(): game_obj.afk_task.cancel()
            OthelloGame._release_game_id_static(game_obj.game_id) 
    for msg_id in games_to_remove_ids:
        if msg_id in active_games: del active_games[msg_id]
    if games_to_remove_ids: print(f"Cleaned up {len(games_to_remove_ids)} old finished othello games from active_games.")

# ================================== DISCORD COMMANDS ==================================
# @bot.command(name="help")
# async def help_command(ctx: commands.Context):
#     embed = discord.Embed(title="杉山啓太Bot コマンド一覧", color=discord.Color.blue())
#     cmds = [
#         ("watermark + [画像添付]", "添付画像にウォーターマークを合成。"),
#         ("/imakita", "過去30分のチャットを3行で要約。(スラッシュコマンド・どこでも利用可)"),
#         ("5000 [上文字列] [下文字列] (hoshii) (rainbow)", "「5000兆円欲しい！」画像を生成。"),
#         ("gaming + [画像添付]", "添付画像をゲーミング風GIFに変換。"),
#         ("othello (@相手ユーザー)", 
#          "・`othello` : オセロの対戦相手を募集します。\n"
#          "・`othello @メンション` : 指定したユーザーと即時対戦を開始します。\n"
#          "・`othello leave` : 進行中のオセロゲームから離脱します。\n"
#          "・`othello point` : あなたの現在のオセロポイントとランキングを表示。\n"),
#         ("voice + [音声ファイル添付]", "添付音声の声をボイチェンでやまかわてるきの声に変換。（45秒まで）"),
#         ("help", "このヘルプを表示。"),
#         ("その他コマンド", "https://github.com/y-exe/sugiyama-bot")
#     ]
#     for name, value in cmds: embed.add_field(name=name, value=value, inline=False)
#     status = "Available" if not GEMINI_API_UNAVAILABLE else "Not Available"
#     embed.set_footer(text=f"Gemini Text API Status: {status}")
#     await ctx.send(embed=embed)

@bot.command(name="setchannel")
@commands.has_permissions(administrator=True)
async def setchannel_command(ctx: commands.Context):
    cid = ctx.channel.id
    if cid in allowed_channels:
        allowed_channels.remove(cid); await ctx.send(f"このチャンネルでのコマンド利用を**禁止**しました。")
    else:
        allowed_channels.add(cid); await ctx.send(f"このチャンネルでのコマンド利用を**許可**しました。")
    save_settings()

@setchannel_command.error
async def setchannel_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions): await ctx.send("管理者権限が必要です。")
    else: await ctx.send(f"setchannelコマンドでエラー: {error}")

@bot.command(name="watermark")
async def watermark_command(ctx: commands.Context):
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

@bot.command(name="5000")
async def five_k_choyen_command(ctx: commands.Context, top_text: str, bottom_text: str, *options: str):
    options_list = [opt.lower() for opt in options]
    params = {"top": top_text, "bottom": bottom_text,
              "hoshii": "true" if "hoshii" in options_list else "false",
              "rainbow": "true" if "rainbow" in options_list else "false"}
    url = f"https://gsapi.cbrx.io/image?{urllib.parse.urlencode(params)}"
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as s, s.get(url) as r:
                if r.status == 200:
                    embed = discord.Embed(title="5000兆円欲しい！", color=discord.Color.gold()).set_image(url=url)
                    await ctx.send(embed=embed)
                else: await ctx.send(f"画像生成失敗 (APIステータス: {r.status})")
        except Exception as e: await ctx.send(f"画像生成中にエラー: {e}")

@five_k_choyen_command.error
async def five_k_choyen_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"引数が不足しています。例: `5000 上の文字 下の文字 オプション` (`{error.param.name}` がありません)")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"引数の形式が正しくありません。({error})")
    else:
        await ctx.send(f"5000コマンドで予期せぬエラーが発生しました: {error}")
        traceback.print_exc()

@bot.command(name="gaming")
async def gaming_command(ctx: commands.Context):
    if not ctx.message.attachments: return await ctx.send("画像を添付してください。")
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
            await ctx.send(f"**ゲーミング風GIFを生成完了**\nうまくいかない場合は黒白ではなくカラー画像を添付してください {' (リサイズ済)' if resized else ''}", file=discord.File(fp=gif_buffer, filename=out_fname))
        except Exception as e: await ctx.send(f"ゲーミングGIFの生成中にエラー: {e}")

@bot.command(name="othello")
async def othello_command(ctx: commands.Context, opponent: discord.Member = None):
    host_id = ctx.author.id
    if opponent:
        if opponent == ctx.author: return await ctx.send("自分自身とは対戦できません。")
        if opponent.bot: return await ctx.send("Botとは対戦できません。")
    
    for game_session_data in active_games.values():
        game_obj = game_session_data.get("game")
        if game_obj and (host_id in game_obj.players.values() or (opponent and opponent.id in game_obj.players.values())):
            await ctx.send("あなたは既に参加中のオセロゲームがあります。まずはそちらを終了してください (`leave` コマンド)。")
            return
    for rec_info in othello_recruitments.values():
        if host_id == rec_info["host_id"]:
            await ctx.send("あなたは既にオセロの対戦相手を募集中です。")
            return

    if opponent :
        players_list = [host_id, opponent.id]; random.shuffle(players_list)
        game_instance = OthelloGame()
        game_instance.players = {BLACK: players_list[0], WHITE: players_list[1]}
        game_instance.channel_id = ctx.channel.id
        game_session = {"game": game_instance, "players": game_instance.players, "host_id": host_id, "channel_id": ctx.channel.id}
        
        msg_content = f"オセロゲーム #{game_instance.game_id} を {ctx.author.mention} vs {opponent.mention} で開始します..."
        msg = await ctx.send(msg_content)
        if msg:
            active_games[msg.id] = game_session
            game_instance.message_id = msg.id
            await send_othello_board_message(ctx.channel, game_session, message_to_update=msg, is_first_turn=True)
            if not game_instance.game_over: game_instance.afk_task = asyncio.create_task(othello_afk_timeout(game_instance))
        else: OthelloGame._release_game_id_static(game_instance.game_id)
        return

    host_points = get_player_points(host_id)
    recruitment_text = (f"<サーバー内対戦> オセロ募集 (ゲームID: 開始時に採番)\n\n"
                        f"{get_initial_board_text()}\n\n"
                        f"{ctx.author.mention} (Pt: {host_points}) さんが対戦相手を募集しています。\n"
                        f"対戦を受ける場合は ✅ でリアクションしてください。\n"
                        f"（募集者はこのメッセージに ❌ でリアクションして取り消し）")
    try:
        msg = await ctx.send(recruitment_text)
        await msg.add_reaction("✅"); await msg.add_reaction("❌")
        othello_recruitments[msg.id] = {"host_id": host_id, "channel_id": ctx.channel.id, "message_id": msg.id}
    except Exception as e: print(f"Othello recruitment message failed: {e}")

@bot.command(name="othello_points", aliases=["point"])
async def othello_points_command(ctx: commands.Context):
    points = get_player_points(ctx.author.id)
    sorted_points = sorted(othello_points.items(), key=lambda item: item[1], reverse=True)
    embed = discord.Embed(title="オセロポイントランキング", color=discord.Color.gold())
    rank_text = ""
    user_rank_text = f"\nあなたの順位: {ctx.author.mention} - {points}pt (ランキング外または未プレイ)"
    user_in_top10 = False
    for i, (player_id_str, player_points) in enumerate(sorted_points[:10]):
        try:
            user = await bot.fetch_user(int(player_id_str))
            user_display = user.mention if user else f"ID:{player_id_str}"
            if user and user.id == ctx.author.id:
                user_rank_text = f"\nあなたの順位: **{i+1}位** {user.mention} - **{player_points}pt**"
                user_in_top10 = True
        except: user_display = f"ID:{player_id_str}"
        rank_text += f"{i+1}位 {user_display} - {player_points}pt\n"
    if not rank_text: rank_text = "まだポイントを持っているプレイヤーがいません。"
    if not user_in_top10 and points > 0 :
        own_rank = -1
        for i, (pid_str, p_points) in enumerate(sorted_points):
            if int(pid_str) == ctx.author.id:
                own_rank = i + 1; break
        if own_rank != -1: user_rank_text = f"\nあなたの順位: **{own_rank}位** {ctx.author.mention} - **{points}pt**"
    embed.description = rank_text.strip() + user_rank_text
    await ctx.send(embed=embed)

@bot.command(name="leave", aliases=["othello_leave"])
async def leave_othello_game_command(ctx: commands.Context):
    player_id_to_leave = ctx.author.id
    game_session_to_leave: dict = None
    game_to_leave: OthelloGame = None

    for msg_id, gs_data in active_games.items():
        g_obj = gs_data.get("game")
        if g_obj and player_id_to_leave in g_obj.players.values() and not g_obj.game_over:
            game_session_to_leave = gs_data
            game_to_leave = g_obj
            break
    if not game_to_leave:
        return await ctx.send("あなたが現在参加している進行中のオセロゲームはありません。")

    confirm_msg = await ctx.send(f"{ctx.author.mention} ゲーム #{game_to_leave.game_id} を本当に離脱しますか？ (相手の勝利扱いになります)")
    await confirm_msg.add_reaction("✅"); await confirm_msg.add_reaction("❌")
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        try: await confirm_msg.delete()
        except: pass
        if str(reaction.emoji) == "✅":
            game_to_leave.game_over = True
            setattr(game_to_leave, 'ended_by_action', 'leave')
            
            opponent_id = next(pid for color, pid in game_to_leave.players.items() if pid != player_id_to_leave)
            game_to_leave.winner = next(color for color, pid in game_to_leave.players.items() if pid == opponent_id) 

            bs = sum(r.count(BLACK) for r in game_to_leave.board)
            ws = sum(r.count(WHITE) for r in game_to_leave.board)
            score_diff = abs(bs - ws)
            point_message = ""

            if opponent_id and player_id_to_leave:
                update_player_points(opponent_id, math.ceil(score_diff / 2)) 
                update_player_points(player_id_to_leave, -score_diff)      
                winner_user_for_msg = await bot.fetch_user(opponent_id)
                point_message = f"({winner_user_for_msg.mention if winner_user_for_msg else '相手'} +{math.ceil(score_diff / 2)}pt, {ctx.author.mention} -{score_diff}pt)"

            try:
                winner_user = await bot.fetch_user(opponent_id)
                loser_user = await bot.fetch_user(player_id_to_leave)
                await ctx.send(f"{loser_user.mention} がゲーム #{game_to_leave.game_id} から離脱しました。{winner_user.mention} の勝利です！ {point_message}")
            except Exception as e_fetch: print(f"Error fetching users on game leave: {e_fetch}")
            
            board_channel = bot.get_channel(game_to_leave.channel_id) or ctx.channel
            board_message_to_update = None
            if board_channel and game_to_leave.message_id:
                try: board_message_to_update = await board_channel.fetch_message(game_to_leave.message_id)
                except: pass
            await send_othello_board_message(board_channel, game_session_to_leave, message_to_update=board_message_to_update)
        else: await ctx.send("離脱をキャンセルしました。", delete_after=10)
    except asyncio.TimeoutError:
        try: await confirm_msg.delete()
        except: pass
        await ctx.send("離脱の確認がタイムアウトしました。", delete_after=10)

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

@bot.command(name="voice")
async def rvc_voice_convert_command(ctx: commands.Context):
    if not ctx.message.attachments:
        await ctx.send("音声ファイルを添付してください。"); return
    attachment = ctx.message.attachments[0]
    if not (attachment.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a'))):
        await ctx.send("サポートされている音声ファイル形式は .wav, .mp3, .flac, .m4a です。"); return

    audio_bytes_io = io.BytesIO()
    await attachment.save(audio_bytes_io)
    audio_bytes_io.seek(0) 

    try:
        temp_audio_stream_for_check = io.BytesIO(audio_bytes_io.getvalue()) 
        temp_audio_stream_for_check.seek(0)

        audio = AudioSegment.from_file(temp_audio_stream_for_check, format=attachment.filename.split('.')[-1].lower())
        duration_seconds = len(audio) / 1000.0
        print(f"Attached audio duration: {duration_seconds:.2f} seconds")
        temp_audio_stream_for_check.close() 

        if duration_seconds > 45.0:
            await ctx.send(f"エラー: 音声ファイルが長すぎます ({duration_seconds:.1f}秒)。45秒以下のファイルを添付してください。")
            audio_bytes_io.close() 
            return
    except CouldntDecodeError:
        await ctx.send("エラー: 音声ファイルの形式を認識できませんでした。有効な音声ファイルか確認してください。")
        audio_bytes_io.close()
        return
    except Exception as e_dur:
        await ctx.send(f"エラー: 音声ファイルの長さ確認中に問題が発生しました: {e_dur}")
        traceback.print_exc()
        audio_bytes_io.close()
        return
    
    rvc_infer_script_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    rvc_model_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    rvc_index_file_name_no_ext, _ = os.path.splitext(RVC_MODEL_NAME_WITH_EXT)
    rvc_index_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, f"{rvc_index_file_name_no_ext}.index")

    if not os.path.exists(rvc_infer_script_full_path):
        await ctx.send("エラー: RVC推論スクリプトが見つかりません。Bot管理者に連絡してください。"); print(f"Voice command error: RVC inference script not found at {rvc_infer_script_full_path}"); audio_bytes_io.close(); return
    if not os.path.exists(rvc_model_full_path):
        await ctx.send(f"エラー: RVCモデル '{RVC_MODEL_NAME_WITH_EXT}' が見つかりません。Bot管理者に連絡してください。"); print(f"Voice command error: RVC model not found at {rvc_model_full_path}"); audio_bytes_io.close(); return

    processing_message = await ctx.send("**やまかわボイチェンの処理をしています...** \nしばらくお待ちください... (目安:20~50秒)")

    base_filename, file_extension = os.path.splitext(attachment.filename)
    timestamp = datetime.datetime.now(JST).strftime("%Y%m%d%H%M%S%f"); unique_id = f"{ctx.author.id}_{ctx.message.id}_{timestamp}"
    input_filename_rvc = f"input_{unique_id}{file_extension}"; output_filename_rvc = f"output_{unique_id}{file_extension}"
    input_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_INPUT_AUDIO_DIR, input_filename_rvc))
    output_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_OUTPUT_AUDIO_DIR, output_filename_rvc))

    try:
        with open(input_filepath_abs_rvc, 'wb') as f_out:
            audio_bytes_io.seek(0) 
            f_out.write(audio_bytes_io.getbuffer())
        print(f"Saved input audio to: {input_filepath_abs_rvc}")
        audio_bytes_io.close() 

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
            print(f"RVCプロセスがエラーコード {process.returncode} で終了しました。"); await processing_message.edit(content=f"音声変換中にエラーが発生しました。"); return
        if os.path.exists(output_filepath_abs_rvc) and os.path.getsize(output_filepath_abs_rvc) > 0:
            await processing_message.edit(content="**やまかわてるきボイチェンの処理が完了しました**\nうまくいかない場合はBGMを抜いてみてください"); await ctx.send(file=discord.File(output_filepath_abs_rvc, filename=output_filename_rvc))
        else:
            await processing_message.edit(content="変換は成功しましたが、出力ファイルが見つかりませんでした。"); print(f"RVC出力ファイルが見つからないか、サイズが0です: {output_filepath_abs_rvc}")
    except Exception as e:
        await processing_message.edit(content=f"予期せぬエラーが発生しました: {e}"); print(f"予期せぬエラー (rvc_voice_convert_command): {e}"); traceback.print_exc()
    finally:
        if 'audio_bytes_io' in locals() and not audio_bytes_io.closed:
            audio_bytes_io.close()
        if os.path.exists(input_filepath_abs_rvc):
            try: os.remove(input_filepath_abs_rvc)
            except Exception as e_rem: print(f"入力一時ファイルの削除に失敗: {e_rem}")
        if os.path.exists(output_filepath_abs_rvc):
            try: os.remove(output_filepath_abs_rvc)
            except Exception as e_rem: print(f"出力一時ファイルの削除に失敗: {e_rem}")

# ================================== NEW MISC COMMANDS ==================================
@bot.command(name="ping")
async def ping_command(ctx: commands.Context):
    latency = bot.latency * 1000
    await ctx.send(f"ping＝{latency:.2f}ms")

@bot.command(name="tenki", aliases=["weather"])
async def weather_command(ctx: commands.Context, *, city_name_query: str):
    async with ctx.typing():
        city_id = None
        if not weather_city_id_map: await load_weather_city_codes()
        
        query_lower = city_name_query.lower()
        if query_lower == "北海道": 
            city_id = "016010" # 札幌
            print(f"Weather: '北海道' mapped to Sapporo ID '{city_id}'.")
        else:
            for name, id_val in weather_city_id_map.items():
                if query_lower == name.lower() : city_id = id_val; break
            if not city_id:
                for name, id_val in weather_city_id_map.items():
                    if query_lower in name.lower() or name.lower() in query_lower :
                        city_id = id_val; print(f"Weather: Found city ID '{city_id}' for query '{city_name_query}' by partial match."); break
        
        if not city_id and not GEMINI_API_UNAVAILABLE:
            prompt = f"日本の天気予報API（つくもAPI）で地名「{city_name_query}」を検索するために最も適切と思われる都市IDを数字のみで返してください。都道府県名の場合は県庁所在地、地方名（例：道北）の場合はその代表都市のIDを。該当なければ「不明」と返してください。"
            id_response = await generate_gemini_text_response([prompt])
            if not id_response.startswith("Error:") and id_response.strip().isdigit():
                city_id = id_response.strip(); print(f"Weather: Gemini suggested City ID for '{city_name_query}': {city_id}")
        
        if not city_id:
            await ctx.send(f"都市「{city_name_query}」の天気情報が見つかりませんでした。"); return
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
                                date = forecast.get("dateLabel", "不明") + f" ({forecast.get('date')[-5:]})"
                                weather_telop = forecast.get("telop", "情報なし")
                                temp_max = forecast.get("temperature", {}).get("max", {}).get("celsius", "--")
                                temp_min = forecast.get("temperature", {}).get("min", {}).get("celsius", "--")
                                value_str = f"{weather_telop} (最高:{temp_max}°C / 最低:{temp_min}°C)"
                                embed.add_field(name=date, value=value_str, inline=False)
                            await ctx.send(embed=embed)
                        else: await ctx.send(f"「{city_name_query}」(ID:{city_id}) の天気予報データを取得できませんでした。API応答: {data.get('description', {}).get('text', '詳細不明')}")
                    else: await ctx.send(f"天気情報の取得に失敗 (HTTP: {response.status})。都市名/ID: {city_name_query}/{city_id}")
        except Exception as e: await ctx.send(f"天気情報取得エラー: {e}"); traceback.print_exc()

@weather_command.error
async def weather_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"都市名を指定してください。例: `tenki 東京` (`{error.param.name}` がありません)")
    else: await ctx.send(f"天気コマンドでエラー: {error}")

@bot.command(name="info")
async def user_info_command(ctx: commands.Context, member: discord.Member = None):
    target_member = member or ctx.author
    embed = discord.Embed(title=f"{target_member.display_name}", color=target_member.color or discord.Color.default())
    if target_member.avatar: embed.set_thumbnail(url=target_member.avatar.url)
    
    embed.add_field(name="ユーザー名", value=f"`{target_member.name}`", inline=True)
    embed.add_field(name="ユーザーID", value=f"`{target_member.id}`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) 

    created_at_jst = target_member.created_at.astimezone(JST)
    embed.add_field(name="アカウント作成日", value=f"{created_at_jst.strftime('%Y年%m月%d日')}", inline=True)
    
    if isinstance(target_member, discord.Member) and target_member.joined_at:
        joined_at_jst = target_member.joined_at.astimezone(JST)
        embed.add_field(name="サーバー参加日", value=f"{joined_at_jst.strftime('%Y年%m月%d日')}\n({(datetime.datetime.now(JST) - joined_at_jst).days }日前)", inline=True)
    else:
        embed.add_field(name="サーバー参加日", value="N/A", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    
    if isinstance(target_member, discord.Member) and target_member.premium_since:
        boost_since_jst = target_member.premium_since.astimezone(JST)
        boost_duration = (datetime.datetime.now(JST) - boost_since_jst).days
        embed.add_field(name="ブースト開始日", value=f"{boost_since_jst.strftime('%Y年%m月%d日')} ({boost_duration}日前)", inline=True)
    else:
        embed.add_field(name="ブースト開始日", value="なし", inline=True)
    
    badges = []
    flags = target_member.public_flags
    if flags.staff: badges.append(USER_BADGES_EMOJI.get("staff", "STAFF"))
    if flags.partner: badges.append(USER_BADGES_EMOJI.get("partner", "PARTNER"))
    if flags.hypesquad: badges.append(USER_BADGES_EMOJI.get("hypesquad", "HYPESQUAD"))
    if flags.bug_hunter: badges.append(USER_BADGES_EMOJI.get("bug_hunter", "BUG_HUNTER")) # Corrected key
    if flags.bug_hunter_level_2: badges.append(USER_BADGES_EMOJI.get("bug_hunter_level_2", "BUG_HUNTER_LV2"))
    if flags.hypesquad_bravery: badges.append(USER_BADGES_EMOJI.get("hypesquad_bravery", "BRAVERY"))
    if flags.hypesquad_brilliance: badges.append(USER_BADGES_EMOJI.get("hypesquad_brilliance", "BRILLIANCE"))
    if flags.hypesquad_balance: badges.append(USER_BADGES_EMOJI.get("hypesquad_balance", "BALANCE"))
    if flags.early_supporter: badges.append(USER_BADGES_EMOJI.get("early_supporter", "EARLY_SUPPORTER"))
    if target_member.bot and flags.verified_bot : badges.append(USER_BADGES_EMOJI.get("verified_bot", "VERIFIED_BOT"))
    if flags.early_verified_bot_developer: badges.append(USER_BADGES_EMOJI.get("early_verified_bot_developer", "VERIFIED_DEV"))
    if flags.discord_certified_moderator: badges.append(USER_BADGES_EMOJI.get("discord_certified_moderator", "CERT_MOD"))
    if flags.active_developer: badges.append(USER_BADGES_EMOJI.get("active_developer", "ACTIVE_DEV"))
    if isinstance(target_member, discord.Member) and target_member.premium_since: # Nitro/Boosterバッジ
        badges.append(USER_BADGES_EMOJI.get("nitro", "<a:nitro:0>")) # Placeholder if nitro emoji not in dict
        # badges.append(USER_BADGES_EMOJI.get("booster", "<a:booster:0>")) # If booster is a separate emoji

    if badges: embed.add_field(name="バッジ", value=" ".join(badges) or "なし", inline=True)
    else: embed.add_field(name="バッジ", value="なし", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    roles = [role.mention for role in sorted(target_member.roles, key=lambda r: r.position, reverse=True) if role.name != "@everyone"]
    if roles:
        roles_str = " ".join(roles)
        if len(roles_str) > 1000: roles_str = roles_str[:1000] + "..."
        embed.add_field(name=f"ロール ({len(roles)})", value=roles_str or "なし", inline=False)
    else:
        embed.add_field(name="ロール", value="なし", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="rate")
async def exchange_rate_command(ctx: commands.Context, amount: float, currency_code: str):
    currency_code_input = currency_code.upper()
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(EXCHANGE_RATE_API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        target_rate_key = f"{currency_code_input}_JPY"
                        if target_rate_key in data:
                            rate_val = data[target_rate_key]
                            amount_in_jpy = amount * rate_val
                            api_time_utc_str = data.get('datetime', '')
                            try:
                                api_time_utc = datetime.datetime.fromisoformat(api_time_utc_str.replace("Z", "+00:00"))
                                api_time_jst = api_time_utc.astimezone(JST)
                                time_str_jst = api_time_jst.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + " JST"
                            except: time_str_jst = api_time_utc_str
                            await ctx.send(f"{amount:,.2f} {currency_code_input} → **{amount_in_jpy:,.2f} 円** (1 {currency_code_input} = {rate_val:,.3f} JPY, {time_str_jst}時点)")
                        else:
                            available_currencies = [key.split('_')[0] for key in data.keys() if key.endswith("_JPY")]
                            await ctx.send(f"通貨「{currency_code_input}」の対日本円レートが見つかりません。\n利用可能(対JPY): {', '.join(available_currencies)}")
                    else: await ctx.send(f"為替レートAPIアクセス失敗 (HTTP: {response.status})")
        except Exception as e: await ctx.send(f"為替レート変換エラー: {e}"); traceback.print_exc()

@exchange_rate_command.error
async def exchange_rate_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        available_currencies_text = "USD, EUR, GBP, AUD, NZD, CAD, CHF, TRY, ZAR, MXN"
        await ctx.send(f"引数が不足しています。例: `rate 150 USD` (`{error.param.name}` がありません)\n使える国コードは {available_currencies_text} です。")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"引数の形式が正しくありません。金額は数値で、通貨コードは3文字で入力してください。")
    else: await ctx.send(f"rateコマンドでエラー: {error}")

@bot.command(name="shorturl", aliases=["short"])
async def shorturl_command(ctx: commands.Context, url_to_shorten: str):
    if not (url_to_shorten.startswith("http://") or url_to_shorten.startswith("https://")):
        url_to_shorten = "http://" + url_to_shorten
    params = {"url": url_to_shorten}
    if SHORTURL_API_KEY and SHORTURL_API_KEY != "YOUR_XGD_API_KEY_PLACEHOLDER":
        params["key"] = SHORTURL_API_KEY
    target_url_with_params = f"{SHORTURL_API_ENDPOINT}?{urllib.parse.urlencode(params)}"
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target_url_with_params) as response:
                    response_content_text = await response.text()
                    print(f"x.gd API request URL: {target_url_with_params}")
                    print(f"x.gd API response status: {response.status}, content: {response_content_text[:200]}")
                    if response.status == 200:
                        try:
                            data = json.loads(response_content_text)
                            if isinstance(data, dict) and data.get("status") == 200 and data.get("shorturl"):
                                await ctx.send(f"短縮URL: {data['shorturl']}")
                            elif isinstance(data, dict) and "message" in data :
                                await ctx.send(f"URL短縮に失敗しました (API Status: {data.get('status', response.status)}): `{data['message']}`")
                            else: 
                                if response_content_text.startswith("https://x.gd/") or response_content_text.startswith("http://x.gd/"):
                                    await ctx.send(f"短縮URL: {response_content_text}")
                                else: await ctx.send(f"URL短縮で予期しない応答がありました。応答: `{response_content_text}`")
                        except json.JSONDecodeError:
                             if response_content_text.startswith("https://x.gd/") or response_content_text.startswith("http://x.gd/"):
                                await ctx.send(f"短縮URL: {response_content_text}")
                             else: await ctx.send(f"URL短縮に失敗しました。APIからの応答がURL形式ではありません: `{response_content_text}`")
                    else: 
                        error_message = response_content_text
                        try:
                            error_data = json.loads(response_content_text)
                            if isinstance(error_data, dict) and "message" in error_data: error_message = error_data["message"]
                        except json.JSONDecodeError: pass
                        await ctx.send(f"URL短縮APIへのアクセスに失敗しました (HTTPステータス: {response.status})。応答: `{error_message}`")
        except Exception as e: await ctx.send(f"URL短縮中にエラーが発生しました: {e}"); traceback.print_exc()

@shorturl_command.error
async def shorturl_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"URLを指定してください。例: `shorturl https://example.com` (`{error.param.name}` がありません)")
    else: await ctx.send(f"shorturlコマンドでエラー: {error}")

@bot.command(name="totusi")
async def totusi_command(ctx: commands.Context, *, text: str):
    if not text: return await ctx.send("文字列を指定してください。例: `totusi テスト`")
    text = text.replace("　", " ")
    char_display_width = 0
    for char_ in text:
        if unicodedata.east_asian_width(char_) in ('F', 'W', 'A'): char_display_width += 2
        else: char_display_width += 1
    arrow_count = math.ceil(char_display_width / 1.5) 
    if arrow_count < 3: arrow_count = 3
    if arrow_count > 15: arrow_count = 15
    line1 = "＿" + "人" * arrow_count + "＿"
    line2 = f"＞　**{text}**　＜"
    line3 = "￣" + ("Y^" * arrow_count) + "Y￣"
    result = f"{line1}\n{line2}\n{line3}" # コードブロックなしで送信
    await ctx.send(result)

@totusi_command.error
async def totusi_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"文字列を指定してください。例: `totusi あいうえお` (`{error.param.name}` がありません)")
    else: await ctx.send(f"totusiコマンドでエラー: {error}")

@bot.command(name="time")
async def time_command(ctx: commands.Context, country_code: str = None):
    if country_code and country_code.lower() == "help":
        help_text = "利用可能な国コード (G20主要国とその他):\n"
        sorted_timezones = sorted(TIMEZONE_MAP.items())
        for code, tz_name in sorted_timezones: help_text += f"`{code}`: {tz_name.split('/')[-1].replace('_', ' ')}\n"
        embed = discord.Embed(title="Timeコマンド ヘルプ", description=help_text[:2000], color=discord.Color.blue())
        return await ctx.send(embed=embed)

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_jst = now_utc.astimezone(JST)

    if not country_code:
        return await ctx.send(f"{now_jst.strftime('%Y-%m-%d %H時%M分%S.%f')[:-3]}秒 (日本時間)")

    target_tz_name_str = TIMEZONE_MAP.get(country_code.upper())
    if not target_tz_name_str:
        valid_codes = ", ".join(TIMEZONE_MAP.keys())
        return await ctx.send(f"国コード「{country_code}」は無効です。\n利用可能な国コード: {valid_codes}\nまたは `time help` を参照してください。")

    try:
        target_timezone = pytz.timezone(target_tz_name_str)
        target_dt = now_utc.astimezone(target_timezone)
        offset = target_dt.utcoffset()
        offset_hours = offset.total_seconds() / 3600
        offset_str = f"UTC{offset_hours:+.1f}".replace(".0", "")
        
        await ctx.send(f"{target_tz_name_str.split('/')[-1].replace('_', ' ')} の現在時刻: {target_dt.strftime('%Y-%m-%d %H時%M分%S.%f')[:-3]}秒 ({offset_str})")

    except pytz.exceptions.UnknownTimeZoneError:
        await ctx.send(f"指定されたタイムゾーン名「{target_tz_name_str}」は `pytz` ライブラリで無効です。")
    except Exception as e:
        await ctx.send(f"時刻の取得中にエラーが発生しました: {e}")

@bot.command(name="amazon")
async def amazon_shorturl_command(ctx: commands.Context, amazon_url: str):
    if not amazon_url:
        return await ctx.send("AmazonのURLを指定してください。")
    parsed_url = urllib.parse.urlparse(amazon_url)
    if not (parsed_url.scheme in ["http", "https"] and ("amazon.co.jp" in parsed_url.netloc or "amzn.asia" in parsed_url.netloc or "amazon.com" in parsed_url.netloc)):
        return await ctx.send("有効なAmazonのURLを指定してください。 (例: https://www.amazon.co.jp/...)")

    # URLから不要なトラッキングパラメータなどを削除して正規化する試み (オプション)
    # 例: dp/ASIN/ または gp/product/ASIN/ の形式に近づける
    # match = re.search(r"(dp|gp/product)/([A-Z0-9]{10})", amazon_url)
    # canonical_url = amazon_url
    # if match:
    #     base = "https://www.amazon.co.jp" if "amazon.co.jp" in parsed_url.netloc else "https://www.amazon.com"
    #     canonical_url = f"{base}/dp/{match.group(2)}/"
    # else: # ASINが見つからなければ元のURLを使う
    #     canonical_url = amazon_url
    # params = { "longUrl": canonical_url, "marketplaceId": "6" }

    params = { "longUrl": urllib.parse.quote_plus(amazon_url), "marketplaceId": "6" } # URLエンコード
    target_url = f"{AMAZON_SHORTURL_ENDPOINT}?{urllib.parse.urlencode(params, safe='/:')}" # quote_plusしたものを再度エンコードしないように注意
    
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" }
                async with session.get(target_url, headers=headers) as response:
                    print(f"Amazon ShortURL API request to: {target_url}") # デバッグ用に完全なURLを表示
                    response_text = await response.text()
                    print(f"Amazon ShortURL API response status: {response.status}, content: {response_text[:200]}")

                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                            if data.get("isOk") is True and data.get("shortUrl"):
                                await ctx.send(f"Amazon短縮URL: {data['shortUrl']}")
                            else:
                                error_detail = data.get("error", {}).get("message", response_text if response_text else "不明なエラー")
                                await ctx.send(f"Amazon URL短縮に失敗しました。API応答: `{error_detail}`")
                        except json.JSONDecodeError:
                             await ctx.send(f"Amazon URL短縮で予期しない応答形式。応答: `{response_text[:200]}`")
                    else:
                        await ctx.send(f"Amazon URL短縮APIアクセス失敗 (HTTP: {response.status})。応答: `{response_text[:200]}`")
        except Exception as e:
            await ctx.send(f"Amazon URL短縮中にエラー: {e}")
            traceback.print_exc()

@amazon_shorturl_command.error
async def amazon_shorturl_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"AmazonのURLを指定してください。例: `amazon https://www.amazon.co.jp/...` (`{error.param.name}`がありません)")
    else:
        await ctx.send(f"amazonコマンドでエラー: {error}")


# =================================== BOT EXECUTION ====================================
if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_PLACEHOLDER" or not DISCORD_BOT_TOKEN:
        print("致命的なエラー: DISCORD_BOT_TOKEN が .env ファイルに設定されていないか、プレースホルダーのままです。")
        print(f"{os.path.join(os.path.dirname(__file__), '.env')} ファイルを作成し、DISCORD_BOT_TOKEN=\"あなたのトークン\" と記述してください。")
        exit(1)
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_PLACEHOLDER" or not GEMINI_API_KEY:
        print("警告: GEMINI_API_KEY が .env ファイルに設定されていないか、プレースホルダーのままです。Gemini関連機能は利用できません。")
    if not SHORTURL_API_KEY or SHORTURL_API_KEY == "YOUR_XGD_API_KEY_PLACEHOLDER":
        print("警告: SHORTURL_API_KEY が .env ファイルに設定されていないか、提供されたサンプルキーのままです。'shorturl' コマンドは利用できない可能性があります。")
    
    missing_deps = []
    try: import numpy
    except ImportError: missing_deps.append("numpy")
    try: from PIL import Image
    except ImportError: missing_deps.append("Pillow")
    try: import pytz
    except ImportError: missing_deps.append("pytz")

    if missing_deps:
        print(f"警告: 以下の必須ライブラリが Bot用仮想環境 にインストールされていません: {', '.join(missing_deps)}")
        print(f"共有仮想環境 (C:\\Bot\\RVC_Project\\venv) を有効化して `pip install {' '.join(missing_deps)}` を実行してください。")

    print("Botを起動します...")
    try:
        load_othello_points()
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure: print("エラー: Discord Botトークンが無効です。トークンを確認してください。")
    except Exception as e: print(f"Bot実行中に予期せぬエラーが発生しました: {e}"); traceback.print_exc()
