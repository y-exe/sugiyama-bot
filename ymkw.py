# ========================== IMPORTS ==========================
import os
import sys
import discord
from discord.ext import commands, tasks
import google.generativeai as genai
# from google.generativeai import types as genai_types # This is a valid Python comment
import datetime
import asyncio
import aiohttp
import urllib.parse
import json
import io
import random
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
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
from collections import deque

# ========================== CONFIGURATION & INITIALIZATION ==========================
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
BASE_DIR = os.path.dirname(__file__)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

YAHOO_CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
YAHOO_WEATHER_API_URL = "https://map.yahooapis.jp/weather/V1/place"

EXCHANGE_RATE_API_URL = "https://exchange-rate-api.krnk.org/api/rate"
SHORTURL_API_ENDPOINT = "https://xgd.io/V1/shorten"
SHORTURL_API_KEY = os.getenv("SHORTURL_API_KEY")
AMAZON_SHORTURL_ENDPOINT = "https://www.amazon.co.jp/associates/sitestripe/getShortUrl"

VOICEVOX_API_KEY = os.getenv("VOICEVOX_API_KEY")
VOICEVOX_SPEAKER_ID = 11
VOICEVOX_API_BASE_URL = "https://deprecatedapis.tts.quest/v2/voicevox/audio/"

_DUMMY_PREFIX_VALUE = "!@#$%^&SUGIYAMA_BOT_DUMMY_PREFIX_XYZ_VERY_UNIQUE"
def get_dummy_prefix(bot, message):
    return _DUMMY_PREFIX_VALUE

# BASE_DIR は既に上で定義済みなので、再定義は不要
SETTINGS_FILE_PATH = os.path.join(BASE_DIR, "bot_settings.json")
GAME_POINTS_FILE_PATH = os.path.join(BASE_DIR, "game_points.json")

allowed_channels = set()
game_points = {}
JST = pytz.timezone("Asia/Tokyo")

MAX_FILE_SIZE_BYTES = int(4.8 * 1024 * 1024)
MIN_IMAGE_DIMENSION = 300
TEMPLATES_BASE_PATH = os.path.join(BASE_DIR, "assets", "watermark_templates")
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

# /imakita rate limit
imakita_request_timestamps = deque() # ★ グローバル変数として初期化されているか確認
IMAKITA_RATE_LIMIT_COUNT = 13
IMAKITA_RATE_LIMIT_SECONDS = 60

GREEN_SQUARE = "<:o_0:1380626312976138400>"
BLACK_STONE  = "<:o_2:1380626308383510548>"
WHITE_STONE  = "<:o_1:1380626310551830580>"
MARKERS = ["0️⃣","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","<:o_A:1380638761288859820>","<:o_B:1380638762941419722>","<:o_C:1380638764782850080>","<:o_D:1380638769216225321>","<:o_E:1380638771178897559>","<:o_F:1380638773926301726>","<:o_G:1380638776103010365>","<:o_H:1380643990784966898>","<:o_I:1380644006093918248>","<:o_J:1380644004181577849>","<:o_K:1380644001652281374>","<:o_L:1380643998841966612>","<:o_M:1380643995855622254>","<:o_N:1380643993431314432>","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"]
active_games = {}
othello_recruitments = {}
OTHELLO_AFK_TIMEOUT_SECONDS = 180

active_janken_games = {}
HAND_EMOJIS = {"rock": "✊", "scissors": "✌️", "paper": "✋"}
EMOJI_TO_HAND = {v: k for k, v in HAND_EMOJIS.items()}
JANKEN_TIMEOUT_HOST_CHOICE_SECONDS = 60.0
JANKEN_WIN_POINTS = 7
JANKEN_LOSE_POINTS = -5

GEMINI_TEXT_MODEL_NAME = 'models/gemini-1.5-flash'

RVC_PROJECT_ROOT_PATH = os.path.abspath(os.path.join(BASE_DIR, "RVC_Project"))
RVC_MODEL_DIR_IN_PROJECT = os.path.join("assets", "weights")
RVC_MODEL_NAME_WITH_EXT = "ymkw.pth"
RVC_INFER_SCRIPT_SUBPATH = os.path.join("tools", "infer_cli.py")
RVC_FIXED_TRANSPOSE = 0
RVC_INPUT_AUDIO_DIR = os.path.join(BASE_DIR, "audio", "input")
RVC_OUTPUT_AUDIO_DIR = os.path.join(BASE_DIR, "audio", "output")

USER_BADGES_EMOJI = {
    "active_developer": "<:activedeveloper:1383253229189730374>",
    "nitro": "<:nitro:1383252018532974642>",
    "hypesquad_balance": "<:balance:1383251792413851688>",
    "hypesquad_bravery": "<:bravery:1383251749623693392>",
    "hypesquad_brilliance": "<:brilliance:1383251723610624174>",
    "premium": "<:booster:1383251702144176168>",
    "partner": "<:partnerserver:1383251682070364210>",
    "early_verified_bot_developer": "<:earlyverifiedbot:1383251648348160030>",
    "bug_hunter": "<:bugHunter:1383251633567170683>",
    "bug_hunter_level_2": "<:bugHunter:1383251633567170683>",
    "early_supporter": "<:earlysupporter:1383251618379727031>",
    "staff": "<:staff:1383251602680578111>",
    "discord_certified_moderator": "<:moderator:1383251587438215218>",
    "verified_bot": "✅"
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

TEXT_IMAGE_FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "MochiyPopOne-Regular.ttf")
TEXT_IMAGE_FONT_SIZE = 100
TEXT_IMAGE_TEXT_COLOR = (255, 255, 0)
TEXT_IMAGE_OUTLINE_COLOR_BLACK = (0, 0, 0)
TEXT_IMAGE_OUTLINE_COLOR_WHITE = (255, 255, 255)
TEXT_IMAGE_OUTLINE_THICKNESS_BLACK = 11
TEXT_IMAGE_OUTLINE_THICKNESS_WHITE = 11
TEXT_IMAGE_PADDING = 30 # 以前は35だったが、調整しやすいように一旦30に戻す
TEXT_IMAGE_LETTER_SPACING_ADJUST = -0.10
TEXT_IMAGE_LINE_HEIGHT_MULTIPLIER = 0.80
TEXT_IMAGE_VERTICAL_OFFSET = -15 # Yオフセット (以前は-25、-10など)
TEXT_MASK_ADDITIONAL_MARGIN = TEXT_IMAGE_FONT_SIZE // 2

# ★★★ BET_DICE_PAYOUTS の定義を追加 ★★★
BET_DICE_PAYOUTS = {
    1: ("大凶... 賭け金は没収です。", -1.0),
    2: ("凶。賭け金の半分を失いました。", -0.5),
    3: ("小吉。賭け金の半分を失いました。", -0.5),
    4: ("吉！賭け金はそのまま戻ってきます。", 0.0),
    5: ("中吉！賭け金が1.5倍になりました。", 0.5),
    6: ("大吉！おめでとうございます！賭け金が2倍になりました！", 1.0)
}
# ★★★★★★★★★★★★★★★★★★★★★★★★

for t_data in TEMPLATES_DATA:
    try:
        parts = t_data['user_ratio_str'].split('/')
        if len(parts) == 2 and float(parts[1]) != 0: t_data['match_ratio_wh'] = float(parts[0]) / float(parts[1])
        else: raise ValueError("Invalid ratio format")
    except Exception as e:
        print(f"Warning: Template '{t_data['name']}' ratio parsing error: {e}"); t_data['match_ratio_wh'] = 1.0

gemini_text_model_instance = None
GEMINI_API_UNAVAILABLE = False
# ... (Gemini初期化は変更なし) ...
print("--- Gemini API Initialization Attempt (Text Model Only) ---")
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_PLACEHOLDER":
    print(f"Using GEMINI_API_KEY: {GEMINI_API_KEY[:5]}...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_text_model_instance = genai.GenerativeModel(GEMINI_TEXT_MODEL_NAME)
        if not gemini_text_model_instance:
            print("ERROR: Gemini text model instance failed to initialize."); GEMINI_API_UNAVAILABLE = True
        else:
            print(f"Gemini Text Model ('{GEMINI_TEXT_MODEL_NAME}') initialized successfully.")
    except Exception as e:
        print(f"ERROR: Gemini API init failed: {e}"); traceback.print_exc(); GEMINI_API_UNAVAILABLE = True
else:
    print("WARNING: GEMINI_API_KEY not set. Gemini features unavailable."); GEMINI_API_UNAVAILABLE = True
print("--- End of Gemini API Initialization Attempt ---")


intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix=get_dummy_prefix, intents=intents, help_command=None)

os.makedirs(RVC_INPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(RVC_OUTPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "assets", "fonts"), exist_ok=True)
os.makedirs(TEMPLATES_BASE_PATH, exist_ok=True)


# ================================= GAME LOGIC (OTHELLO) & HELPERS =================================
EMPTY = 0; BLACK = 1; WHITE = 2; BOARD_SIZE = 8
class OthelloGame: # ... (OthelloGameクラスの定義は変更なし) ...
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
        self.message_id: int = None

    @staticmethod
    def _assign_game_id_static():
        gid = OthelloGame._next_game_id_counter
        while gid in OthelloGame._active_game_ids: gid += 1
        OthelloGame._active_game_ids.add(gid)
        OthelloGame._next_game_id_counter = gid + 1
        print(f"Assigned Othello Game ID: {gid}"); return gid
    @staticmethod
    def _release_game_id_static(gid):
        if gid in OthelloGame._active_game_ids:
            OthelloGame._active_game_ids.remove(gid)
            print(f"Released Othello Game ID: {gid}")

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


# ★★★ get_initial_board_text 関数の定義を追加 ★★★
def get_initial_board_text():
    temp_game = OthelloGame() # OthelloGameクラスがこの関数より前に定義されている必要あり
    board_str = ""
    for r_idx in range(BOARD_SIZE): # BOARD_SIZE も定義されている必要あり
        for c_idx in range(BOARD_SIZE):
            if temp_game.board[r_idx][c_idx] == BLACK: board_str += BLACK_STONE # BLACK_STONEなども定義済みであること
            elif temp_game.board[r_idx][c_idx] == WHITE: board_str += WHITE_STONE
            else: board_str += GREEN_SQUARE
        board_str += "\n"
    return board_str.strip()


# ================================= HELPER FUNCTIONS (Points, Settings, Image, etc.) =================================
# ... (OthelloGame class, get_initial_board_text, load/save_settings, load/save_game_points, get/update_player_points unchanged from previous full code)
# ... (_resize_image_if_too_large, _process_and_composite_image, _create_gaming_gif unchanged)
# ... (generate_gemini_text_response, generate_summary_with_gemini unchanged)
# ... (send_othello_board_message - with updated point logic for normal end)
# ... (generate_voicevox_audio, process_audio_with_rvc unchanged)
# OTHELLO GAME LOGIC (unchanged)
EMPTY = 0; BLACK = 1; WHITE = 2; BOARD_SIZE = 8
class OthelloGame:
    _next_game_id_counter = 1
    _active_game_ids = set()
    def __init__(self): # ... (rest of OthelloGame class is unchanged)
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.board[3][3] = WHITE; self.board[3][4] = BLACK
        self.board[4][3] = BLACK; self.board[4][4] = WHITE
        self.current_player = BLACK
        self.valid_moves_with_markers = {}
        self.game_over = False; self.winner = None; self.last_pass = False
        self.players = {} # {BLACK: player_id, WHITE: player_id}
        self.channel_id = None
        self.last_move_time = datetime.datetime.now(JST)
        self.game_id = OthelloGame._assign_game_id_static()
        self.afk_task: asyncio.Task = None
        self.message_id: int = None # To store the game board message ID

    @staticmethod
    def _assign_game_id_static():
        gid = OthelloGame._next_game_id_counter
        while gid in OthelloGame._active_game_ids:
            gid += 1
        OthelloGame._active_game_ids.add(gid)
        OthelloGame._next_game_id_counter = gid + 1
        print(f"Assigned Othello Game ID: {gid}")
        return gid

    @staticmethod
    def _release_game_id_static(gid):
        if gid in OthelloGame._active_game_ids:
            OthelloGame._active_game_ids.remove(gid)
            print(f"Released Othello Game ID: {gid}")
        # To prevent unbounded growth of _next_game_id_counter if many games are played,
        # one might consider more sophisticated ID management, but for typical use this is okay.

    def is_on_board(self, r, c): return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE
    def get_flips(self, r_start, c_start, player): # Returns list of (r,c) tuples to flip
        if not self.is_on_board(r_start, c_start) or self.board[r_start][c_start] != EMPTY: return []
        opponent = WHITE if player == BLACK else BLACK
        tiles_to_flip = []
        for dr, dc in [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]: # 8 directions
            r, c = r_start + dr, c_start + dc
            current_line_flips = []
            while self.is_on_board(r, c) and self.board[r][c] == opponent:
                current_line_flips.append((r,c))
                r += dr; c += dc
            if self.is_on_board(r,c) and self.board[r][c] == player and current_line_flips:
                tiles_to_flip.extend(current_line_flips)
        return tiles_to_flip

    def calculate_valid_moves(self, player):
        self.valid_moves_with_markers.clear()
        marker_index = 0
        possible_moves = []
        for r_idx in range(BOARD_SIZE):
            for c_idx in range(BOARD_SIZE):
                if self.board[r_idx][c_idx] == EMPTY and self.get_flips(r_idx, c_idx, player):
                    possible_moves.append((r_idx, c_idx))
                    if marker_index < len(MARKERS):
                        self.valid_moves_with_markers[(r_idx,c_idx)] = MARKERS[marker_index]
                        marker_index +=1
        return possible_moves

    def make_move(self, r, c, player):
        if self.game_over: return False
        if not self.is_on_board(r,c) or self.board[r][c] != EMPTY: return False
        tiles_to_flip = self.get_flips(r,c,player)
        if not tiles_to_flip: return False
        self.board[r][c] = player
        for fr, fc in tiles_to_flip: self.board[fr][fc] = player
        self.last_pass = False
        self.last_move_time = datetime.datetime.now(JST)
        return True

    def switch_player(self): self.current_player = WHITE if self.current_player == BLACK else BLACK
    def check_game_status(self): # Checks for game over conditions
        if self.game_over: return
        if self.calculate_valid_moves(self.current_player): # Current player has moves
            self.last_pass = False; return
        # Current player has no moves, check opponent
        if self.last_pass: # Both players passed consecutively
            self.game_over = True
        else:
            self.last_pass = True
            self.switch_player()
            if not self.calculate_valid_moves(self.current_player): # Opponent also has no moves
                self.game_over = True
        if self.game_over: self.determine_winner()

    def determine_winner(self):
        black_score = sum(row.count(BLACK) for row in self.board)
        white_score = sum(row.count(WHITE) for row in self.board)
        if black_score > white_score: self.winner = BLACK
        elif white_score > black_score: self.winner = WHITE
        else: self.winner = EMPTY # Draw

    def get_current_player_id(self): return self.players.get(self.current_player)
    def get_opponent_player_id(self): return self.players.get(WHITE if self.current_player == BLACK else BLACK)

# SETTINGS & POINTS (unchanged)
def load_settings(): # ...
    global allowed_channels
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
                allowed_channels = set(settings_data.get("allowed_channels", []))
        else: # File doesn't exist, create with empty set
            allowed_channels = set()
            save_settings()
    except Exception as e:
        print(f"Error loading settings: {e}. Using empty allowed channels set. (File: {SETTINGS_FILE_PATH})")
        allowed_channels = set()
def save_settings(): # ...
    settings_data = {"allowed_channels": list(allowed_channels)}
    try:
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings: {e}")
def load_game_points(): # ...
    global game_points
    try:
        if os.path.exists(GAME_POINTS_FILE_PATH):
            with open(GAME_POINTS_FILE_PATH, 'r', encoding='utf-8') as f:
                game_points = json.load(f)
        else: # File doesn't exist, initialize and save
            game_points = {}
            save_game_points()
    except json.JSONDecodeError: # File is empty or corrupted
        print(f"Game points file is empty or corrupted. Initializing with empty points. (File: {GAME_POINTS_FILE_PATH})")
        game_points = {}
        save_game_points() # Save the fresh empty state
    except Exception as e:
        print(f"Error loading game points: {e}. Using empty points data.")
        game_points = {}
def save_game_points(): # ...
    try:
        with open(GAME_POINTS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(game_points, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving game points: {e}")
def get_player_points(player_id: int) -> int: return game_points.get(str(player_id), 0)
def update_player_points(player_id: int, points_change: int): # ...
    player_id_str = str(player_id)
    current_points = game_points.get(player_id_str, 0)
    new_points = max(0, current_points + points_change) # Points cannot be negative
    game_points[player_id_str] = new_points
    save_game_points()

# IMAGE HELPERS (unchanged)
async def _resize_image_if_too_large(
    image_fp: io.BytesIO, 
    target_format: str, 
    max_size_bytes: int = MAX_FILE_SIZE_BYTES, # Default from global
    min_dimension: int = MIN_IMAGE_DIMENSION, # Default from global
    initial_aggressiveness: float = 0.9,
    subsequent_resize_factor: float = 0.85, 
    max_iterations: int = 7
) -> tuple[io.BytesIO | None, bool]:
    image_fp.seek(0, io.SEEK_END); current_size = image_fp.tell(); image_fp.seek(0)
    if current_size <= max_size_bytes: return image_fp, False # No resize needed

    current_fp_to_process = image_fp # Start with the original BytesIO
    resized_overall = False
    
    # If it's a GIF, we need to handle frames. For others, a single image.
    is_gif = target_format.upper() == "GIF"

    for iteration in range(max_iterations): # max_iterations to prevent infinite loops
        current_fp_to_process.seek(0) # Rewind buffer for reading
        try:
            img = Image.open(current_fp_to_process)
            original_width, original_height = img.width, img.height

            # If already small enough or too small to reasonably resize further
            if min(original_width, original_height) <= min_dimension:
                # If it's still too large by bytes but dimensions are small, not much more we can do by resizing
                if current_fp_to_process.tell() > MAX_FILE_SIZE_BYTES:
                    print(f"Image dimensions ({original_width}x{original_height}) too small for further effective resizing, but size ({current_fp_to_process.tell()} bytes) still too large.")
                break # Stop if dimensions are too small

            # Calculate new size
            current_fp_to_process.seek(0, io.SEEK_END); current_iteration_size = current_fp_to_process.tell(); current_fp_to_process.seek(0)
            
            resize_this_iteration_factor = subsequent_resize_factor
            if iteration == 0 and current_iteration_size > max_size_bytes:
                # Aggressive first resize if way too large
                area_ratio = MAX_FILE_SIZE_BYTES / current_iteration_size
                dimension_ratio_estimate = math.sqrt(area_ratio) * initial_aggressiveness
                resize_this_iteration_factor = max(0.1, min(dimension_ratio_estimate, 0.95)) # Clamp between 10% and 95%

            new_width = int(original_width * resize_this_iteration_factor)
            new_height = int(original_height * resize_this_iteration_factor)

            # Ensure new dimensions are not smaller than min_dimension, preserving aspect ratio
            if new_width < min_dimension or new_height < min_dimension:
                aspect_ratio_orig = original_width / original_height
                if new_width < min_dimension and new_height < min_dimension: # Both too small
                    if new_width * aspect_ratio_orig > min_dimension : # Scale by width
                         new_width = min_dimension
                         new_height = int(new_width / aspect_ratio_orig)
                    else: # Scale by height
                         new_height = min_dimension
                         new_width = int(new_height * aspect_ratio_orig)
                elif new_width < min_dimension:
                    new_width = min_dimension
                    new_height = int(new_width / aspect_ratio_orig)
                else: # new_height < min_dimension
                    new_height = min_dimension
                    new_width = int(new_height * aspect_ratio_orig)
                
                new_width = max(new_width, 1); new_height = max(new_height, 1) # Ensure positive dimensions
                if new_width >= original_width and new_height >= original_height: # Avoid upscaling
                     break # No effective downscale possible

            output_fp = io.BytesIO()
            
            if is_gif:
                frames = []
                durations = []
                loop = img.info.get('loop', 0)
                disposal = img.info.get('disposal', 2) # Default disposal method

                try:
                    img.seek(0) # Start from the first frame
                    while True:
                        # Create a copy of the current frame to avoid modifying the original
                        frame_copy = img.copy().convert("RGBA") # Convert to RGBA for consistency
                        frame_copy.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                        frames.append(frame_copy)
                        durations.append(img.info.get('duration', 100)) # Get duration for this frame
                        img.seek(img.tell() + 1) # Move to the next frame
                except EOFError:
                    pass # End of frames
                
                if not frames: break # No frames processed (e.g., not a valid GIF)
                
                frames[0].save(output_fp, format="GIF", save_all=True, append_images=frames[1:], 
                               duration=durations, loop=loop, disposal=disposal, optimize=True)
            else: # For non-GIF images (PNG, JPEG etc.)
                # Create a copy for resizing to avoid issues with original stream
                resized_img = img.copy() 
                resized_img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                
                save_params = {'optimize': True}
                if target_format.upper() == 'JPEG': save_params['quality'] = 85 # Good quality for JPEGs
                elif target_format.upper() == 'PNG': save_params['compress_level'] = 7 # Good compression for PNGs
                
                resized_img.save(output_fp, format=target_format.upper(), **save_params)

            output_fp.seek(0, io.SEEK_END); new_size = output_fp.tell(); output_fp.seek(0)

            # Close the previous BytesIO object if it's not the original one passed to the function
            if current_fp_to_process != image_fp:
                current_fp_to_process.close()
            
            current_fp_to_process = output_fp # Update to the new (resized) BytesIO
            resized_overall = True

            if new_size <= max_size_bytes:
                return current_fp_to_process, resized_overall # Success!
        
        except Exception as e_resize:
            print(f"Error during image resize iteration: {e_resize}")
            # If an error occurs, and we created an intermediate buffer, close it
            if current_fp_to_process != image_fp:
                current_fp_to_process.close()
            return image_fp, False # Return original on error, indicating no successful resize

    # If loop finishes and still too large, return the last processed (smallest attempted)
    # The caller should check the size again if truly critical.
    return current_fp_to_process, resized_overall
def _process_and_composite_image(img_bytes: bytes, tmpl_data: dict) -> io.BytesIO | None: # ... (unchanged)
    try:
        base_image = Image.open(io.BytesIO(img_bytes))
        target_width, target_height = tmpl_data['target_size']
        
        # Use ImageOps.fit to crop and resize to fill the target dimensions
        processed_base_image = ImageOps.fit(base_image, (target_width, target_height), Image.Resampling.LANCZOS)

        overlay_path = os.path.join(TEMPLATES_BASE_PATH, tmpl_data['name'])
        if not os.path.exists(overlay_path):
            print(f"Overlay template not found: {overlay_path}")
            return None
        
        overlay_image = Image.open(overlay_path).convert("RGBA")
        # Ensure overlay is resized to target dimensions if not already
        if overlay_image.size != (target_width, target_height):
            overlay_image = overlay_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Ensure base image is RGBA for alpha compositing
        if processed_base_image.mode != 'RGBA':
            processed_base_image = processed_base_image.convert('RGBA')
        
        final_image = Image.alpha_composite(processed_base_image, overlay_image)
        
        output_buffer = io.BytesIO()
        final_image.save(output_buffer, "PNG")
        output_buffer.seek(0)
        return output_buffer
    except Exception as e_composite:
        print(f"Error during image compositing: {e_composite}")
        return None
def _create_gaming_gif(img_bytes: bytes, duration_ms: int = 50, max_size: tuple = (256, 256)) -> io.BytesIO | None: # ... (unchanged)
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA") # Ensure RGBA for HSV conversion and transparency
        img.thumbnail(max_size, Image.Resampling.LANCZOS) # Resize to max_size while maintaining aspect ratio
        
        frames = []
        for i in range(36): # 36 frames for a full 360-degree hue shift (10 degrees per frame)
            # Convert to HSV
            h, s, v = img.convert("HSV").split()
            
            # Shift hue
            # Numpy is efficient for pixel manipulation
            h_array = np.array(h, dtype=np.int16) # Use int16 for intermediate calculation to avoid overflow
            hue_shift_amount = int((i * 10) * (255.0 / 360.0)) # Map 0-360 degrees to 0-255
            shifted_h_array = np.mod(h_array + hue_shift_amount, 256).astype(np.uint8) # Modulo 256 for hue
            
            shifted_h_image = Image.fromarray(shifted_h_array, 'L') # Create image from hue channel
            
            # Merge back to HSV and then convert to RGBA
            gaming_frame_hsv = Image.merge("HSV", (shifted_h_image, s, v))
            frames.append(gaming_frame_hsv.convert("RGBA")) # Convert back to RGBA for saving in GIF
            
        output_buffer = io.BytesIO()
        # Save as GIF
        # `disposal=2` means restore to background color (important for transparency)
        frames[0].save(output_buffer, format="GIF", save_all=True, append_images=frames[1:], 
                       duration=duration_ms, loop=0, disposal=2, optimize=True)
        output_buffer.seek(0)
        return output_buffer
    except Exception as e_gif:
        print(f"Error creating gaming GIF: {e_gif}")
        traceback.print_exc()
        return None

# GEMINI HELPERS (unchanged)
async def generate_gemini_text_response(prompt_parts: list) -> str: # ...
    global GEMINI_API_UNAVAILABLE
    if not gemini_text_model_instance or GEMINI_API_UNAVAILABLE:
        return "Error: Gemini Text API is not available."
    try:
        response = await asyncio.to_thread(
            gemini_text_model_instance.generate_content,
            prompt_parts,
            request_options={'timeout': 120} 
        )
        if hasattr(response, 'text') and response.text:
            return response.text
        elif response.candidates and response.candidates[0].finish_reason:
            return f"Could not generate response. Reason: {response.candidates[0].finish_reason.name}"
        elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
            return f"Prompt blocked. Reason: {response.prompt_feedback.block_reason.name}"
        else:
            print(f"Unexpected Gemini text response format: {response}")
            return "Could not generate response. Unexpected format."
    except Exception as e:
        print(f"Gemini Text API Error: {type(e).__name__} - {e}")
        traceback.print_exc()
        return f"Gemini Text API Error: {type(e).__name__} - {e}"
async def generate_summary_with_gemini(text: str, num_points: int = 3) -> str: # ...
    prompt = f"以下の文章を日本語で{num_points}個の短い箇条書きに要約してください:\n\n{text}"
    return await generate_gemini_text_response([prompt])

# VOICEVOX & RVC HELPERS (unchanged)
async def generate_voicevox_audio(text_to_speak: str, speaker_id: int, api_key: str) -> io.BytesIO | None: # ...
    if not api_key or api_key == "YOUR_VOICEVOX_API_KEY_PLACEHOLDER": # Generic placeholder check
        print("VoiceVox API key is not configured or is a placeholder.")
        return None
    
    print(f"Attempting VoiceVox TTS. API Key used: '{api_key[:5]}...', Speaker ID: {speaker_id}") # Mask key in log
    
    params_dict = {
        "text": text_to_speak,
        "speaker": str(speaker_id), 
        "key": api_key
    }
    
    print(f"Requesting VoiceVox TTS for text: '{text_to_speak[:50]}...'")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(VOICEVOX_API_BASE_URL, params=params_dict, timeout=aiohttp.ClientTimeout(total=60)) as response:
                print(f"VoiceVox API response status: {response.status}, Content-Type: {response.content_type}")

                if response.status == 200:
                    if response.content_type in ('audio/wav', 'audio/x-wav'):
                        audio_data = await response.read()
                        print(f"VoiceVox TTS success, received {len(audio_data)} bytes of {response.content_type} data.")
                        return io.BytesIO(audio_data)
                    else:
                        error_text_body = "(Could not decode body as text)"
                        try: error_text_body = (await response.text())[:200]
                        except: pass
                        print(f"VoiceVox API returned 200 OK but with unexpected Content-Type ({response.content_type}): {error_text_body}")
                        return None
                else: # Non-200 status
                    error_text_body = "(Could not decode error body as text)"
                    try: error_text_body = (await response.text())[:500]
                    except: pass
                    print(f"VoiceVox API request failed with status {response.status}: {error_text_body}")
                    if response.status == 403: print("  (This might be an API key issue or access restriction)")
                    return None
    except asyncio.TimeoutError:
        print("VoiceVox API request timed out.")
        return None
    except Exception as e:
        print(f"Error during VoiceVox API call: {e}")
        traceback.print_exc()
        return None
async def process_audio_with_rvc(ctx: commands.Context, audio_bytes_io: io.BytesIO, original_filename_base: str, input_file_extension_no_dot: str): # ...
    # ... (Full implementation as provided before)
    try:
        temp_audio_stream_for_check = io.BytesIO(audio_bytes_io.getvalue())
        temp_audio_stream_for_check.seek(0)
        audio_segment = AudioSegment.from_file(temp_audio_stream_for_check, format=input_file_extension_no_dot)
        duration_seconds = len(audio_segment) / 1000.0
        print(f"Audio duration for RVC: {duration_seconds:.2f} seconds")
        temp_audio_stream_for_check.close()

        if duration_seconds > 45.0:
            await ctx.send(f"エラー: 音声が長すぎます ({duration_seconds:.1f}秒)。45秒以下の音声にしてください。")
            return False
    except CouldntDecodeError:
        await ctx.send("エラー: 音声ファイルの形式を認識できませんでした。有効な音声ファイルか確認してください。")
        return False
    except Exception as e_dur:
        await ctx.send(f"エラー: 音声ファイルの長さ確認中に問題が発生しました: {e_dur}")
        traceback.print_exc()
        return False
    finally:
        audio_bytes_io.seek(0)

    rvc_infer_script_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    rvc_model_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    rvc_index_file_name_no_ext, _ = os.path.splitext(RVC_MODEL_NAME_WITH_EXT)
    rvc_index_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, f"{rvc_index_file_name_no_ext}.index")

    if not os.path.exists(rvc_infer_script_full_path) or not os.path.exists(rvc_model_full_path):
        await ctx.send("エラー: RVC関連ファイルが見つかりません。Bot管理者に連絡してください。"); return False

    processing_message = await ctx.send("**やまかわボイチェンの処理をしています...** \nしばらくお待ちください... (目安:20~50秒)")
    timestamp = datetime.datetime.now(JST).strftime("%Y%m%d%H%M%S%f"); unique_id = f"{ctx.author.id}_{ctx.message.id}_{timestamp}"
    input_filename_rvc = f"input_{unique_id}.{input_file_extension_no_dot}"
    output_filename_rvc = f"output_{unique_id}.{input_file_extension_no_dot}" # RVC typically outputs wav, adjust if different
    input_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_INPUT_AUDIO_DIR, input_filename_rvc))
    output_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_OUTPUT_AUDIO_DIR, output_filename_rvc))
    
    success_flag = False
    try:
        with open(input_filepath_abs_rvc, 'wb') as f_out:
            audio_bytes_io.seek(0) 
            f_out.write(audio_bytes_io.getbuffer())
        print(f"Saved input audio for RVC to: {input_filepath_abs_rvc}")

        effective_python_executable = sys.executable 
        command = [effective_python_executable, rvc_infer_script_full_path, 
                   "--f0up_key", str(RVC_FIXED_TRANSPOSE), "--input_path", input_filepath_abs_rvc, 
                   "--opt_path", output_filepath_abs_rvc, "--model_name", RVC_MODEL_NAME_WITH_EXT]
        if os.path.exists(rvc_index_full_path): command.extend(["--feature_path", rvc_index_full_path])
        
        print(f"Executing RVC command: {' '.join(command)}")
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=RVC_PROJECT_ROOT_PATH)
        stdout_bytes, stderr_bytes = await process.communicate()
        # ... (stdout/stderr logging) ...
        if stdout_bytes: print(f"--- RVC STDOUT ---\n{stdout_bytes.decode('utf-8', errors='ignore').strip()}\n------------------")
        if stderr_bytes: print(f"--- RVC STDERR ---\n{stderr_bytes.decode('utf-8', errors='ignore').strip()}\n------------------")
        
        if process.returncode != 0:
            await processing_message.edit(content=f"音声変換中にエラーが発生しました (RVCプロセス)。")
        elif os.path.exists(output_filepath_abs_rvc) and os.path.getsize(output_filepath_abs_rvc) > 0:
            await processing_message.edit(content="**やまかわてるきボイチェンの処理が完了しました**")
            # Ensure the output filename for Discord reflects the content (e.g., if RVC always outputs wav)
            discord_output_filename = f"rvc_{original_filename_base}.wav" # Assuming RVC outputs wav
            await ctx.send(file=discord.File(output_filepath_abs_rvc, filename=discord_output_filename))
            success_flag = True
        else:
            await processing_message.edit(content="変換は成功しましたが、出力ファイルが見つかりませんでした。")
    except Exception as e:
        await processing_message.edit(content=f"予期せぬエラーが発生しました (RVC処理): {e}")
        traceback.print_exc()
    finally: # Cleanup temp files
        if os.path.exists(input_filepath_abs_rvc):
            try: os.remove(input_filepath_abs_rvc)
            except Exception as e_rem: print(f"Failed to delete RVC input temp: {e_rem}")
        if os.path.exists(output_filepath_abs_rvc): # Always try to delete RVC output after sending or on failure
            try: os.remove(output_filepath_abs_rvc)
            except Exception as e_rem: print(f"Failed to delete RVC output temp: {e_rem}")
    return success_flag

# TEXT IMAGE DRAWING HELPER (Updated for new outline logic)
# TEXT IMAGE DRAWING HELPER (Updated for new outline logic)
def draw_text_layered_outline(draw, base_pos, char_text, font, 
                              text_color,
                              middle_outline_color,
                              middle_outline_total_thickness,
                              outer_outline_color,
                              outer_outline_total_thickness):
    x, y = base_pos
    
    # Layer 1: Outermost outline (e.g., White)
    # This outline extends 'outer_outline_total_thickness' pixels from the text edge.
    # This is the total distance from the very center of the char glyph to the outermost edge of this layer
    for dx_outer in range(-outer_outline_total_thickness, outer_outline_total_thickness + 1):
        for dy_outer in range(-outer_outline_total_thickness, outer_outline_total_thickness + 1):
            # Use a circular shape for the outline 'brush'
            if dx_outer*dx_outer + dy_outer*dy_outer <= outer_outline_total_thickness*outer_outline_total_thickness :
                 draw.text((x + dx_outer, y + dy_outer), char_text, font=font, fill=outer_outline_color)
    
    # Layer 2: Middle outline (e.g., Black)
    # This outline extends 'middle_outline_total_thickness' pixels from the text edge.
    # It's drawn on top of the outer outline.
    for dx_middle in range(-middle_outline_total_thickness, middle_outline_total_thickness + 1):
        for dy_middle in range(-middle_outline_total_thickness, middle_outline_total_thickness + 1):
            if dx_middle*dx_middle + dy_middle*dy_middle <= middle_outline_total_thickness*middle_outline_total_thickness:
                draw.text((x + dx_middle, y + dy_middle), char_text, font=font, fill=middle_outline_color)
    
    # Layer 3: Main text
    draw.text((x, y), char_text, font=font, fill=text_color)


# ================================== DISCORD EVENTS ==================================
@bot.event
async def on_ready(): # ... (Slightly updated print statements, font check)
    print(f'Logged in as: {bot.user.name} ({bot.user.id})')
    load_settings(); load_game_points()
    # await load_weather_city_codes() # Not used by YOLP directly

    print(f"Settings loaded. Allowed channels: {len(allowed_channels)}")
    print(f"Game points loaded for {len(game_points)} players.")
    
    gemini_status = "Available" if not GEMINI_API_UNAVAILABLE else "Not Available"
    print(f"Gemini API Status: {gemini_status}")
    
    vv_status = "Available" if VOICEVOX_API_KEY and VOICEVOX_API_KEY != "YOUR_VOICEVOX_API_KEY_PLACEHOLDER" else "Not Available"
    print(f"VoiceVox API Status: {vv_status}")

    yolp_status = "Client ID Set" if YAHOO_CLIENT_ID and YAHOO_CLIENT_ID != "YOUR_YAHOO_CLIENT_ID_PLACEHOLDER" else "Client ID Missing/Placeholder"
    print(f"Yahoo Weather API (YOLP) Status: {yolp_status}")

    if not os.path.exists(TEXT_IMAGE_FONT_PATH):
        print(f"CRITICAL WARNING: Text command font not found at {TEXT_IMAGE_FONT_PATH}. 'text' command will fail.")
    else:
        print(f"Text command font found: {TEXT_IMAGE_FONT_PATH}")

    print("--- RVC Checks ---") # ... (RVC checks unchanged)
    rvc_infer_script_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    if not os.path.exists(rvc_infer_script_full_path): print(f"  WARNING: RVC inference script NOT FOUND: {rvc_infer_script_full_path}")
    else: print(f"  RVC inference script OK: {rvc_infer_script_full_path}")
    rvc_model_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    if not os.path.exists(rvc_model_full_path): print(f"  WARNING: RVC model '{RVC_MODEL_NAME_WITH_EXT}' NOT FOUND: {rvc_model_full_path}")
    else: print(f"  RVC model '{RVC_MODEL_NAME_WITH_EXT}' OK: {rvc_model_full_path}")
    print("------------------")

    try: synced = await bot.tree.sync(); print(f'Synced {len(synced)} slash commands.')
    except Exception as e: print(f"Slash command sync failed: {e}")
    
    if not cleanup_finished_games_task.is_running(): cleanup_finished_games_task.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help 杉山啓太Bot by(*'▽')"))
    print("Bot is ready and watching.")

@bot.event
async def on_message(message: discord.Message): # ... (Unchanged)
    if message.author == bot.user or message.author.bot or not message.guild: return

    original_content = message.content
    content_lower_stripped = original_content.strip().lower()
    
    if content_lower_stripped.startswith("setchannel"):
        _content_backup = message.content
        message.content = f"{get_dummy_prefix(bot, message)}setchannel" 
        await bot.process_commands(message)
        message.content = _content_backup # Restore original content for other potential listeners
        return

    if message.channel.id not in allowed_channels: return

    command_parts = original_content.split(" ", 1)
    potential_command_name = command_parts[0].lower()
    
    is_othello_subcommand = False
    if potential_command_name == "othello" and len(command_parts) > 1:
        sub_command_parts = command_parts[1].split(" ", 1)
        sub_command_name = sub_command_parts[0].lower()
        if sub_command_name == "leave":
            potential_command_name = "leave"; command_parts = [potential_command_name]; is_othello_subcommand = True
        elif sub_command_name in ["point", "points"]:
            potential_command_name = "othello_points"; command_parts = [potential_command_name]; is_othello_subcommand = True
    
    command_obj = bot.get_command(potential_command_name)

    if command_obj:
        print(f"Prefix-less command '{potential_command_name}' detected from '{message.author.name}'. Processing...")
        _content_backup_cmd = message.content
        prefix_to_use = get_dummy_prefix(bot, message)
        
        if is_othello_subcommand: # Subcommands like "othello leave" are handled by "leave" command directly
            message.content = f"{prefix_to_use}{potential_command_name}"
        elif len(command_parts) > 1: # Command with arguments
            args_part = command_parts[1]
            message.content = f"{prefix_to_use}{potential_command_name} {args_part}".strip()
        else: # Command without arguments
            message.content = f"{prefix_to_use}{potential_command_name}"
        
        print(f"  Modified message content for processing: '{message.content}'")
        await bot.process_commands(message)
        message.content = _content_backup_cmd # Restore for safety, though usually not needed after process_commands


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User): # ... (Janken host part removed, Othello part unchanged)
    if user == bot.user: return
    message = reaction.message; message_id = message.id

    # Othello recruitment logic
    if message_id in othello_recruitments: # ... (unchanged othello recruitment)
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

    # Othello game move logic
    if message_id in active_games: # ... (unchanged othello game move)
        game_session = active_games.get(message_id)
        if not game_session: return
        game = game_session["game"]
        if user.id not in game.players.values() or game.game_over:
            try: await reaction.remove(user) # User not part of this game or game is over
            except discord.HTTPException: pass
            return
        if user.id != game.players.get(game.current_player): # Not current player's turn
            try: await reaction.remove(user)
            except discord.HTTPException: pass
            return
        
        chosen_move = next((coord for coord, marker_emoji in game.valid_moves_with_markers.items() if str(reaction.emoji) == marker_emoji), None)
        if chosen_move:
            if game.make_move(chosen_move[0], chosen_move[1], game.current_player):
                if game.afk_task and not game.afk_task.done(): game.afk_task.cancel() # Cancel previous AFK task
                game.switch_player(); game.check_game_status()
                await send_othello_board_message(message.channel, game_session, message_to_update=message)
                if not game.game_over: # Start new AFK task if game continues
                    game.afk_task = asyncio.create_task(othello_afk_timeout(game))
        try: await reaction.remove(user) # Remove user's reaction after processing or if invalid
        except discord.HTTPException: pass
        return

    # Janken game logic (Opponent's turn via reaction)
    if message_id in active_janken_games: # ... (Janken opponent reaction unchanged)
        game_data = active_janken_games[message_id]
        if game_data["game_status"] == "opponent_recruiting" and user.id != game_data["host_id"] and not user.bot:
            if str(reaction.emoji) in HAND_EMOJIS.values() and game_data["opponent_id"] is None: # First valid opponent
                game_data["opponent_id"] = user.id
                game_data["opponent_hand"] = EMOJI_TO_HAND[str(reaction.emoji)]
                game_data["game_status"] = "finished"

                # Fetch users (ensure they exist)
                try:
                    host_user = await bot.fetch_user(game_data["host_id"])
                    opponent_user = user # The user who reacted is the opponent
                except discord.NotFound:
                    print(f"Janken: Could not find user for host {game_data['host_id']} or opponent {user.id}")
                    # Clean up game if users can't be fetched?
                    if message_id in active_janken_games: del active_janken_games[message_id]
                    try: await game_data["message"].edit(content="じゃんけんエラー: ユーザーが見つかりませんでした。", embed=None, view=None)
                    except: pass
                    return

                result_text, host_points_change, opponent_points_change = determine_janken_winner(
                    game_data["host_hand"], game_data["opponent_hand"]
                )
                
                update_player_points(game_data["host_id"], host_points_change)
                update_player_points(game_data["opponent_id"], opponent_points_change)

                embed_result = discord.Embed(title="じゃんけん 結果", color=discord.Color.gold())
                embed_result.add_field(name="対戦", value=f"{host_user.mention} ({HAND_EMOJIS[game_data['host_hand']]}) vs {opponent_user.mention} ({HAND_EMOJIS[game_data['opponent_hand']]})", inline=False)
                embed_result.add_field(name="結果", value=result_text, inline=False)
                embed_result.add_field(name="ポイント変動", 
                                       value=f"{host_user.mention}: {get_player_points(game_data['host_id'])}pt ({'+' if host_points_change >= 0 else ''}{host_points_change}pt)\n"
                                             f"{opponent_user.mention}: {get_player_points(game_data['opponent_id'])}pt ({'+' if opponent_points_change >= 0 else ''}{opponent_points_change}pt)", 
                                       inline=False)
                try:
                    if game_data["message"]: # Ensure message object is still valid
                        await game_data["message"].edit(embed=embed_result, view=None) # Clear buttons/reactions
                except discord.HTTPException as e:
                    print(f"Error editing Janken result message: {e}")
                
                if message_id in active_janken_games: del active_janken_games[message_id]
            
            elif game_data["opponent_id"] is not None and user.id != game_data["opponent_id"]: # Another user tried to join after opponent found
                try: await reaction.remove(user) 
                except: pass
            elif str(reaction.emoji) not in HAND_EMOJIS.values(): # Invalid emoji
                try: await reaction.remove(user)
                except: pass
            return # Janken logic handled
        elif game_data["game_status"] == "opponent_recruiting" and user.id == game_data["host_id"]: # Host reacting on own msg
            try: await reaction.remove(user)
            except: pass
            return

# Othello AFK Timeout - Point logic for AFK/Leave should be reviewed based on new rules if necessary
# Current AFK point logic: winner (non-AFK) gets ceil(score_diff/2) [min 1], AFK player loses score_diff
async def othello_afk_timeout(game: OthelloGame):
    # ... (AFK timeout logic for Othello - needs review for point consistency if desired) ...
    # For now, keeping AFK point logic separate from normal game end.
    # If new othello rules should apply to AFK, this needs adjustment.
    await asyncio.sleep(OTHELLO_AFK_TIMEOUT_SECONDS)
    game_message_id = getattr(game, 'message_id', None)
    if not game_message_id: return

    game_session_from_active = active_games.get(game_message_id)
    if game_session_from_active and game_session_from_active.get("game") == game and not game.game_over:
        print(f"Othello Game #{game.game_id}: AFK timeout for player {game.players.get(game.current_player)}")
        
        afk_player_id = game.players.get(game.current_player)
        opponent_id = game.get_opponent_player_id() 

        game.game_over = True
        # AFK player is current player, so opponent (other color) wins
        game.winner = WHITE if game.current_player == BLACK else BLACK 
        setattr(game, 'ended_by_action', 'afk')
        
        bs = sum(r.count(BLACK) for r in game.board)
        ws = sum(r.count(WHITE) for r in game.board)
        score_diff_afk = abs(bs - ws) if bs != ws else 1 # Min 1 point difference for calculation
        
        afk_player_user = await bot.fetch_user(afk_player_id) if afk_player_id else None
        winner_player_user = await bot.fetch_user(opponent_id) if opponent_id else None
        afk_mention = afk_player_user.mention if afk_player_user else f"ID:{afk_player_id}"
        winner_mention = winner_player_user.mention if winner_player_user else f"ID:{opponent_id}"
        
        point_message = ""
        if opponent_id and afk_player_id:
            # Example AFK Penalty: Winner gets fixed points, AFK player loses fixed points or based on diff
            points_for_winner_afk = 10  # Example: Fixed 10 points for non-AFK player
            points_lost_by_afk = -15    # Example: Fixed -15 points for AFK player
            
            # Or based on new rules (less harsh for AFK loser?):
            # points_for_winner_afk = (score_diff_afk * 3) + 10 # Same as win
            # points_for_afk_player = max(0, 20 - score_diff_afk) # Loser rule for AFK
            # points_change_for_afk_player = points_for_afk_player - get_player_points(afk_player_id)
            # update_player_points(afk_player_id, points_change_for_afk_player)


            update_player_points(opponent_id, points_for_winner_afk)
            update_player_points(afk_player_id, points_lost_by_afk) # Direct loss
            point_message = f"({winner_mention} +{points_for_winner_afk}pt, {afk_mention} {points_lost_by_afk}pt)"
        
        channel = bot.get_channel(game.channel_id)
        if channel:
            await channel.send(f"ゲーム #{game.game_id}: {afk_mention} が{OTHELLO_AFK_TIMEOUT_SECONDS//60}分以上行動しなかったため、{winner_mention} の勝利です！ {point_message}")
        
        message_to_update = None
        if channel and game.message_id:
            try: message_to_update = await channel.fetch_message(game.message_id)
            except: pass
        if message_to_update: # Ensure message object exists
            await send_othello_board_message(channel or None, game_session_from_active, message_to_update=message_to_update)


# ... (cleanup_finished_games_task は変更なし) ...
@tasks.loop(minutes=5)
async def cleanup_finished_games_task():
    # Othello cleanup
    othello_games_to_remove_ids = []
    current_time_jst = datetime.datetime.now(JST)
    for msg_id, game_session_data in list(active_games.items()):
        game_obj = game_session_data.get("game")
        if game_obj and game_obj.game_over and \
           (current_time_jst - game_obj.last_move_time > datetime.timedelta(hours=1)):
            othello_games_to_remove_ids.append(msg_id)
            if game_obj.afk_task and not game_obj.afk_task.done():
                game_obj.afk_task.cancel()
            OthelloGame._release_game_id_static(game_obj.game_id) 
    for msg_id in othello_games_to_remove_ids:
        if msg_id in active_games: del active_games[msg_id]
    if othello_games_to_remove_ids: print(f"Cleaned up {len(othello_games_to_remove_ids)} old finished othello games from active_games.")

    # Janken cleanup
    janken_games_to_remove_ids = []
    for msg_id, j_game_data in list(active_janken_games.items()):
        try:
            game_msg_obj = j_game_data.get("message")
            if game_msg_obj:
                msg_age = current_time_jst - game_msg_obj.created_at.astimezone(JST)
                if msg_age > datetime.timedelta(minutes=30) and j_game_data.get("game_status") != "finished":
                    janken_games_to_remove_ids.append(msg_id)
        except Exception as e:
            print(f"Error during Janken cleanup check for msg_id {msg_id}: {e}")

    for msg_id in janken_games_to_remove_ids:
        if msg_id in active_janken_games:
            try:
                game_msg_obj = active_janken_games[msg_id].get("message")
                if game_msg_obj:
                    await game_msg_obj.edit(embed=discord.Embed(title="じゃんけん", description="このじゃんけんゲームは時間切れにより終了しました。", color=discord.Color.orange()), view=None)
            except Exception as e_clean_msg:
                print(f"Error cleaning up Janken message {msg_id}: {e_clean_msg}")
            del active_janken_games[msg_id]
            print(f"Cleaned up stale Janken game (ID: {msg_id}).")


# ================================== DISCORD COMMANDS ==================================
@bot.command(name="help")
async def help_command(ctx: commands.Context):
    embed = discord.Embed(title="杉山啓太Bot コマンド一覧", color=discord.Color.blue())
    cmds = [
        ("watermark + [画像添付]", "添付画像にウォーターマークを合成。"),
        ("/imakita", "過去30分のチャットを3行で要約。(スラッシュコマンド・どこでも利用可、1分13回制限)"),
        ("5000 [上文字列] [下文字列] (hoshii) (rainbow)", "「5000兆円欲しい！」画像を生成。"),
        ("gaming + [画像添付]", "添付画像をゲーミング風GIFに変換。"),
        ("othello (@相手ユーザー)", 
         "・`othello` : オセロの対戦相手を募集します。\n"
         "・`othello @メンション` : 指定したユーザーと即時対戦を開始します。\n"
         "・`othello leave` : 進行中のオセロゲームから離脱します。\n"
         "・`othello point` : あなたの現在のゲームポイントとランキングを表示。\n"
         "・ポイント: 勝者 (石差×3)+10pt, 敗者 max(0, 20-石差)pt\n"),
        ("voice [テキスト] または [音声ファイル添付]", 
         "・`voice こんにちは` : 入力テキストをやまかわてるきの声に変換。（VoiceVox経由）\n"
         "・音声ファイル添付: 添付音声の声をやまかわてるきの声に変換。（45秒まで）"),
        ("janken", "じゃんけんを開始します。ボタン/リアクションで手を選んで勝負！ (勝者:+7pt, 敗者:-5pt)"),
        ("bet [金額]", "指定したポイントを賭けてシンプルなダイスゲームに挑戦。 (例: `bet 10`)"),
        ("text [文字列] (,で改行) (squareで正方形化)", "指定スタイルで文字画像を生成。(例: `text クッソ,でけえや square`)"),
        ("ping", "Botの応答速度を表示。"),
        ("tenki [都市名]", "指定した日本の都市の天気予報を表示。(例: `tenki 東京`)"),
        ("info (@ユーザー)", "指定したユーザー(または自分)の情報を表示。"),
        ("rate [金額] [通貨コード]", "指定した外貨を日本円に換算。(例: `rate 100 USD`)"),
        ("shorturl [URL]", "URLを短縮します。(x.gd使用)"),
        ("amazon [Amazon URL]", "AmazonのURLを短縮します。"),
        ("totusi [文字列]", "＿人人人＿風のAAを生成。"),
        ("time (国コード)", "現在時刻を表示。国コード指定でその国の時刻も。(例: `time US`, `time help`で一覧)"),
        ("help", "このヘルプを表示。"),
        ("setchannel", "Botのコマンド利用を許可/禁止する。(管理者のみ)"),
        ("その他", "コマンド詳細は [GitHub](https://github.com/y-exe/sugiyama-bot) を参照してください。")
    ]
    for name, value in cmds: embed.add_field(name=name, value=value, inline=False)
    status_gemini = "Available" if not GEMINI_API_UNAVAILABLE else "Not Available"
    status_vv = "Available" if VOICEVOX_API_KEY and VOICEVOX_API_KEY != "YOUR_VOICEVOX_API_KEY_PLACEHOLDER" else "Not Available"
    font_status = "OK" if os.path.exists(TEXT_IMAGE_FONT_PATH) else "フォント無し"
    embed.set_footer(text=f"Gemini: {status_gemini} | VoiceVox: {status_vv} | Text画像フォント: {font_status}")
    await ctx.send(embed=embed)


# ... (setchannel_command, watermark_command, five_k_choyen_command, gaming_command, othello_command, game_points_command, leave_othello_game_command は変更なし、または微修正) ...
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
        
        final_b_io = await asyncio.to_thread(_process_and_composite_image, img_b, sel_t)
        if final_b_io:
            final_b_resized_io, resized_flag = await _resize_image_if_too_large(final_b_io, "PNG")
            if final_b_resized_io is None: return await ctx.send("ウォーターマーク画像の処理中にエラーが発生しました。")
            
            final_b_resized_io.seek(0, io.SEEK_END); file_size = final_b_resized_io.tell(); final_b_resized_io.seek(0)
            if file_size > MAX_FILE_SIZE_BYTES: 
                return await ctx.send(f"加工後画像のファイルサイズが大きすぎます ({file_size / (1024*1024):.2f}MB)。")

            out_fname = f"wm_{os.path.splitext(att.filename)[0]}.png"
            await ctx.send(f"加工完了！ (使用: {sel_t['name']}){' (リサイズ済)' if resized_flag else ''}", file=discord.File(fp=final_b_resized_io, filename=out_fname))
            if final_b_resized_io != final_b_io : final_b_io.close() # Close original if different
            final_b_resized_io.close()
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
            gif_buffer_io = await asyncio.to_thread(_create_gaming_gif, image_bytes)
            if gif_buffer_io is None: return await ctx.send("ゲーミングGIFの生成に失敗しました。")

            gif_buffer_resized_io, resized_flag = await _resize_image_if_too_large(gif_buffer_io, "GIF")
            if gif_buffer_resized_io is None: return await ctx.send(f"ゲーミングGIFのリサイズ処理中にエラーが発生しました。")
            
            gif_buffer_resized_io.seek(0, io.SEEK_END); file_size = gif_buffer_resized_io.tell(); gif_buffer_resized_io.seek(0)
            if file_size > MAX_FILE_SIZE_BYTES: 
                return await ctx.send(f"生成GIFのファイルサイズが大きすぎます ({file_size / (1024*1024):.2f}MB)。")

            out_fname = f"gaming_{os.path.splitext(attachment.filename)[0]}.gif"
            await ctx.send(f"**ゲーミング風GIFを生成完了**\nうまくいかない場合は黒白ではなくカラー画像を添付してください {' (リサイズ済)' if resized_flag else ''}", file=discord.File(fp=gif_buffer_resized_io, filename=out_fname))
            if gif_buffer_resized_io != gif_buffer_io: gif_buffer_io.close()
            gif_buffer_resized_io.close()
        except Exception as e: await ctx.send(f"ゲーミングGIFの生成中にエラー: {e}")


@bot.command(name="othello")
async def othello_command(ctx: commands.Context, opponent: discord.Member = None):
    host_id = ctx.author.id
    if opponent:
        if opponent == ctx.author: return await ctx.send("自分自身とは対戦できません。")
        if opponent.bot: return await ctx.send("Botとは対戦できません。")
    
    # Check if host or opponent is already in an active othello game or recruitment
    for game_session_data in active_games.values():
        game_obj = game_session_data.get("game")
        if game_obj and (host_id in game_obj.players.values() or (opponent and opponent.id in game_obj.players.values())):
            await ctx.send("あなたまたは指定された相手は既に参加中のオセロゲームがあります。まずはそちらを終了してください (`othello leave` コマンド)。")
            return
    for rec_info in othello_recruitments.values():
        if host_id == rec_info["host_id"] or (opponent and opponent.id == rec_info["host_id"]):
            await ctx.send("あなたまたは指定された相手は既にオセロの対戦相手を募集中です。")
            return

    if opponent : # Direct match
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

    # Recruitment
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
async def game_points_command(ctx: commands.Context):
    points = get_player_points(ctx.author.id)
    # Sort by points descending, then by player ID ascending for tie-breaking (optional)
    sorted_points_data = sorted(game_points.items(), key=lambda item: (item[1], int(item[0])), reverse=True)
    
    embed = discord.Embed(title="ゲームポイントランキング", color=discord.Color.gold())
    rank_text_parts = []
    user_rank_info = f"\nあなたの順位: {ctx.author.mention} - {points}pt (ランキング外または未プレイ)"
    user_found_in_top = False

    for i, (player_id_str, player_points_val) in enumerate(sorted_points_data[:10]): # Top 10
        rank = i + 1
        try:
            user = await bot.fetch_user(int(player_id_str))
            user_display = user.mention if user else f"ID:{player_id_str}"
            medal = ""
            if rank == 1: medal = "🥇 "
            elif rank == 2: medal = "🥈 "
            elif rank == 3: medal = "🥉 "
            
            rank_text_parts.append(f"{medal}{rank}位 {user_display} - {player_points_val}pt")
            if user and user.id == ctx.author.id:
                user_rank_info = f"\nあなたの順位: **{medal}{rank}位** {user.mention} - **{player_points_val}pt**"
                user_found_in_top = True
        except ValueError: # If player_id_str is not a valid int (should not happen with current setup)
            rank_text_parts.append(f"{rank}位 ID:{player_id_str} (取得エラー) - {player_points_val}pt")
        except discord.NotFound:
             rank_text_parts.append(f"{rank}位 ID:{player_id_str} (不明なユーザー) - {player_points_val}pt")


    if not rank_text_parts: rank_text_parts.append("まだポイントを持っているプレイヤーがいません。")
    
    if not user_found_in_top and points > 0: # If user has points but not in top 10
        for i, (pid_str, p_points_val) in enumerate(sorted_points_data):
            if int(pid_str) == ctx.author.id:
                user_rank_info = f"\nあなたの順位: **{i+1}位** {ctx.author.mention} - **{points}pt**"
                break
                
    embed.description = "\n".join(rank_text_parts) + user_rank_info
    embed.set_footer(text="このポイントはオセロ(othello)・じゃんけん(janken)・賭け(bet)で共通です。")
    await ctx.send(embed=embed)


# Othello Leave Command - Point logic for leaver/opponent should be reviewed if new rules apply
# Current: Leaver loses score_diff, opponent gains ceil(score_diff/2) [min 1]
@bot.command(name="leave", aliases=["othello_leave"])
async def leave_othello_game_command(ctx: commands.Context):
    # ... (leave othello logic, consider point consistency with new othello rules if leaver should get 20-diff or similar)
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

    confirm_msg = await ctx.send(f"{ctx.author.mention} ゲーム #{game_to_leave.game_id} を本当に離脱しますか？ (相手の勝利扱いになり、ポイントが変動します)")
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
            # Winner is the opponent
            game_to_leave.winner = next(color for color, pid in game_to_leave.players.items() if pid == opponent_id) 

            bs = sum(r.count(BLACK) for r in game_to_leave.board)
            ws = sum(r.count(WHITE) for r in game_to_leave.board)
            score_diff_leave = abs(bs - ws) if bs != ws else 1 # Min 1 point diff
            point_message = ""

            if opponent_id and player_id_to_leave:
                # Example Leave Penalty: Opponent gets fixed points, Leaver loses fixed points
                points_for_opponent_leave = 15 # Fixed points for opponent
                points_lost_by_leaver = -20    # Fixed points leaver loses
                
                # Or apply a variation of the new rules?
                # points_for_opponent_leave = (score_diff_leave * 3) + 10
                # points_for_leaver_calc = max(0, 20 - score_diff_leave) 
                # update_player_points(player_id_to_leave, points_for_leaver_calc - get_player_points(player_id_to_leave)) # if it means setting their points
                # OR: leaver loses more, e.g., -( (score_diff_leave * 1) + 5 )

                update_player_points(opponent_id, points_for_opponent_leave) 
                update_player_points(player_id_to_leave, points_lost_by_leaver) # Direct loss    
                
                winner_user_for_msg = await bot.fetch_user(opponent_id)
                point_message = f"({winner_user_for_msg.mention if winner_user_for_msg else '相手'} +{points_for_opponent_leave}pt, {ctx.author.mention} {points_lost_by_leaver}pt)"

            try:
                winner_user = await bot.fetch_user(opponent_id)
                loser_user = await bot.fetch_user(player_id_to_leave) # This is ctx.author
                await ctx.send(f"{loser_user.mention} がゲーム #{game_to_leave.game_id} から離脱しました。{winner_user.mention} の勝利です！ {point_message}")
            except Exception as e_fetch: print(f"Error fetching users on game leave: {e_fetch}")
            
            board_channel = bot.get_channel(game_to_leave.channel_id) or ctx.channel
            board_message_to_update = None
            if board_channel and game_to_leave.message_id:
                try: board_message_to_update = await board_channel.fetch_message(game_to_leave.message_id)
                except: pass
            if board_message_to_update: # Ensure message object exists
                await send_othello_board_message(board_channel, game_session_to_leave, message_to_update=board_message_to_update)
        else: await ctx.send("離脱をキャンセルしました。", delete_after=10)
    except asyncio.TimeoutError:
        try: await confirm_msg.delete()
        except: pass
        await ctx.send("離脱の確認がタイムアウトしました。", delete_after=10)


@bot.tree.command(name="imakita", description="過去30分のチャットを3行で要約します。")
async def imakita_slash(interaction: discord.Interaction):
    global imakita_request_timestamps

    current_time = datetime.datetime.now().timestamp()
    # Remove timestamps older than RATE_LIMIT_SECONDS
    while imakita_request_timestamps and imakita_request_timestamps[0] < current_time - IMAKITA_RATE_LIMIT_SECONDS:
        imakita_request_timestamps.popleft()

    if len(imakita_request_timestamps) >= IMAKITA_RATE_LIMIT_COUNT:
        await interaction.response.send_message(
            f"APIリクエストが集中しています。しばらく時間をおいて再度お試しください。(あと約 {int(IMAKITA_RATE_LIMIT_SECONDS - (current_time - imakita_request_timestamps[0]))}秒)",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    imakita_request_timestamps.append(current_time) # Add new request timestamp

    if not hasattr(interaction.channel, 'history'):
         return await interaction.followup.send("このチャンネルではメッセージ履歴を取得できません。", ephemeral=True)

    after_time = discord.utils.utcnow() - datetime.timedelta(minutes=30)
    c_list = [f"{m.author.display_name}: {m.content}" async for m in interaction.channel.history(limit=200, after=after_time) if m.author != bot.user and not m.author.bot and m.content]
    if not c_list: return await interaction.followup.send("過去30分にメッセージはありませんでした。", ephemeral=True)
    
    summary = await generate_summary_with_gemini("\n".join(reversed(c_list)), 3)
    msg = f"**今北産業:**\n{summary}" if not summary.startswith("Error:") else f"要約エラー:\n{summary}"
    await interaction.followup.send(msg, ephemeral=True)

# ... (generate_voicevox_audio, process_audio_with_rvc, rvc_voice_convert_command は変更なし) ...
# --- VoiceVox Helper ---
async def generate_voicevox_audio(text_to_speak: str, speaker_id: int, api_key: str) -> io.BytesIO | None:
    if not api_key or api_key == "YOUR_VOICEVOX_API_KEY_PLACEHOLDER":
        print("VoiceVox API key is not configured or is a placeholder.")
        return None
    
    print(f"Attempting VoiceVox TTS. API Key used: '{api_key}', Speaker ID: {speaker_id}")
    
    params_dict = {
        "text": text_to_speak,
        "speaker": str(speaker_id),
        "key": api_key
    }
    
    print(f"Requesting VoiceVox TTS for text: '{text_to_speak[:50]}...'")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(VOICEVOX_API_BASE_URL, params=params_dict, timeout=aiohttp.ClientTimeout(total=60)) as response:
                print(f"VoiceVox API response status: {response.status}, Content-Type: {response.content_type}")

                if response.status == 200:
                    if response.content_type in ('audio/wav', 'audio/x-wav'): # Handle both
                        audio_data = await response.read()
                        print(f"VoiceVox TTS success, received {len(audio_data)} bytes of {response.content_type} data.")
                        return io.BytesIO(audio_data)
                    else: # 200 OK but unexpected content type
                        try:
                            error_text = await response.text()
                            print(f"VoiceVox API returned 200 OK but with unexpected Content-Type ({response.content_type}): {error_text[:200]}")
                        except UnicodeDecodeError: # If body is not decodable text
                            print(f"VoiceVox API returned 200 OK but with unexpected Content-Type ({response.content_type}) and non-text body.")
                        return None
                elif response.status == 403: # Forbidden
                    error_text = ""
                    try: error_text = await response.text()
                    except UnicodeDecodeError: error_text = "(Failed to decode error response as text)"
                    print(f"VoiceVox API request failed with status 403 (Forbidden).")
                    print(f"  Response Text: {error_text[:500]}")
                    return None
                else: # Other errors
                    error_text = ""
                    try: error_text = await response.text()
                    except UnicodeDecodeError: error_text = "(Failed to decode error response as text)"
                    print(f"VoiceVox API request failed with status {response.status}: {error_text[:500]}")
                    return None
    except asyncio.TimeoutError:
        print("VoiceVox API request timed out.")
        return None
    except Exception as e:
        print(f"Error during VoiceVox API call: {e}")
        traceback.print_exc()
        return None

# --- RVC Helper (extracted for reuse) ---
async def process_audio_with_rvc(ctx: commands.Context, audio_bytes_io: io.BytesIO, original_filename_base: str, input_file_extension_no_dot: str):
    """
    Processes the given audio stream with RVC.
    `input_file_extension_no_dot` should be like "wav", "mp3".
    """
    # Duration check (moved inside)
    try:
        temp_audio_stream_for_check = io.BytesIO(audio_bytes_io.getvalue()) # Create a copy for duration check
        temp_audio_stream_for_check.seek(0)
        audio_segment = AudioSegment.from_file(temp_audio_stream_for_check, format=input_file_extension_no_dot)
        duration_seconds = len(audio_segment) / 1000.0
        print(f"Audio duration for RVC: {duration_seconds:.2f} seconds")
        temp_audio_stream_for_check.close() # Close the temporary stream

        if duration_seconds > 45.0: # Max 45 seconds for RVC processing
            await ctx.send(f"エラー: 音声が長すぎます ({duration_seconds:.1f}秒)。45秒以下の音声にしてください。")
            return False # Indicate failure
    except CouldntDecodeError:
        await ctx.send("エラー: 音声ファイルの形式を認識できませんでした。有効な音声ファイルか確認してください。")
        return False
    except Exception as e_dur:
        await ctx.send(f"エラー: 音声ファイルの長さ確認中に問題が発生しました: {e_dur}")
        traceback.print_exc()
        return False
    finally: # Ensure original stream is reset if manipulated
        audio_bytes_io.seek(0) # Reset original stream for further processing

    rvc_infer_script_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    rvc_model_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    rvc_index_file_name_no_ext, _ = os.path.splitext(RVC_MODEL_NAME_WITH_EXT)
    rvc_index_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, f"{rvc_index_file_name_no_ext}.index")

    if not os.path.exists(rvc_infer_script_full_path):
        await ctx.send("エラー: RVC推論スクリプトが見つかりません。Bot管理者に連絡してください。"); return False
    if not os.path.exists(rvc_model_full_path):
        await ctx.send(f"エラー: RVCモデル '{RVC_MODEL_NAME_WITH_EXT}' が見つかりません。Bot管理者に連絡してください。"); return False

    processing_message = await ctx.send("**やまかわボイチェンの処理をしています...** \nしばらくお待ちください... (目安:20~50秒)")

    timestamp = datetime.datetime.now(JST).strftime("%Y%m%d%H%M%S%f"); unique_id = f"{ctx.author.id}_{ctx.message.id}_{timestamp}"
    input_filename_rvc = f"input_{unique_id}.{input_file_extension_no_dot}"; output_filename_rvc = f"output_{unique_id}.{input_file_extension_no_dot}"
    input_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_INPUT_AUDIO_DIR, input_filename_rvc))
    output_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_OUTPUT_AUDIO_DIR, output_filename_rvc))
    
    success_flag = False
    try:
        with open(input_filepath_abs_rvc, 'wb') as f_out:
            audio_bytes_io.seek(0) 
            f_out.write(audio_bytes_io.getbuffer())
        print(f"Saved input audio for RVC to: {input_filepath_abs_rvc}")

        effective_python_executable = sys.executable 
        print(f"RVC Python executable: {effective_python_executable}")
        command = [effective_python_executable, rvc_infer_script_full_path, 
                   "--f0up_key", str(RVC_FIXED_TRANSPOSE), 
                   "--input_path", input_filepath_abs_rvc, 
                   "--opt_path", output_filepath_abs_rvc, 
                   "--model_name", RVC_MODEL_NAME_WITH_EXT]
        if os.path.exists(rvc_index_full_path): command.extend(["--feature_path", rvc_index_full_path])
        
        print(f"Executing RVC command: {' '.join(command)}")
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=RVC_PROJECT_ROOT_PATH)
        stdout_bytes, stderr_bytes = await process.communicate()
        stdout_str = stdout_bytes.decode('utf-8', errors='ignore').strip(); stderr_str = stderr_bytes.decode('utf-8', errors='ignore').strip()
        if stdout_str: print(f"--- RVC STDOUT ---\n{stdout_str}\n------------------")
        if stderr_str: print(f"--- RVC STDERR ---\n{stderr_str}\n------------------")
        
        if process.returncode != 0:
            print(f"RVC process failed with code {process.returncode}.")
            await processing_message.edit(content=f"音声変換中にエラーが発生しました (RVCプロセス)。ログを確認してください。")
        elif os.path.exists(output_filepath_abs_rvc) and os.path.getsize(output_filepath_abs_rvc) > 0:
            await processing_message.edit(content="**やまかわてるきボイチェンの処理が完了しました**\nうまくいかない場合はBGMを抜いてみてください")
            await ctx.send(file=discord.File(output_filepath_abs_rvc, filename=f"rvc_{original_filename_base}.{input_file_extension_no_dot}"))
            success_flag = True
        else:
            await processing_message.edit(content="変換は成功しましたが、出力ファイルが見つかりませんでした。")
            print(f"RVC output file not found or empty: {output_filepath_abs_rvc}")
            
    except Exception as e:
        await processing_message.edit(content=f"予期せぬエラーが発生しました (RVC処理): {e}")
        print(f"Unexpected error in process_audio_with_rvc: {e}"); traceback.print_exc()
    finally:
        if os.path.exists(input_filepath_abs_rvc):
            try: os.remove(input_filepath_abs_rvc)
            except Exception as e_rem: print(f"Failed to delete RVC input temp file: {e_rem}")
        # Delete output only if not sent successfully or if an error occurred before sending
        if os.path.exists(output_filepath_abs_rvc):
            if not success_flag: # If not successful, try to delete
                 try: os.remove(output_filepath_abs_rvc)
                 except Exception as e_rem: print(f"Failed to delete RVC output temp file (on failure): {e_rem}")
            # Consider if successfully sent files should also be deleted after a while or immediately
            # For now, successfully sent files are kept in RVC_OUTPUT_AUDIO_DIR until manual cleanup
    return success_flag


@bot.command(name="voice")
async def rvc_voice_convert_command(ctx: commands.Context, *, text_input: str = None):
    if not ctx.message.attachments and not text_input:
        await ctx.send("音声ファイルを添付するか、変換したいテキストを入力してください。\n例: `voice こんにちはやまかわてるきです` または `voice` + 音声ファイル添付")
        return

    audio_bytes_io = None
    original_filename_base = "text_to_speech"
    input_file_extension = "wav" # Default for TTS

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not (attachment.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a'))):
            await ctx.send("添付ファイルの形式は .wav, .mp3, .flac, .m4a のいずれかにしてください。")
            return
        
        audio_bytes_io = io.BytesIO()
        await attachment.save(audio_bytes_io)
        audio_bytes_io.seek(0)
        original_filename_base, ext = os.path.splitext(attachment.filename)
        input_file_extension = ext.lstrip('.').lower()

    elif text_input:
        if not VOICEVOX_API_KEY or VOICEVOX_API_KEY == "YOUR_VOICEVOX_API_KEY_PLACEHOLDER":
            await ctx.send("エラー: VoiceVox APIキーが設定されていません。テキストからの音声変換は利用できません。")
            return
        
        async with ctx.typing():
            tts_status_msg = await ctx.send(f"「{text_input[:30]}{'...' if len(text_input)>30 else ''}」をVoiceVoxで音声生成中...")
            generated_audio_stream = await generate_voicevox_audio(text_input, VOICEVOX_SPEAKER_ID, VOICEVOX_API_KEY)
        
        if generated_audio_stream:
            audio_bytes_io = generated_audio_stream
            # audio_bytes_io.seek(0) # Already at 0 from BytesIO constructor if data passed
            await tts_status_msg.edit(content=f"VoiceVoxでの音声生成完了。RVC処理を開始します...")
        else:
            await tts_status_msg.edit(content="VoiceVoxでの音声生成に失敗しました。APIエラーか、テキストが長すぎる可能性があります。")
            return
        # input_file_extension is "wav" for TTS
    
    if audio_bytes_io and audio_bytes_io.getbuffer().nbytes > 0:
        await process_audio_with_rvc(ctx, audio_bytes_io, original_filename_base, input_file_extension)
    else:
        # This case might be hit if generated_audio_stream was None but somehow audio_bytes_io was not.
        if not (ctx.message.attachments and text_input): # Avoid double message if attachment also failed
            await ctx.send("音声データの準備に失敗しました。")
    
    if audio_bytes_io: # Always close the stream if it was opened/created
        audio_bytes_io.close()

# ================================== JANKEN COMMAND (with Buttons) ==================================
class JankenChoiceView(discord.ui.View):
    def __init__(self, host_id: int, game_message_id: int):
        super().__init__(timeout=JANKEN_TIMEOUT_HOST_CHOICE_SECONDS) # ★修正: _SECONDS を使用
        self.host_id = host_id
        self.game_message_id = game_message_id
        self.host_choice = None

    async def on_timeout(self):
        if self.game_message_id in active_janken_games and active_janken_games[self.game_message_id]["game_status"] == "host_choosing":
            game_data = active_janken_games[self.game_message_id]
            embed_timeout = discord.Embed(title="じゃんけん", description="ホストが手を選ばなかったため、じゃんけんはキャンセルされました。", color=discord.Color.orange())
            try:
                await game_data["message"].edit(embed=embed_timeout, view=None)
            except discord.HTTPException:
                pass # Message might have been deleted
            del active_janken_games[self.game_message_id]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("じゃんけんの開始者のみが手を選べます。", ephemeral=True)
            return False
        return True

    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        self.host_choice = choice
        self.stop() # Stop listening for further interactions on this view

        if self.game_message_id not in active_janken_games: # Game might have been cancelled/timed out
             return await interaction.response.edit_message(content="このじゃんけんゲームは既に終了またはキャンセルされています。", embed=None, view=None)


        game_data = active_janken_games[self.game_message_id]
        game_data["host_hand"] = self.host_choice
        game_data["game_status"] = "opponent_recruiting"

        embed_opponent_recruit = discord.Embed(
            title="じゃんけん",
            description=f"{interaction.user.mention} が手を選びました！\n対戦相手を募集中です。\n参加する人は下のリアクションで手を選んでください。",
            color=discord.Color.green()
        )
        # Edit the original message to show opponent recruiting phase and add reaction emojis
        try:
            await game_data["message"].edit(embed=embed_opponent_recruit, view=None) # Remove buttons
            await game_data["message"].clear_reactions() # Clear any previous reactions
            for emoji in HAND_EMOJIS.values():
                await game_data["message"].add_reaction(emoji)
        except discord.HTTPException as e:
            print(f"Error updating Janken message for opponent recruiting: {e}")
            # Potentially delete game data if message update fails critically
            if self.game_message_id in active_janken_games:
                del active_janken_games[self.game_message_id]
            return

    @discord.ui.button(label="グー", style=discord.ButtonStyle.primary, emoji="✊")
    async def rock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer() # Acknowledge interaction immediately
        await self.handle_choice(interaction, "rock")

    @discord.ui.button(label="チョキ", style=discord.ButtonStyle.primary, emoji="✌️")
    async def scissors_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.handle_choice(interaction, "scissors")

    @discord.ui.button(label="パー", style=discord.ButtonStyle.primary, emoji="✋")
    async def paper_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.handle_choice(interaction, "paper")

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.stop()
        if self.game_message_id in active_janken_games:
            game_data = active_janken_games[self.game_message_id]
            embed_cancel = discord.Embed(title="じゃんけん", description="じゃんけんはホストによってキャンセルされました。", color=discord.Color.red())
            try:
                await game_data["message"].edit(embed=embed_cancel, view=None)
            except discord.HTTPException:
                pass
            del active_janken_games[self.game_message_id]

def determine_janken_winner(host_hand: str, opponent_hand: str) -> tuple[str, int, int]:
    # ... (determine_janken_winner unchanged) ...
    win_conditions = {
        ("rock", "scissors"): "host",
        ("scissors", "paper"): "host",
        ("paper", "rock"): "host",
    }
    if host_hand == opponent_hand:
        return "引き分け！ポイント変動なし。", 0, 0
    
    if (host_hand, opponent_hand) in win_conditions: # Host wins
        result_text = f"{HAND_EMOJIS[host_hand]} を出したホストの勝ち！"
        return result_text, JANKEN_WIN_POINTS, JANKEN_LOSE_POINTS
    else: # Opponent wins
        result_text = f"{HAND_EMOJIS[opponent_hand]} を出した相手の勝ち！"
        return result_text, JANKEN_LOSE_POINTS, JANKEN_WIN_POINTS

@bot.command(name="janken")
async def janken_command(ctx: commands.Context):
    host_id = ctx.author.id
    # 「あなたは既に進行中のじゃんけんがあります。」のチェックを削除
    # if any(game.get("host_id") == host_id and game.get("game_status") != "finished" for game in active_janken_games.values()):
    #     await ctx.send("あなたは既に進行中のじゃんけんがあります。")
    #     return

    embed_host_choose = discord.Embed(
        title="じゃんけん",
        description=f"{ctx.author.mention} じゃんけんを開始しました。\nまずあなたが出す手を下のボタンで選んでください。",
        color=discord.Color.blue()
    )
    
    view = JankenChoiceView(host_id, 0) 
    game_message = await ctx.send(embed=embed_host_choose, view=view)
    view.game_message_id = game_message.id 

    active_janken_games[game_message.id] = {
        "host_id": host_id, "host_hand": None,
        "opponent_id": None, "opponent_hand": None,
        "channel_id": ctx.channel.id, "message": game_message,
        "game_status": "host_choosing"
    }

# ================================== TEXT IMAGE DRAWING HELPER ==================================
# 描画順: 奥から手前へ (白縁 -> 黒縁 -> 黄色文字)
# 黄色文字→黒縁(17px)→白縁(12px) の指示は、
# 1. 文字の周りに17pxの黒縁
# 2. その黒縁の周りに12pxの白縁
# という意味なので、文字の中心から見ると、
# - 黒縁の端までは 17px
# - 白縁の端までは 17px + 12px = 29px
def draw_text_layered_outline(draw, base_pos, char_text, font, 
                              text_color,           # 黄色 (本体)
                              inner_outline_color,  # 黒色 (内側の縁)
                              inner_outline_radius, # 黒縁の半径 (文字の中心から黒縁の端まで)
                              outer_outline_color,  # 白色 (外側の縁)
                              outer_outline_radius): # 白縁の半径 (文字の中心から白縁の端まで)
    x, y = base_pos
    
    # Layer 1: Outermost outline (e.g., White)
    # outer_outline_radius は文字の中心からこの縁の最も外側までの距離
    for dx_outer in range(-outer_outline_radius, outer_outline_radius + 1):
        for dy_outer in range(-outer_outline_radius, outer_outline_radius + 1):
            if dx_outer*dx_outer + dy_outer*dy_outer <= outer_outline_radius*outer_outline_radius :
                 draw.text((x + dx_outer, y + dy_outer), char_text, font=font, fill=outer_outline_color)
    
    # Layer 2: Middle outline (e.g., Black)
    # inner_outline_radius は文字の中心からこの縁の最も外側までの距離
    for dx_inner in range(-inner_outline_radius, inner_outline_radius + 1):
        for dy_inner in range(-inner_outline_radius, inner_outline_radius + 1):
            if dx_inner*dx_inner + dy_inner*dy_inner <= inner_outline_radius*inner_outline_radius:
                draw.text((x + dx_inner, y + dy_inner), char_text, font=font, fill=inner_outline_color)
    
    # Layer 3: Main text
    draw.text((x, y), char_text, font=font, fill=text_color)

# ================================== TEXT IMAGE COMMAND ==================================
@bot.command(name="text")
async def text_image_command(ctx: commands.Context, *, args: str):
    if not args: await ctx.send("画像にするテキストを指定してください。"); return
    make_square = False
    text_to_render = args.strip()
    if text_to_render.lower().endswith(" square"):
        text_to_render = text_to_render[:-7].strip(); make_square = True
    if not text_to_render: await ctx.send("画像にするテキスト内容が空です。"); return
    if not os.path.exists(TEXT_IMAGE_FONT_PATH): await ctx.send(f"エラー: フォントファイルが見つかりません。"); return

    try:
        async with ctx.typing():
            font = ImageFont.truetype(TEXT_IMAGE_FONT_PATH, TEXT_IMAGE_FONT_SIZE)
            
            lines_input = text_to_render.split(',')
            max_text_content_width = 0; current_y_for_layout = 0; line_layout_data = []
            letter_spacing_abs = int(TEXT_IMAGE_FONT_SIZE * TEXT_IMAGE_LETTER_SPACING_ADJUST)
            dummy_draw = ImageDraw.Draw(Image.new("L",(1,1)))
            try: ascent, descent = font.getmetrics(); font_standard_height = ascent + descent
            except AttributeError: font_standard_height = TEXT_IMAGE_FONT_SIZE

            for line_text in lines_input:
                current_line_chars_info = []; line_actual_width = 0; max_char_actual_height_in_line = 0
                if not line_text.strip():
                    max_char_actual_height_in_line = font_standard_height
                    current_line_chars_info.append({'width': 0, 'height': font_standard_height})
                else:
                    for i, char_s in enumerate(line_text):
                        char_bbox = dummy_draw.textbbox((0,0), char_s, font=font)
                        char_w = char_bbox[2] - char_bbox[0]; char_h = char_bbox[3] - char_bbox[1]
                        current_line_chars_info.append({'width': char_w, 'height': char_h})
                        line_actual_width += char_w
                        if i < len(line_text) - 1: line_actual_width += letter_spacing_abs
                        max_char_actual_height_in_line = max(max_char_actual_height_in_line, char_h)
                line_height_for_next = int(max_char_actual_height_in_line * TEXT_IMAGE_LINE_HEIGHT_MULTIPLIER) \
                                        if max_char_actual_height_in_line > 0 \
                                        else int(font_standard_height * TEXT_IMAGE_LINE_HEIGHT_MULTIPLIER)
                line_layout_data.append({
                    "text": line_text, "chars_info": current_line_chars_info,
                    "render_width": line_actual_width, "y_start_in_block": current_y_for_layout,
                    "height_for_next_line": line_height_for_next})
                max_text_content_width = max(max_text_content_width, line_actual_width)
                current_y_for_layout += line_height_for_next
            total_text_content_height = current_y_for_layout
            if max_text_content_width <= 0 or total_text_content_height <= 0:
                await ctx.send("エラー: テキスト内容から有効なサイズを計算できませんでした。"); return

            # 一時キャンバスのサイズ計算
            # MaxFilterの繰り返し回数に基づく総半径
            outline_total_radius_approx = TEXT_IMAGE_OUTLINE_THICKNESS_BLACK + TEXT_IMAGE_OUTLINE_THICKNESS_WHITE
            temp_canvas_margin = outline_total_radius_approx + TEXT_MASK_ADDITIONAL_MARGIN
            temp_canvas_width = int(max_text_content_width + temp_canvas_margin * 2)
            temp_canvas_height = int(total_text_content_height + temp_canvas_margin * 2)
            
            text_mask_on_temp_canvas = Image.new('L', (temp_canvas_width, temp_canvas_height), 0)
            text_mask_draw_temp = ImageDraw.Draw(text_mask_on_temp_canvas)
            text_block_start_x_on_mask = temp_canvas_margin
            text_block_start_y_on_mask = temp_canvas_margin
            for line_data in line_layout_data:
                line_str = line_data["text"]
                current_x_char_draw = text_block_start_x_on_mask + (max_text_content_width - line_data["render_width"]) / 2.0
                draw_y_char = text_block_start_y_on_mask + line_data["y_start_in_block"]
                if not line_str.strip() and not line_str: continue
                for i, char_info in enumerate(line_data["chars_info"]):
                    if i < len(line_str):
                        char_single = line_str[i]
                        text_mask_draw_temp.text((current_x_char_draw, draw_y_char), char_single, font=font, fill=255)
                        current_x_char_draw += char_info['width'] + letter_spacing_abs
            
            # text_mask_on_temp_canvas.save("debug_0_text_mask.png")

            # 縁取りレイヤーの作成とクロップ
            # 白縁: 黒縁回数 + 白縁回数 Filter
            # 黒縁: 黒縁回数 Filter
            
            # 白縁用マスク
            thickness_for_white_layer = TEXT_IMAGE_OUTLINE_THICKNESS_BLACK + TEXT_IMAGE_OUTLINE_THICKNESS_WHITE
            dilated_mask_w = text_mask_on_temp_canvas.copy()
            if thickness_for_white_layer > 0:
                for _ in range(thickness_for_white_layer):
                    dilated_mask_w = dilated_mask_w.filter(ImageFilter.MaxFilter(3))
            bbox_w = dilated_mask_w.getbbox()
            cropped_white_layer = dilated_mask_w.crop(bbox_w) if bbox_w else None
            # if cropped_white_layer: cropped_white_layer.save("debug_1_cropped_white.png")

            # 黒縁用マスク
            thickness_for_black_layer = TEXT_IMAGE_OUTLINE_THICKNESS_BLACK
            dilated_mask_b = text_mask_on_temp_canvas.copy()
            if thickness_for_black_layer > 0:
                for _ in range(thickness_for_black_layer):
                    dilated_mask_b = dilated_mask_b.filter(ImageFilter.MaxFilter(3))
            bbox_b = dilated_mask_b.getbbox()
            cropped_black_layer = dilated_mask_b.crop(bbox_b) if bbox_b else None
            # if cropped_black_layer: cropped_black_layer.save("debug_2_cropped_black.png")

            # 文字本体用マスク
            bbox_t = text_mask_on_temp_canvas.getbbox()
            cropped_text_layer = text_mask_on_temp_canvas.crop(bbox_t) if bbox_t else None
            # if cropped_text_layer: cropped_text_layer.save("debug_3_cropped_text.png")

            # 最終画像のサイズ決定
            if cropped_white_layer: # 最も外側の縁を基準
                content_final_width = cropped_white_layer.width
                content_final_height = cropped_white_layer.height
            elif cropped_black_layer:
                content_final_width = cropped_black_layer.width
                content_final_height = cropped_black_layer.height
            elif cropped_text_layer:
                content_final_width = cropped_text_layer.width
                content_final_height = cropped_text_layer.height
            else:
                await ctx.send("エラー: 描画コンテンツ生成不可。"); return

            final_img_width = content_final_width + TEXT_IMAGE_PADDING * 2
            final_img_height = content_final_height + TEXT_IMAGE_PADDING * 2
            final_image_canvas = Image.new("RGBA", (final_img_width, final_img_height), (0,0,0,0))

            # 各クロップ済みレイヤーを最終画像の中央にペースト
            y_paste_offset_global = TEXT_IMAGE_VERTICAL_OFFSET
            if cropped_white_layer:
                paste_x = (final_img_width - cropped_white_layer.width) // 2
                paste_y = (final_img_height - cropped_white_layer.height) // 2 + y_paste_offset_global
                final_image_canvas.paste(TEXT_IMAGE_OUTLINE_COLOR_WHITE, (paste_x, paste_y), cropped_white_layer)
            if cropped_black_layer:
                paste_x = (final_img_width - cropped_black_layer.width) // 2
                paste_y = (final_img_height - cropped_black_layer.height) // 2 + y_paste_offset_global
                final_image_canvas.paste(TEXT_IMAGE_OUTLINE_COLOR_BLACK, (paste_x, paste_y), cropped_black_layer)
            if cropped_text_layer:
                paste_x = (final_img_width - cropped_text_layer.width) // 2
                paste_y = (final_img_height - cropped_text_layer.height) // 2 + y_paste_offset_global
                final_image_canvas.paste(TEXT_IMAGE_TEXT_COLOR, (paste_x, paste_y), cropped_text_layer)

            # Squareモード処理
            output_image = final_image_canvas # デフォルトは加工前の画像
            if make_square:
                # 現在の final_image_canvas からコンテンツ部分を正確に切り出す
                alpha_channel = final_image_canvas.getchannel('A')
                content_actual_bbox = alpha_channel.getbbox()

                if content_actual_bbox:
                    cropped_for_square = final_image_canvas.crop(content_actual_bbox)
                    # クロップされたコンテンツの幅と高さのうち、大きい方を基準に正方形化
                    target_dimension = max(cropped_for_square.width, cropped_for_square.height)
                    if target_dimension > 0:
                        # 新しい正方形の透明なキャンバスを作成
                        square_canvas = Image.new("RGBA", (target_dimension, target_dimension), (0,0,0,0))
                        # クロップしたコンテンツを、この正方形キャンバスに合わせてリサイズ（アスペクト比無視）
                        stretched_content = cropped_for_square.resize((target_dimension, target_dimension), Image.Resampling.LANCZOS)
                        # 正方形キャンバスにペースト（中央揃えは不要、(0,0)でOK）
                        square_canvas.paste(stretched_content, (0,0))
                        output_image = square_canvas # 出力画像をこの正方形画像に置き換え
                    else:
                        print("Warning (square): Cropped content for square had zero dimension.")
                else:
                    print("Warning (square): No content bbox found in final_image_canvas for squaring.")
            
            # 保存と送信
            img_byte_arr = io.BytesIO()
            output_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            # output_image.save("debug_final_output_for_send.png")

            final_image_io_resized, resized_flag = await _resize_image_if_too_large(img_byte_arr, "PNG", MAX_FILE_SIZE_BYTES)
            # ... (以降の送信処理は同じ)
            if final_image_io_resized is None:
                await ctx.send("エラー: 画像の最終処理に失敗しました。"); img_byte_arr.close(); return
            final_image_io_resized.seek(0, io.SEEK_END); final_size = final_image_io_resized.tell(); final_image_io_resized.seek(0)
            if final_size > MAX_FILE_SIZE_BYTES:
                await ctx.send(f"生成された画像サイズが大きすぎます ({final_size/(1024*1024):.2f}MB)。"); final_image_io_resized.close(); return
            await ctx.send(file=discord.File(fp=final_image_io_resized, filename="text_image.png"))
            if img_byte_arr != final_image_io_resized and not img_byte_arr.closed: img_byte_arr.close()
            if final_image_io_resized and not final_image_io_resized.closed: final_image_io_resized.close()

    except Exception as e:
        await ctx.send(f"テキスト画像生成中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc()

# Weather command with Yahoo API - YAHOO_CLIENT_ID の参照を確認
@bot.command(name="tenki", aliases=["weather"])
async def weather_command_yolp(ctx: commands.Context, *, place_name: str):
    # YAHOO_CLIENT_ID はグローバルスコープから参照される
    if not YAHOO_CLIENT_ID or YAHOO_CLIENT_ID == "YOUR_YAHOO_CLIENT_ID_PLACEHOLDER":
        await ctx.send("エラー: 天気APIのCLIENT IDが設定されていません。管理者に連絡してください。")
        return
    # ... (rest of the YOLP weather command) ...
    async with ctx.typing():
        if GEMINI_API_UNAVAILABLE:
            await ctx.send("地名からの座標取得に失敗しました (Gemini API利用不可)。")
            return

        coord_prompt = f"「{place_name}」の代表的な緯度と経度を、カンマ区切りで小数点以下6桁程度で教えてください。例: 35.6895,139.6917"
        coord_response_str = await generate_gemini_text_response([coord_prompt])

        if coord_response_str.startswith("Error:") or not coord_response_str:
            await ctx.send(f"「{place_name}」の座標取得に失敗しました。Geminiからの応答: {coord_response_str}")
            return

        try:
            lat_str, lon_str = coord_response_str.strip().split(',')
            latitude = float(lat_str.strip())
            longitude = float(lon_str.strip())
        except ValueError:
            await ctx.send(f"座標の解析に失敗しました。Geminiからの応答「{coord_response_str}」が不正な形式です。地名をより具体的にしてみてください。")
            return
        
        print(f"Weather YOLP: Coordinates for '{place_name}' -> Lat: {latitude}, Lon: {longitude}")

        params = {
            "appid": YAHOO_CLIENT_ID, # グローバル変数を直接使用
            "coordinates": f"{longitude},{latitude}", 
            "output": "json",
            "interval": "5" 
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(YAHOO_WEATHER_API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "Feature" not in data or not data["Feature"] or \
                           "Property" not in data["Feature"][0] or \
                           "WeatherList" not in data["Feature"][0]["Property"] or \
                           "Weather" not in data["Feature"][0]["Property"]["WeatherList"] or \
                           not data["Feature"][0]["Property"]["WeatherList"]["Weather"]:
                            await ctx.send(f"「{place_name}」({latitude:.4f},{longitude:.4f})の天気情報が見つかりませんでした。APIからの詳細情報なし。")
                            return

                        weather_info_list = data["Feature"][0]["Property"]["WeatherList"]["Weather"]
                        
                        embed = discord.Embed(title=f"{place_name} の天気情報 (Yahoo!)", color=discord.Color.blue())
                        embed.description = f"緯度: {latitude:.4f}, 経度: {longitude:.4f}"
                        embed.set_footer(text="情報源: Yahoo! Open Local Platform")
                        
                        forecasts_to_show = min(len(weather_info_list), 5) # 最大5件表示

                        for i in range(forecasts_to_show):
                            forecast = weather_info_list[i]
                            fc_time_str = forecast.get("Date", "時刻不明") 
                            fc_type = forecast.get("Type", "不明") 
                            fc_rainfall = forecast.get("Rainfall", 0.0) 

                            try:
                                fc_dt_obj = datetime.datetime.strptime(fc_time_str, "%Y%m%d%H%M").replace(tzinfo=JST) # JSTとして解釈
                                fc_time_display = f"<t:{int(fc_dt_obj.timestamp())}:t>" # Discord Timestamp (Time)
                            except ValueError:
                                fc_time_display = fc_time_str
                            
                            weather_status_jp = "観測実況" if fc_type == "observation" else "予報"
                            
                            field_name = f"{fc_time_display} ({weather_status_jp})"
                            field_value = f"降水量: **{fc_rainfall:.2f} mm/h**"
                            embed.add_field(name=field_name, value=field_value, inline=True if forecasts_to_show > 1 else False)

                        await ctx.send(embed=embed)

                    elif response.status == 403: 
                        error_data_text = await response.text()
                        print(f"Yahoo Weather API Error 403: {error_data_text[:300]}")
                        await ctx.send(f"天気APIへのアクセスが拒否されました。アプリケーションIDまたはAPI側の制限を確認してください。")
                    else:
                        error_data_text = await response.text()
                        print(f"Yahoo Weather API Error {response.status}: {error_data_text[:300]}")
                        await ctx.send(f"天気情報の取得に失敗 (HTTP: {response.status})。")
        except Exception as e:
            await ctx.send(f"天気情報取得中に予期せぬエラー: {e}")
            traceback.print_exc()

@weather_command_yolp.error
async def weather_command_yolp_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"地名を指定してください。例: `tenki 東京都千代田区` (`{error.param.name}` がありません)")
    else: await ctx.send(f"天気コマンド(YOLP)でエラー: {error}")

@bot.command(name="info")
async def user_info_command(ctx: commands.Context, member: discord.Member = None):
    target_member = member or ctx.author
    embed = discord.Embed(title=f"{target_member.display_name}", color=target_member.color or discord.Color.default())
    if target_member.avatar: embed.set_thumbnail(url=target_member.avatar.url)
    
    embed.add_field(name="ユーザー名", value=f"`{target_member.name}`", inline=True)
    embed.add_field(name="ユーザーID", value=f"`{target_member.id}`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

    created_at_jst = target_member.created_at.astimezone(JST)
    embed.add_field(name="アカウント作成日", value=f"<t:{int(target_member.created_at.timestamp())}:D>", inline=True) # Discord Timestamp
    
    if isinstance(target_member, discord.Member) and target_member.joined_at:
        # joined_at_jst = target_member.joined_at.astimezone(JST)
        # embed.add_field(name="サーバー参加日", value=f"{joined_at_jst.strftime('%Y年%m月%d日')}\n({(datetime.datetime.now(JST) - joined_at_jst).days }日前)", inline=True)
        embed.add_field(name="サーバー参加日", value=f"<t:{int(target_member.joined_at.timestamp())}:R>", inline=True) # Relative Timestamp
    else:
        embed.add_field(name="サーバー参加日", value="N/A", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer
    
    if isinstance(target_member, discord.Member) and target_member.premium_since:
        # boost_since_jst = target_member.premium_since.astimezone(JST)
        # boost_duration = (datetime.datetime.now(JST) - boost_since_jst).days
        # embed.add_field(name="ブースト開始日", value=f"{boost_since_jst.strftime('%Y年%m月%d日')} ({boost_duration}日前)", inline=True)
        embed.add_field(name="ブースト開始日", value=f"<t:{int(target_member.premium_since.timestamp())}:R>", inline=True)
    else:
        embed.add_field(name="ブースト開始日", value="なし", inline=True)
    
    badges = []
    flags = target_member.public_flags
    # Using a dictionary for cleaner badge addition
    badge_map = {
        "staff": flags.staff, "partner": flags.partner,
        "hypesquad_bravery": flags.hypesquad_bravery, "hypesquad_brilliance": flags.hypesquad_brilliance,
        "hypesquad_balance": flags.hypesquad_balance, "bug_hunter": flags.bug_hunter,
        "bug_hunter_level_2": flags.bug_hunter_level_2, "early_supporter": flags.early_supporter,
        "verified_bot": (target_member.bot and flags.verified_bot),
        "early_verified_bot_developer": flags.early_verified_bot_developer,
        "discord_certified_moderator": flags.discord_certified_moderator,
        "active_developer": flags.active_developer,
        "nitro": (isinstance(target_member, discord.Member) and target_member.premium_since) # Nitro/Booster is via premium_since
    }
    for badge_name, has_badge in badge_map.items():
        if has_badge:
            emoji = USER_BADGES_EMOJI.get(badge_name)
            if emoji: badges.append(emoji)
            # else: badges.append(f"[{badge_name.upper()}]") # Fallback if emoji missing

    if badges: embed.add_field(name="バッジ", value=" ".join(badges) or "なし", inline=True)
    else: embed.add_field(name="バッジ", value="なし", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

    if isinstance(target_member, discord.Member):
        roles = [role.mention for role in sorted(target_member.roles, key=lambda r: r.position, reverse=True) if role.name != "@everyone"]
        if roles:
            roles_str = " ".join(roles)
            if len(roles_str) > 1000: roles_str = roles_str[:997] + "..." # Limit length
            embed.add_field(name=f"ロール ({len(roles)})", value=roles_str or "なし", inline=False)
        else:
            embed.add_field(name="ロール", value="なし", inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name="rate")
async def exchange_rate_command(ctx: commands.Context, amount_str: str, currency_code: str):
    try:
        amount = float(amount_str)
    except ValueError:
        await ctx.send("金額は有効な数値で入力してください。例: `rate 100 USD`")
        return

    currency_code_input = currency_code.upper()
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(EXCHANGE_RATE_API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        target_rate_key = f"{currency_code_input}_JPY" # API specific key
                        if target_rate_key in data and isinstance(data[target_rate_key], (int, float)):
                            rate_val = data[target_rate_key]
                            amount_in_jpy = amount * rate_val
                            
                            api_time_utc_str = data.get('datetime', '')
                            time_str_jst = api_time_utc_str # Default
                            try:
                                # Assuming API returns ISO format string like "2023-10-27T10:00:00.000Z"
                                api_time_utc = datetime.datetime.fromisoformat(api_time_utc_str.replace("Z", "+00:00"))
                                api_time_jst = api_time_utc.astimezone(JST)
                                time_str_jst = api_time_jst.strftime('%Y-%m-%d %H:%M:%S') + " JST"
                            except ValueError: # If fromisoformat fails
                                print(f"Could not parse exchange rate API time: {api_time_utc_str}")
                            
                            await ctx.send(f"{amount:,.2f} {currency_code_input} → **{amount_in_jpy:,.2f} 円**\n(1 {currency_code_input} = {rate_val:,.3f} JPY, {time_str_jst}時点)")
                        else:
                            available_currencies = sorted([key.split('_')[0] for key in data.keys() if key.endswith("_JPY") and isinstance(data[key], (int,float))])
                            await ctx.send(f"通貨「{currency_code_input}」の対日本円レートが見つかりません。\n利用可能 (対JPY): ` {', '.join(available_currencies[:15])}{' ...' if len(available_currencies) > 15 else ''} `")
                    else: await ctx.send(f"為替レートAPIアクセス失敗 (HTTP: {response.status})")
        except Exception as e: await ctx.send(f"為替レート変換エラー: {e}"); traceback.print_exc()

@exchange_rate_command.error
async def exchange_rate_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"引数が不足しています。例: `rate 100 USD` (`{error.param.name}` がありません)")
    elif isinstance(error, commands.BadArgument): # This might not be hit if type hint is float
        await ctx.send(f"引数の形式が正しくありません。金額は数値で、通貨コードは3文字で入力してください。")
    else: await ctx.send(f"rateコマンドでエラー: {error}")

@bot.command(name="shorturl", aliases=["short"])
async def shorturl_command(ctx: commands.Context, *, url_to_shorten: str): # Use * to capture full URL
    if not (url_to_shorten.startswith("http://") or url_to_shorten.startswith("https://")):
        url_to_shorten = "http://" + url_to_shorten
    
    params = {"url": url_to_shorten}
    if SHORTURL_API_KEY and SHORTURL_API_KEY != "YOUR_XGD_API_KEY_PLACEHOLDER":
        params["key"] = SHORTURL_API_KEY
    
    # Use POST for x.gd API if key is provided, as per some docs, otherwise GET
    # For simplicity, sticking to GET as it often works for public shortening.
    # If API requires POST with key:
    # headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    # async with session.post(SHORTURL_API_ENDPOINT, data=params, headers=headers) as response:
    
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
                                await ctx.send(f"短縮URL: <{data['shorturl']}>") # Enclose in <> to prevent embed
                            elif isinstance(data, dict) and "message" in data :
                                await ctx.send(f"URL短縮に失敗しました (API Status: {data.get('status', response.status)}): `{data['message']}`")
                            else: # API might return plain text URL on success without API key
                                if response_content_text.startswith("https://x.gd/") or response_content_text.startswith("http://x.gd/"):
                                    await ctx.send(f"短縮URL: <{response_content_text}>")
                                else: await ctx.send(f"URL短縮で予期しない応答がありました。応答: `{response_content_text}`")
                        except json.JSONDecodeError: # If response is not JSON but plain URL
                             if response_content_text.startswith("https://x.gd/") or response_content_text.startswith("http://x.gd/"):
                                await ctx.send(f"短縮URL: <{response_content_text}>")
                             else: await ctx.send(f"URL短縮に失敗しました。APIからの応答がJSONでもURL形式でもありません: `{response_content_text}`")
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
    line3 = "￣" + ("Y^" * (arrow_count // 2)) + ("Y" if arrow_count % 2 != 0 else "") + ("^Y" * (arrow_count//2)) + "￣" # Improved Y^ pattern
    if arrow_count == 3: line3 = "￣Y^Y^Y￣" # Special case for 3
    elif arrow_count == 4: line3 = "￣Y^Y^^Y￣" # Make it look a bit better

    result = f"{line1}\n{line2}\n{line3}"
    await ctx.send(result)

@totusi_command.error
async def totusi_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"文字列を指定してください。例: `totusi あいうえお` (`{error.param.name}` がありません)")
    else: await ctx.send(f"totusiコマンドでエラー: {error}")

@bot.command(name="time")
async def time_command(ctx: commands.Context, country_code_or_help: str = None):
    if country_code_or_help and country_code_or_help.lower() == "help":
        help_text_lines = ["利用可能な国/地域コード (一部):"]
        sorted_timezones = sorted(TIMEZONE_MAP.items())
        for code, tz_name_full in sorted_timezones:
             # Extract city/region name, replace underscores
            tz_display_name = tz_name_full.split('/')[-1].replace('_', ' ')
            help_text_lines.append(f"`{code}`: {tz_display_name}")
        
        # Paginate if too long (Discord embed description limit is 4096)
        embed_description = "\n".join(help_text_lines)
        if len(embed_description) > 4000 : 
            # Simple split for now, could be more sophisticated pagination
            parts = []
            current_part = ""
            for line in help_text_lines:
                if len(current_part) + len(line) +1 > 4000:
                    parts.append(current_part)
                    current_part = line
                else:
                    if current_part: current_part += "\n"
                    current_part += line
            if current_part: parts.append(current_part)

            for i, part_desc in enumerate(parts):
                embed = discord.Embed(title=f"Timeコマンド ヘルプ ({i+1}/{len(parts)})", description=part_desc, color=discord.Color.blue())
                await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(title="Timeコマンド ヘルプ", description=embed_description, color=discord.Color.blue())
            return await ctx.send(embed=embed)


    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_jst = now_utc.astimezone(JST)

    if not country_code_or_help: # No argument, show JST
        return await ctx.send(f"{now_jst.strftime('%Y-%m-%d %H時%M分%S.%f')[:-3]}秒 (日本時間)")

    target_tz_name_str = TIMEZONE_MAP.get(country_code_or_help.upper())
    if not target_tz_name_str:
        valid_codes = ", ".join(list(TIMEZONE_MAP.keys())[:15]) + ("..." if len(TIMEZONE_MAP) > 15 else "")
        return await ctx.send(f"国コード「{country_code_or_help}」は無効です。\n利用可能な国コード: {valid_codes}\n詳細は `time help` を参照してください。")

    try:
        target_timezone = pytz.timezone(target_tz_name_str)
        target_dt = now_utc.astimezone(target_timezone)
        offset = target_dt.utcoffset()
        offset_hours = offset.total_seconds() / 3600
        offset_str = f"UTC{offset_hours:+g}" # Use g for cleaner output (e.g., +5.5 not +5.5000)
        
        tz_display_name_info = target_tz_name_str.split('/')[-1].replace('_', ' ')
        await ctx.send(f"{tz_display_name_info} の現在時刻: {target_dt.strftime('%Y-%m-%d %H時%M分%S.%f')[:-3]}秒 ({offset_str})")

    except pytz.exceptions.UnknownTimeZoneError:
        await ctx.send(f"指定されたタイムゾーン名「{target_tz_name_str}」は内部ライブラリで無効です。")
    except Exception as e:
        await ctx.send(f"時刻の取得中にエラーが発生しました: {e}")


@bot.command(name="amazon")
async def amazon_shorturl_command(ctx: commands.Context, *, amazon_url: str):
    if not amazon_url:
        return await ctx.send("AmazonのURLを指定してください。")
    
    # Basic URL validation (scheme and common Amazon domains)
    parsed_url = urllib.parse.urlparse(amazon_url)
    if not (parsed_url.scheme in ["http", "https"] and \
            any(domain in parsed_url.netloc for domain in ["amazon.co.jp", "amzn.asia", "amazon.com"])):
        return await ctx.send("有効なAmazonのURLを指定してください。 (例: https://www.amazon.co.jp/...)")

    # Marketplace ID: 6 for .co.jp, 1 for .com. Adjust if needed.
    marketplace_id = "6" if "amazon.co.jp" in parsed_url.netloc else "1"
    
    params = { "longUrl": urllib.parse.quote_plus(amazon_url), "marketplaceId": marketplace_id }
    target_url = f"{AMAZON_SHORTURL_ENDPOINT}?{urllib.parse.urlencode(params, safe='/:')}"
    
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" }
                async with session.get(target_url, headers=headers) as response:
                    print(f"Amazon ShortURL API request to: {target_url}") 
                    response_text = await response.text()
                    print(f"Amazon ShortURL API response status: {response.status}, content: {response_text[:200]}")

                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                            if data.get("isOk") is True and data.get("shortUrl"):
                                await ctx.send(f"Amazon短縮URL: <{data['shortUrl']}>") # Enclose to prevent embed
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


@bot.command(name="bet")
async def bet_command(ctx: commands.Context, amount_str: str):
    try:
        amount = int(amount_str)
    except ValueError:
        await ctx.send("賭け金は整数で指定してください。")
        return

    player_id = ctx.author.id
    current_points = get_player_points(player_id)

    if amount <= 0:
        await ctx.send("賭け金は1ポイント以上で指定してください。")
        return
    if current_points < amount:
        await ctx.send(f"ポイントが不足しています。現在のポイント: {current_points}pt")
        return
    
    async with ctx.typing():
        await asyncio.sleep(random.uniform(0.5, 1.5)) 
        
        dice_roll = random.randint(1, 6)
        message, payout_multiplier = BET_DICE_PAYOUTS[dice_roll]
        
        points_change = int(amount * payout_multiplier)
        update_player_points(player_id, points_change)
        
        new_total_points = get_player_points(player_id)

        embed = discord.Embed(title="ダイスベット(賭け)", color=discord.Color.random())
        embed.description = f"{ctx.author.mention} が {amount}pt をベット！"
        embed.add_field(name="結果", value=f"出た目: **{dice_roll}**\n{message}", inline=False)
        embed.add_field(name="ポイント変動", value=f"{'+' if points_change >=0 else ''}{points_change}pt", inline=True)
        embed.add_field(name="現在のポイント", value=f"{new_total_points}pt", inline=True) # Changed from "残り"
        
        await ctx.send(embed=embed)

@bet_command.error
async def bet_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"賭け金を指定してください。例: `bet 10` (`{error.param.name}` がありません)")
    elif isinstance(error, commands.BadArgument): # Will be hit if int() fails
        await ctx.send("賭け金は整数で指定してください。")
    else:
        await ctx.send(f"betコマンドでエラーが発生しました: {error}")
        traceback.print_exc()

# ================================== BOT EXECUTION ====================================
if __name__ == "__main__":
    # ... (Startup checks for tokens, API keys, font file, etc. unchanged) ...
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_PLACEHOLDER" or not DISCORD_BOT_TOKEN:
        print("CRITICAL ERROR: DISCORD_BOT_TOKEN is not set or is a placeholder in .env"); exit(1)
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_PLACEHOLDER" or not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY is not set. Gemini features will be unavailable.")
    if not YAHOO_CLIENT_ID or YAHOO_CLIENT_ID == "YOUR_YAHOO_CLIENT_ID_PLACEHOLDER":
        print("WARNING: YAHOO_CLIENT_ID is not set. Weather command (YOLP) will be unavailable.")
    if not VOICEVOX_API_KEY or VOICEVOX_API_KEY == "YOUR_VOICEVOX_API_KEY_PLACEHOLDER":
        print("WARNING: VOICEVOX_API_KEY is not set. Text-to-speech for 'voice' command will be unavailable.")
    # ... (other optional API key checks)

    missing_deps = [] # ... (dependency checks unchanged)
    try: import numpy
    except ImportError: missing_deps.append("numpy")
    try: from PIL import Image, ImageDraw, ImageFont, ImageFilter # Ensure all PIL components are checked
    except ImportError: missing_deps.append("Pillow (ensure ImageDraw, ImageFont, ImageFilter are available)")
    try: import pytz
    except ImportError: missing_deps.append("pytz")
    try: import pydub
    except ImportError: missing_deps.append("pydub")

    if missing_deps:
        print(f"WARNING: Missing required libraries: {', '.join(missing_deps)}. Please install them.")
        # exit(1) # Optionally exit if critical dependencies are missing

    if not os.path.exists(TEXT_IMAGE_FONT_PATH):
        print(f"CRITICAL WARNING: Text command font not found: {TEXT_IMAGE_FONT_PATH}. The 'text' command will likely fail.")
        print("Please place the font file (e.g., MochiyPopOne-Regular.ttf) in the 'assets/fonts/' directory.")

    print("Starting Bot...")
    try:
        # load_game_points() is called in on_ready, ensure it's robust
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("CRITICAL ERROR: Invalid Discord Bot Token. Please check your DISCORD_BOT_TOKEN in .env")
    except Exception as e:
        print(f"CRITICAL ERROR during bot execution: {e}")
        traceback.print_exc()
