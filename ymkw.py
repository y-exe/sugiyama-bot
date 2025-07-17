# ========================== IMPORTS ==========================
import os, sys, discord, datetime, asyncio, aiohttp, urllib.parse, json, io, random, math, subprocess, traceback, unicodedata, re
import xml.etree.ElementTree as ET
import google.generativeai as genai
import pytz
import numpy as np
from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from collections import deque
from dotenv import load_dotenv

# ========================== CONFIGURATION & INITIALIZATION ==========================
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
BASE_DIR = os.path.dirname(__file__)

# --- Bot & API Keys ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VOICEVOX_API_KEY = os.getenv("VOICEVOX_API_KEY")
SHORTURL_API_KEY = os.getenv("SHORTURL_API_KEY")

# --- API Endpoints ---
WEATHER_API_BASE_URL = "https://weather.tsukumijima.net/api/forecast/city/"
PRIMARY_AREA_XML_URL = "https://weather.tsukumijima.net/primary_area.xml"
EXCHANGE_RATE_API_URL = "https://exchange-rate-api.krnk.org/api/rate"
SHORTURL_API_ENDPOINT = "https://xgd.io/V1/shorten"
AMAZON_SHORTURL_ENDPOINT = "https://www.amazon.co.jp/associates/sitestripe/getShortUrl"
VOICEVOX_API_BASE_URL = "https://deprecatedapis.tts.quest/v2/voicevox/audio/"

# --- Bot Settings ---
_DUMMY_PREFIX_VALUE = "!@#$%^&SUGIYAMA_BOT_DUMMY_PREFIX_XYZ_VERY_UNIQUE"
def get_dummy_prefix(bot, message): return _DUMMY_PREFIX_VALUE
VOICEVOX_SPEAKER_ID = 11

# --- Imakita Command Settings ---
IMAKITA_RATE_LIMIT_SECONDS = 60
IMAKITA_RATE_LIMIT_COUNT = 5
imakita_request_timestamps = deque()

# --- File Paths & Data ---
SETTINGS_FILE_PATH = os.path.join(BASE_DIR, "bot_settings.json")
GAME_POINTS_FILE_PATH = os.path.join(BASE_DIR, "game_points.json")
LOGIN_BONUS_DATA_FILE_PATH = os.path.join(BASE_DIR, "login_bonus_data.json")
WEATHER_CITY_CODES_FILE_PATH = os.path.join(BASE_DIR, "weather_city_codes.json")
allowed_channels = set()
game_points = {}
login_bonus_data = {}
weather_city_id_map = {}
JST = pytz.timezone("Asia/Tokyo")
MAX_FILE_SIZE_BYTES = int(7.8 * 1024 * 1024)
MIN_IMAGE_DIMENSION = 300

# --- Watermark Templates ---
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
    {"name": "REDMAGIC9PRO.png", "user_ratio_str": "6/5", "target_size": (4080, 3400)},
    {"name": "REDMI121.png", "user_ratio_str": "64/85", "target_size": (3072, 4080)},
    {"name": "REDMI122.png", "user_ratio_str": "85/64", "target_size": (4080, 3072)},
    {"name": "OPPOFINDX5PRO.png", "user_ratio_str": "256/363", "target_size": (3072, 4356)},
    {"name": "ONELINE.png", "user_ratio_str": "3175/2458", "target_size": (6530, 4916)},
    {"name": "NOTHINGPHONE2A.png", "user_ratio_str": "3265/2458", "target_size": (6530, 4916)}, 
    {"name": "VIVOX60TPRO2.png", "user_ratio_str": "3/4", "target_size": (3000, 4000)},
    {"name": "VIVOX60TPRO.png", "user_ratio_str": "4/3", "target_size": (4080, 3060)},
    {"name": "ONEPLUS11R5G.png", "user_ratio_str": "8/7", "target_size": (8192, 7168)},
    {"name": "XIAOMI15ULTRA 3.png", "user_ratio_str": "1151/1818", "target_size": (2302, 3636)},
    {"name": "XIAOMI15ULTRA 2.png", "user_ratio_str": "568/503", "target_size": (4544, 4024)},
    {"name": "HONORMAGIC7PRO.png", "user_ratio_str": "16/10", "target_size": (4096, 2560)},
    {"name": "ONEPLUS.png", "user_ratio_str": "4/3", "target_size": (4096, 3072)},
    {"name": "NIKOND7500.png", "user_ratio_str": "974/1591", "target_size": (3896, 6364)}, 
    {"name": "VIVOXFOLD3PRO.png", "user_ratio_str": "300/257", "target_size": (1200, 1028)},
    {"name": "VIVOX100.png", "user_ratio_str": "300/257", "target_size": (1200, 1028)},
    {"name": "HUAWEIP30PRO.png", "user_ratio_str": "4/3", "target_size": (3648, 2736)},
    {"name": "XIAOMI13ULTRA.png", "user_ratio_str": "1/1", "target_size": (2048, 2048)} 
]
for t_data in TEMPLATES_DATA:
    if 'match_ratio_wh' not in t_data:
        try:
            w, h = map(float, t_data['user_ratio_str'].split('/'))
            t_data['match_ratio_wh'] = w / h if h != 0 else 1.0
        except (ValueError, ZeroDivisionError) as e:
            print(f"Template ratio error: {t_data['name']} - {e}")
            t_data['match_ratio_wh'] = 1.0

# --- Game & Emoji Settings ---
GREEN_SQUARE = "<:o0:1387735237173182544>"
BLACK_STONE = "<:o2:1387735312129593445>"
WHITE_STONE = "<:o1:1387735281775411220>"
MARKERS = ["<:0_o:1387735948812488734>","<:1_o:1387735961374560368>","<:2_o:1387735974582423663>","<:3_o:1387735988629147710>","<:4_o:1387736001157398568>","<:5_o:1387736014591758367>","<:6_o:1387736028684750868>","<:7_o:1387736046099501077>","<:8_o:1387736058783072266>","<:9_o:1387736070518603776>","<:o_A:1380638761288859820>","<:o_B:1380638762941419722>","<:o_C:1380638764782850080>","<:o_D:1380638769216225321>","<:o_E:1380638771178897559>","<:o_F:1380638773926301726>","<:o_G:1380638776103010365>","<:o_H:1380643990784966898>","<:o_I:1380644006093918248>","<:o_J:1380644004181577849>","<:o_K:1380644001652281374>","<:o_L:1380643998841966612>","<:o_M:1380643995855622254>","<:o_N:1380643993431314432>","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"]
active_games = {} # Othello
OTHELLO_AFK_TIMEOUT_SECONDS = 180
active_janken_games = {}
HAND_EMOJIS = {"rock": "✊", "scissors": "✌️", "paper": "✋"}
EMOJI_TO_HAND = {v: k for k, v in HAND_EMOJIS.items()}
JANKEN_WIN_POINTS, JANKEN_LOSE_POINTS, JANKEN_DRAW_POINTS = 7, -5, 2
BET_DICE_PAYOUTS = {
    1: ("大凶... 賭け金は没収です。", -1.0), 2: ("凶。賭け金の半分を失いました。", -0.5),
    3: ("小吉。賭け金の半分を失いました。", -0.5), 4: ("吉！賭け金はそのまま戻ってきます。", 0.0),
    5: ("中吉！賭け金が1.5倍になりました。", 0.5), 6: ("大吉！おめでとうございます！賭け金が2倍になりました！", 1.0)
}
# Connect Four
CONNECTFOUR_MARKERS = MARKERS[1:8]
CF_EMPTY, CF_P1_TOKEN, CF_P2_TOKEN = "<:4_0:1395065436114128937>", "<:4_1:1395065453675544586>", "<:4_2:1395065472491323493>"
ROWS, COLS = 6, 7
CONNECTFOUR_WIN_POINTS, CONNECTFOUR_LOSE_POINTS, CONNECTFOUR_DRAW_POINTS = 15, -10, 5
active_connectfour_games = {}
# High & Low
active_highlow_games = {}
# Badge Emojis
USER_BADGES_EMOJI = {
    'staff': '<:staff:1383251602680578111>',
    'partner': '<:partnerserver:1383251682070364210>',
    'hypesquad': '<:events:1383251448451563560>',
    'hypesquad_bravery': '<:bravery:1383251749623693392>',
    'hypesquad_brilliance': '<:brilliance:1383251723610624174>',
    'hypesquad_balance': '<:balance:1383251792413851688>',
    'bug_hunter': '<:bugHunter:1383251633567170683>',
    'bug_hunter_level_2': '<:bugHunter:1383251633567170683>',
    'early_supporter': '<:earlysupporter:1383251618379727031>',
    'early_verified_bot_developer': '<:earlyverifiedbot:1383251648348160030>',
    'verified_bot_developer': '<:earlyverifiedbot:1383251648348160030>',
    'discord_certified_moderator': '<:moderator:1383251587438215218>',
    'active_developer': '<:activedeveloper:1383253229189730374>',
    'nitro': '<:nitro:1383252018532974642>',
    'booster': '<:booster:1383251702144176168>',
}

# --- Text Image & RVC Settings ---
GEMINI_TEXT_MODEL_NAME = 'models/gemini-2.5-flash-lite-preview-06-17'
RVC_PROJECT_ROOT_PATH = os.path.abspath(os.path.join(BASE_DIR, "RVC_Project"))
RVC_MODEL_DIR_IN_PROJECT = os.path.join("assets", "weights")
RVC_MODEL_NAME_WITH_EXT = "ymkw.pth"
RVC_INFER_SCRIPT_SUBPATH = os.path.join("tools", "infer_cli.py")
RVC_FIXED_TRANSPOSE = 0
RVC_INPUT_AUDIO_DIR, RVC_OUTPUT_AUDIO_DIR = os.path.join(BASE_DIR, "audio", "input"), os.path.join(BASE_DIR, "audio", "output")
WAIFU2X_CAFFE_PATH = os.getenv("WAIFU2X_CAFFE_PATH")

# --- Font & Color Settings ---
TEXT_IMAGE_FONT_PATH_DEFAULT = os.path.join(BASE_DIR, "assets", "fonts", "MochiyPopOne-Regular.ttf")
TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD = os.path.join(BASE_DIR, "assets", "fonts", "NotoSerifJP-Black.ttf")
TEXT_IMAGE_FONT_SIZE_COMMON = 110
NORMAL_LETTER_SPACING = 0
SQUARE_LETTER_SPACING = -17
NORMAL_TEXT_COLOR_YELLOW = (255, 255, 0)
NORMAL_TEXT_COLOR_BLUE = (50, 150, 255)
NORMAL_OUTLINE_COLOR_BLACK = (0, 0, 0)
NORMAL_OUTLINE_THICKNESS_BLACK = 7
NORMAL_OUTLINE_COLOR_WHITE = (255, 255, 255)
NORMAL_OUTLINE_THICKNESS_WHITE = 5
SQUARE_TEXT_COLOR_YELLOW = (255, 255, 0)
SQUARE_TEXT_COLOR_BLUE = (50, 150, 255)
SQUARE_OUTLINE_COLOR_BLACK = (0, 0, 0)
SQUARE_OUTLINE_THICKNESS_BLACK = 15
SQUARE_OUTLINE_COLOR_WHITE = (255, 255, 255)
SQUARE_OUTLINE_THICKNESS_WHITE = 12
NORMAL_TEXT3_COLOR_RED = (0xC3, 0x02, 0x03)
NORMAL_TEXT3_OUTLINE_COLOR_WHITE = (255, 255, 255)
NORMAL_TEXT3_OUTLINE_THICKNESS_WHITE = 7
SQUARE_TEXT3_COLOR_RED = (0xC3, 0x02, 0x03)
SQUARE_TEXT3_OUTLINE_COLOR_WHITE = (255, 255, 255)
SQUARE_TEXT3_OUTLINE_THICKNESS_WHITE = 15
SQUARE_IMAGE_SIZE = 500
SQUARE_PADDING_FOR_OUTLINE = 15

# --- Initialization ---
gemini_text_model_instance = None
GEMINI_API_UNAVAILABLE = False
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_PLACEHOLDER":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_text_model_instance = genai.GenerativeModel(GEMINI_TEXT_MODEL_NAME)
    except Exception as e:
        print(f"Gemini init error: {e}")
        GEMINI_API_UNAVAILABLE = True
else:
    GEMINI_API_UNAVAILABLE = True

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix=get_dummy_prefix, intents=intents, help_command=None, case_insensitive=True)

for d in [RVC_INPUT_AUDIO_DIR, RVC_OUTPUT_AUDIO_DIR, os.path.join(BASE_DIR, "assets", "fonts"), TEMPLATES_BASE_PATH]:
    os.makedirs(d, exist_ok=True)

# ========================== HELPER FUNCTIONS (Order is important!) ==========================

# --- Custom Embeds & Error Helper ---
STATUS_EMOJIS = {
    "success": "<:status_success:1389613617560682666>", "danger": "<:status_danger:1389613631968247838>",
    "info": "<:status_info:1389613655640899734>", "warning": "<:status_warning:1389613669515661394>",
    "pending": "<:status_pending:1389613644089655296>"
}
BOT_ICON_URL = "https://raw.githubusercontent.com/y-exe/sugiyama-bot/main/icon.jpg"

def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue(), status: str = "info", api_source: str = None) -> discord.Embed:
    embed = discord.Embed(title=f"{STATUS_EMOJIS.get(status, '')} {title}", description=description, color=color)
    footer_text = "杉山啓太Bot"
    if api_source: footer_text += f" / {api_source}"
    embed.set_footer(text=footer_text, icon_url=BOT_ICON_URL)
    embed.timestamp = datetime.datetime.now(JST)
    return embed

async def send_error_embed(ctx, error: Exception):
    channel = None
    if isinstance(ctx, commands.Context): channel = ctx.channel
    elif isinstance(ctx, discord.Interaction): channel = ctx.channel
    elif isinstance(ctx, discord.abc.Messageable): channel = ctx
    if channel:
        error_traceback = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        description = f"開発者 (<@1102557945889300480>)に報告してください。\n```{error_traceback[:1800]}```"
        embed = create_embed("エラーが発生しました", description, discord.Color.red(), status="danger")
        try:
            if isinstance(ctx, discord.Interaction) and ctx.response.is_done():
                await ctx.followup.send(embed=embed, ephemeral=True)
            else: await channel.send(embed=embed)
        except Exception as e:
            print(f"CRITICAL: Failed to send error embed to channel {channel.id}. Reason: {e}")
    print(f"--- ERROR in command/event ---\nContext/Interaction Channel: {getattr(channel, 'name', 'N/A')}")
    traceback.print_exc()

# --- Data Management (Points, Settings, etc.) ---
def load_game_points():
    global game_points
    try:
        if os.path.exists(GAME_POINTS_FILE_PATH):
            with open(GAME_POINTS_FILE_PATH, 'r', encoding='utf-8') as f: game_points = json.load(f)
        else: game_points = {}; save_game_points()
    except (json.JSONDecodeError, IOError):
        game_points = {}; save_game_points(); print(f"Corrupted game points file at {GAME_POINTS_FILE_PATH}, created new.")
    except Exception as e: print(f"Error loading game points: {e}"); game_points = {}

def save_game_points():
    try:
        with open(GAME_POINTS_FILE_PATH, 'w', encoding='utf-8') as f: json.dump(game_points, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Error saving game points: {e}")

def get_player_points(player_id: int) -> int:
    return game_points.get(str(player_id), 0)

def update_player_points(player_id: int, points_change: int):
    if not isinstance(player_id, int) or player_id == bot.user.id: return
    player_id_str = str(player_id)
    current_points = game_points.get(player_id_str, 0)
    new_points = max(0, current_points + points_change)
    game_points[player_id_str] = new_points
    save_game_points()

def load_settings():
    global allowed_channels
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
                allowed_channels = set(settings_data.get("allowed_channels", []))
        else: allowed_channels = set(); save_settings()
    except Exception as e: print(f"Error loading settings: {e}"); allowed_channels = set()

def save_settings():
    try:
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump({"allowed_channels": list(allowed_channels)}, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Error saving settings: {e}")

def load_login_bonus_data():
    global login_bonus_data
    try:
        if os.path.exists(LOGIN_BONUS_DATA_FILE_PATH):
            with open(LOGIN_BONUS_DATA_FILE_PATH, 'r', encoding='utf-8') as f: login_bonus_data = json.load(f)
        else: login_bonus_data = {}; save_login_bonus_data()
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading login bonus data, creating new file: {e}"); login_bonus_data = {}; save_login_bonus_data()

def save_login_bonus_data():
    try:
        with open(LOGIN_BONUS_DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(login_bonus_data, f, indent=4, ensure_ascii=False)
    except IOError as e: print(f"Error saving login bonus data: {e}")

# --- Game Logic & UI Classes (Othello, ConnectFour, High&Low) ---

# Othello
EMPTY = 0; BLACK = 1; WHITE = 2
class OthelloGame:
    _next_game_id_counter = 1
    def __init__(self, board_size: int = 8):
        self.board_size, self.board = board_size, [[EMPTY]*board_size for _ in range(board_size)]
        mid_l, mid_h = board_size // 2 - 1, board_size // 2
        self.board[mid_l][mid_l], self.board[mid_l][mid_h] = WHITE, BLACK
        self.board[mid_h][mid_l], self.board[mid_h][mid_h] = BLACK, WHITE
        self.current_player, self.valid_moves_with_markers = BLACK, {}
        self.game_over, self.winner, self.last_pass = False, None, False
        self.players, self.channel_id, self.message_id = {}, None, None
        self.last_move_time = datetime.datetime.now(JST)
        self.game_id = OthelloGame._assign_game_id_static()
        self.afk_task = None
    @staticmethod
    def _assign_game_id_static(): gid = OthelloGame._next_game_id_counter; OthelloGame._next_game_id_counter += 1; return gid
    def is_on_board(self,r,c): return 0<=r<self.board_size and 0<=c<self.board_size
    def get_flips(self,r_s,c_s,p):
        if not self.is_on_board(r_s,c_s) or self.board[r_s][c_s]!=EMPTY: return []
        op=WHITE if p==BLACK else BLACK; ttf=[]
        for dr,dc in [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]:
            r,c=r_s+dr,c_s+dc; cpf=[]
            while self.is_on_board(r,c) and self.board[r][c]==op: cpf.append((r,c)); r+=dr; c+=dc
            if self.is_on_board(r,c) and self.board[r][c]==p and cpf: ttf.extend(cpf)
        return ttf
    def calculate_valid_moves(self,p):
        self.valid_moves_with_markers.clear(); mi=0; cvc=[]
        for r_idx in range(self.board_size):
            for c_idx in range(self.board_size):
                if self.board[r_idx][c_idx]==EMPTY and self.get_flips(r_idx,c_idx,p): 
                    cvc.append((r_idx,c_idx)); self.valid_moves_with_markers[(r_idx,c_idx)]=MARKERS[mi] if mi<len(MARKERS) else "❓"; mi+=1
        return cvc
    def make_move(self,r,c,p):
        if self.game_over or not self.is_on_board(r,c) or self.board[r][c]!=EMPTY: return False
        ttf=self.get_flips(r,c,p)
        if not ttf: return False
        self.board[r][c]=p
        for fr_loop, fc_loop in ttf: self.board[fr_loop][fc_loop] = p
        self.last_pass=False; self.last_move_time=datetime.datetime.now(JST); return True
    def switch_player(self): self.current_player = WHITE if self.current_player==BLACK else BLACK
    def check_game_status(self):
        if self.game_over: return
        if self.calculate_valid_moves(self.current_player): self.last_pass=False; return
        if self.last_pass: self.game_over=True
        else: self.last_pass=True; self.switch_player()
        if not self.calculate_valid_moves(self.current_player): self.game_over=True
        if self.game_over: self.determine_winner()
    def determine_winner(self):
        bs, ws = sum(r.count(BLACK) for r in self.board), sum(r.count(WHITE) for r in self.board)
        self.winner = BLACK if bs>ws else (WHITE if ws>bs else EMPTY)
    def get_current_player_id(self): return self.players.get(self.current_player)

# High & Low
class HighLow対戦Game:
    def __init__(self, host_id, opponent_id, bet_amount, message_id):
        self.players = [host_id, opponent_id]
        self.bet = bet_amount
        self.choices = {host_id: None, opponent_id: None}
        self.current_card = random.randint(1, 13)
        self.message_id = message_id
    def get_card_display(self, card_value=None):
        target_card = card_value if card_value is not None else self.current_card
        if target_card == 1: return "A"
        if target_card == 11: return "J"
        if target_card == 12: return "Q"
        if target_card == 13: return "K"
        return str(target_card)
    def has_everyone_chosen(self):
        return all(self.choices.values())

# Connect Four
class ConnectFourGame:
    _next_game_id_counter = 1
    def __init__(self, p1_id, p2_id):
        self.board = [[CF_EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        player_ids = [p1_id, p2_id]
        random.shuffle(player_ids)
        self.players = {CF_P1_TOKEN: player_ids[0], CF_P2_TOKEN: player_ids[1]}
        self.current_player_token = CF_P1_TOKEN
        self.winner = None
        self.game_over = False
        self.message_id = None
        self.channel_id = None
        self.afk_task = None
        self.game_id = ConnectFourGame._assign_game_id_static()
    @staticmethod
    def _assign_game_id_static():
        gid = ConnectFourGame._next_game_id_counter
        ConnectFourGame._next_game_id_counter += 1; return gid
    def get_current_player_id(self):
        return self.players.get(self.current_player_token)
    def drop_token(self, col):
        if not (0 <= col < COLS) or self.board[0][col] != CF_EMPTY: return False
        for r in range(ROWS - 1, -1, -1):
            if self.board[r][col] == CF_EMPTY:
                self.board[r][col] = self.current_player_token
                return True
        return False
    def check_win(self):
        token = self.current_player_token
        if token == CF_EMPTY: return False
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(self.board[r][c+i] == token for i in range(4)): self.winner=token; self.game_over=True; return True
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(self.board[r+i][c] == token for i in range(4)): self.winner=token; self.game_over=True; return True
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(self.board[r+i][c+i] == token for i in range(4)): self.winner=token; self.game_over=True; return True
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(self.board[r-i][c+i] == token for i in range(4)): self.winner=token; self.game_over=True; return True
        return False
    def switch_player(self):
        self.current_player_token = CF_P2_TOKEN if self.current_player_token == CF_P1_TOKEN else CF_P1_TOKEN
    def is_board_full(self):
        is_full = all(self.board[0][c] != CF_EMPTY for c in range(COLS))
        if is_full: self.game_over = True
        return is_full

# --- Game Helper Functions (Moved to be before UI Classes) ---

def create_othello_board_embed(game_session: dict) -> discord.Embed:
    game = game_session["game"]
    p_black_id = game_session["players"].get(BLACK)
    p_white_id = game_session["players"].get(WHITE)
    current_player_id = game.get_current_player_id()
    p_black_mention = f"<@{p_black_id}> (Pt: {get_player_points(p_black_id)})" if p_black_id != bot.user.id else f"<@{p_black_id}>"
    p_white_mention = f"<@{p_white_id}> (Pt: {get_player_points(p_white_id)})" if p_white_id != bot.user.id else f"<@{p_white_id}>"
    current_player_mention = f"<@{current_player_id}>"
    title = f"オセロゲーム #{game.game_id} ({game.board_size}x{game.board_size})"
    color = discord.Color.green() if not game.game_over else discord.Color.dark_grey()
    embed = discord.Embed(title=title, color=color)
    board_lines = []
    if not game.game_over: game.calculate_valid_moves(game.current_player)
    for r_idx in range(game.board_size):
        row_str = "".join(
            game.valid_moves_with_markers.get((r_idx, c_idx)) or 
            {BLACK: BLACK_STONE, WHITE: WHITE_STONE}.get(game.board[r_idx][c_idx], GREEN_SQUARE)
            for c_idx in range(game.board_size)
        )
        board_lines.append(row_str)
    embed.description = (f"{BLACK_STONE} {p_black_mention} vs {WHITE_STONE} {p_white_mention}\n\n" + "\n".join(board_lines))
    black_score = sum(r.count(BLACK) for r in game.board)
    white_score = sum(r.count(WHITE) for r in game.board)
    embed.add_field(name="スコア", value=f"{BLACK_STONE} {black_score} - {WHITE_STONE} {white_score}", inline=True)
    if not game.game_over:
        embed.add_field(name="手番", value=current_player_mention, inline=True)
        embed.set_footer(text="石を置きたい場所のリアクションを押してください。")
    else:
        embed.add_field(name="状態", value="**ゲーム終了**", inline=True)
    embed.timestamp = datetime.datetime.now(JST)
    return embed

async def send_othello_result_message(channel: discord.TextChannel, game_session: dict, original_message: discord.Message, reason_key: str = "normal"):
    game = game_session["game"]
    final_board_embed = create_othello_board_embed(game_session)
    try: await original_message.edit(embed=final_board_embed, view=None)
    except discord.HTTPException: pass
    p_black_id, p_white_id = game.players.get(BLACK), game.players.get(WHITE)
    is_bot_match = bot.user.id in [p_black_id, p_white_id]
    try:
        p_black_user = await bot.fetch_user(p_black_id) if p_black_id else None
        p_white_user = await bot.fetch_user(p_white_id) if p_white_id else None
    except discord.NotFound: p_black_user, p_white_user = None, None
    result_embed = create_embed(f"オセロゲーム #{game.game_id} 結果", "", discord.Color.gold(), "success")
    winner_text, points_changed_text = "引き分け", ""
    ended_by_action = getattr(game, 'ended_by_action', False)
    if game.winner != EMPTY:
        winner_id, loser_id = game.players.get(game.winner), game.players.get(WHITE if game.winner == BLACK else BLACK)
        try:
            winner_user = await bot.fetch_user(winner_id) if winner_id else None
            loser_user = await bot.fetch_user(loser_id) if loser_id else None
        except discord.NotFound: winner_user, loser_user = None, None
        winner_mention = winner_user.mention if winner_user else f'ID:{winner_id}'
        loser_mention = loser_user.mention if loser_user else f'ID:{loser_id}'
        winner_stone = BLACK_STONE if game.winner == BLACK else WHITE_STONE
        reason_text = f"🏆 {winner_stone} **{winner_mention}** の勝ち！"
        if reason_key == "afk": reason_text = f"**{loser_mention}** が時間切れのため、{winner_stone} **{winner_mention}** の勝ち！"
        elif reason_key == "leave": reason_text = f"**{loser_mention}** が離脱したため、{winner_stone} **{winner_mention}** の勝ち！"
        winner_text = reason_text
        if winner_user and loser_user and not is_bot_match:
            black_score, white_score = sum(r.count(BLACK) for r in game.board), sum(r.count(WHITE) for r in game.board)
            score_diff = abs(black_score - white_score)
            points_win, points_lose = 0, 0
            if ended_by_action:
                win_status_bonus = max(0, (black_score if winner_id == p_black_id else white_score) - (white_score if winner_id == p_black_id else black_score))
                if game.board_size == 6: points_win, points_lose = 20 + win_status_bonus, -15 + win_status_bonus
                elif game.board_size == 8: points_win, points_lose = 20 + (win_status_bonus * 2), -15 + (win_status_bonus * 2)
                else: points_win, points_lose = 30 + (win_status_bonus * 3), -10 + (win_status_bonus * 3)
            else:
                if game.board_size == 6: points_win, points_lose = score_diff * 2 + 20, max(0, 30 - score_diff)
                elif game.board_size == 8: points_win, points_lose = score_diff * 3 + 20, max(0, 50 - score_diff)
                else: points_win, points_lose = score_diff * 4 + 30, max(0, 60 - score_diff)
            update_player_points(winner_id, points_win); update_player_points(loser_id, -points_lose)
            points_changed_text = f"▫️ {winner_user.name}: `+{points_win}pt`\n▫️ {loser_user.name}: `{-points_lose}pt`"
    elif game.winner == EMPTY and not ended_by_action and not is_bot_match:
        winner_text = "🤝 引き分け！"; points_for_draw = 5 
        update_player_points(p_black_id, points_for_draw); update_player_points(p_white_id, points_for_draw)
        points_changed_text = f"▫️ 両者: `+{points_for_draw}pt`"
    result_embed.add_field(name="結果", value=winner_text, inline=False)
    if points_changed_text:
        result_embed.add_field(name="ポイント変動", value=points_changed_text, inline=False)
        if p_black_user and p_white_user:
            result_embed.add_field(name="現在のポイント", value=f"▫️ {p_black_user.name}: `{get_player_points(p_black_id)}pt`\n▫️ {p_white_user.name}: `{get_player_points(p_white_id)}pt`", inline=False)
    try: await original_message.reply(embed=result_embed, mention_author=False)
    except discord.HTTPException as e: print(f"Failed to send othello result message: {e}")
    try: await original_message.clear_reactions()
    except discord.HTTPException: pass
    if original_message.id in active_games: del active_games[original_message.id]

async def othello_afk_timeout(game: OthelloGame):
    await asyncio.sleep(OTHELLO_AFK_TIMEOUT_SECONDS)
    game_session = active_games.get(game.message_id)
    if game_session and game_session.get("game") == game and not game.game_over:
        print(f"Othello Game #{game.game_id}: AFK timeout for player {game.get_current_player_id()}")
        game.game_over = True
        game.winner = WHITE if game.current_player == BLACK else BLACK 
        setattr(game, 'ended_by_action', 'afk')
        channel = bot.get_channel(game.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(game.message_id)
                await send_othello_result_message(channel, game_session, message, "afk")
            except (discord.NotFound, discord.HTTPException) as e: print(f"AFK Timeout: Error handling message: {e}")

async def make_bot_move(message: discord.Message, game_session: dict):
    game = game_session["game"]
    if game.game_over or game.get_current_player_id() != bot.user.id: return
    await asyncio.sleep(random.uniform(0.5, 0.9))
    valid_moves = game.calculate_valid_moves(game.current_player)
    if not valid_moves:
        game.switch_player(); game.check_game_status()
        if game.game_over: await send_othello_result_message(message.channel, game_session, message)
        else: await message.edit(embed=create_othello_board_embed(game_session))
        return
    size, last_idx = game.board_size, game.board_size - 1
    corners = {(0, 0), (0, last_idx), (last_idx, 0), (last_idx, last_idx)}
    bad_spots_map = { (0, 0): {(0, 1), (1, 0), (1, 1)}, (0, last_idx): {(0, last_idx - 1), (1, last_idx), (1, last_idx - 1)},
                      (last_idx, 0): {(last_idx - 1, 0), (last_idx, 1), (last_idx - 1, 1)},
                      (last_idx, last_idx): {(last_idx - 1, last_idx), (last_idx, last_idx - 1), (last_idx - 1, last_idx - 1)} }
    corner_moves, good_moves, bad_moves = [], [], []
    for move in valid_moves:
        if move in corners: corner_moves.append(move)
        else:
            is_bad = any(game.board[c[0]][c[1]] == EMPTY and move in adj for c, adj in bad_spots_map.items())
            if is_bad: bad_moves.append(move)
            else: good_moves.append(move)
    if corner_moves: bot_move = random.choice(corner_moves)
    elif good_moves: bot_move = min(good_moves, key=lambda m: len(game.get_flips(m[0], m[1], game.current_player)))
    else: bot_move = random.choice(bad_moves) if bad_moves else random.choice(valid_moves)
    if game.make_move(bot_move[0], bot_move[1], game.current_player):
        game.switch_player(); game.check_game_status()
        await message.edit(embed=create_othello_board_embed(game_session))
        if game.game_over: await send_othello_result_message(message.channel, game_session, message)
        else:
            if game.get_current_player_id() == bot.user.id: asyncio.create_task(make_bot_move(message, game_session))
            else:
                await update_reactions_for_next_turn(message, set(game.valid_moves_with_markers.values()))
                if not bot.user.id in game.players.values(): game.afk_task = asyncio.create_task(othello_afk_timeout(game))

async def update_reactions_for_next_turn(message: discord.Message, new_emojis: set):
    try:
        current_emojis = {str(r.emoji) for r in message.reactions if r.me}
        to_remove = current_emojis - new_emojis
        to_add = new_emojis - current_emojis
        tasks = []
        for emoji_str in to_remove:
            tasks.append(message.remove_reaction(emoji_str, bot.user))
        if tasks: await asyncio.gather(*tasks, return_exceptions=True)
        sorted_to_add = sorted(list(to_add), key=lambda e: MARKERS.index(e) if e in MARKERS else float('inf'))
        for emoji in sorted_to_add:
            try: await message.add_reaction(emoji)
            except discord.HTTPException: pass
    except (discord.NotFound, discord.Forbidden): pass
    except Exception as e: print(f"Error updating reactions: {e}")

# --- Connect Four Helper Functions ---
def create_connectfour_embed(game: ConnectFourGame):
    p1_id = game.players.get(CF_P1_TOKEN)
    p2_id = game.players.get(CF_P2_TOKEN)
    p1_mention = f"<@{p1_id}>"
    p2_mention = f"<@{p2_id}>"
    title = f"四目並べ #{game.game_id}"
    board_str = "\n".join("".join(row) for row in game.board)
    numbers_str = "".join(CONNECTFOUR_MARKERS)

    description = (
        f"{CF_P1_TOKEN} {p1_mention} vs {CF_P2_TOKEN} {p2_mention}\n\n"
        f"{board_str}\n{numbers_str}\n\n"
        f"ルール: テトリスのように、コマを落としたい列のリアクションを押してください。"
    )

    embed = discord.Embed(
        title=title,
        description=f"{CF_P1_TOKEN} {p1_mention} vs {CF_P2_TOKEN} {p2_mention}\n\n{board_str}\n{numbers_str}",
        color=discord.Color.blue()
    )
    if not game.game_over:
        current_player_id = game.get_current_player_id()
        embed.add_field(name="手番", value=f"<@{current_player_id}> ({game.current_player_token})")
    else:
        if game.winner:
            winner_id = game.players.get(game.winner)
            embed.description += f"\n\n**🏆 <@{winner_id}> の勝利！**"
            embed.color = discord.Color.gold()
        else:
            embed.description += f"\n\n**🤝 引き分け！**"
            embed.color = discord.Color.light_grey()
    embed.timestamp = datetime.datetime.now(JST)
    return embed

async def send_connectfour_result_message(channel: discord.TextChannel, game: ConnectFourGame, original_message: discord.Message, reason_key: str = "normal"):
    final_embed = create_connectfour_embed(game)
    try: await original_message.edit(embed=final_embed, view=None, content=None)
    except discord.HTTPException: pass
    try: await original_message.clear_reactions()
    except discord.HTTPException: pass

    result_embed = create_embed(f"四目並べ #{game.game_id} 結果", "", discord.Color.gold(), "success")
    winner_id, loser_id = None, None
    winner_text = "🤝 引き分け！"

    if game.winner:
        winner_id = game.players.get(game.winner)
        loser_id = next((pid for pid in game.players.values() if pid != winner_id), None)
        
        winner_mention = f"<@{winner_id}>"
        loser_mention = f"<@{loser_id}>" if loser_id else "相手"

        reason_map = {
            "afk": f"**{loser_mention}** が時間切れのため、{game.winner} **{winner_mention}** の勝ち！",
            "leave": f"**{loser_mention}** が離脱したため、{game.winner} **{winner_mention}** の勝ち！",
            "normal": f"🏆 {game.winner} **{winner_mention}** の勝ち！"
        }
        winner_text = reason_map.get(reason_key, reason_map["normal"])

    result_embed.add_field(name="結果", value=winner_text, inline=False)
    
    points_changed_text = ""
    
    if winner_id and loser_id:
        if winner_id != bot.user.id:
            update_player_points(winner_id, CONNECTFOUR_WIN_POINTS)
        if loser_id != bot.user.id:
            update_player_points(loser_id, CONNECTFOUR_LOSE_POINTS)
        
        try:
            winner_user = await bot.fetch_user(winner_id)
            loser_user = await bot.fetch_user(loser_id)
            
            winner_pt_text = f"`{CONNECTFOUR_WIN_POINTS:+}pt`" if winner_id != bot.user.id else "`±0pt`"
            loser_pt_text = f"`{CONNECTFOUR_LOSE_POINTS:+}pt`" if loser_id != bot.user.id else "`±0pt`"
            
            points_changed_text = f"▫️ {winner_user.name}: {winner_pt_text}\n▫️ {loser_user.name}: {loser_pt_text}"
        except discord.NotFound: pass

    elif not game.winner and not (bot.user.id in game.players.values()):
        p1_id, p2_id = game.players.values()
        update_player_points(p1_id, CONNECTFOUR_DRAW_POINTS)
        update_player_points(p2_id, CONNECTFOUR_DRAW_POINTS)
        points_changed_text = f"▫️ 両者: `+{CONNECTFOUR_DRAW_POINTS}pt`"

    if points_changed_text:
        result_embed.add_field(name="ポイント変動", value=points_changed_text, inline=False)

    await original_message.reply(embed=result_embed, mention_author=False)
    if original_message.id in active_connectfour_games:
        del active_connectfour_games[original_message.id]

async def connectfour_afk_timeout(game: ConnectFourGame):
    await asyncio.sleep(OTHELLO_AFK_TIMEOUT_SECONDS)
    game_session = active_connectfour_games.get(game.message_id)
    if game_session and game_session == game and not game.game_over:
        print(f"ConnectFour Game #{game.game_id}: AFK timeout for player {game.get_current_player_id()}")
        game.game_over = True
        game.winner = CF_P2_TOKEN if game.current_player_token == CF_P1_TOKEN else CF_P1_TOKEN
        channel = bot.get_channel(game.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(game.message_id)
                await send_connectfour_result_message(channel, game, message, "afk")
            except (discord.NotFound, discord.HTTPException) as e: print(f"CF AFK Timeout: Error handling message: {e}")

def _check_win_for_logic(board, token, col, rows, cols):
    """【廃止予定】この関数は新しいAIでは使いませんが、互換性のために残します。"""
    return False

def get_connectfour_bot_move(game: ConnectFourGame) -> int:
    """コネクトフォーのBotの思考ロジック (最終改訂版)"""
    valid_cols = [c for c in range(COLS) if game.board[0][c] == CF_EMPTY]
    if not valid_cols:
        return -1

    my_token = game.current_player_token
    opponent_token = CF_P1_TOKEN if my_token == CF_P2_TOKEN else CF_P2_TOKEN

    def check_move(token_to_check):
        """指定されたトークンが、次にどこかに置けば勝てる手を探す"""
        for col in valid_cols:
            # 仮想の盤面を作成
            temp_board = [row[:] for row in game.board]
            
            # その列にコマを落とす
            row = -1
            for r in range(ROWS - 1, -1, -1):
                if temp_board[r][col] == CF_EMPTY:
                    temp_board[r][col] = token_to_check
                    row = r
                    break
            if row == -1: continue

            for c in range(COLS - 3):
                if all(temp_board[row][c+i] == token_to_check for i in range(4)): return col
            if row <= ROWS - 4:
                if all(temp_board[row+i][col] == token_to_check for i in range(4)): return col
            for i in range(4):
                start_r, start_c = row - i, col - i
                if 0 <= start_r <= ROWS - 4 and 0 <= start_c <= cols - 4:
                    if all(temp_board[start_r+j][start_c+j] == token_to_check for j in range(4)): return col
            for i in range(4):
                start_r, start_c = row + i, col - i
                if 3 <= start_r < ROWS and 0 <= start_c <= cols - 4:
                    if all(temp_board[start_r-j][start_c+j] == token_to_check for j in range(4)): return col
        return None

    win_move = check_move(my_token)
    if win_move is not None:
        return win_move

    block_move = check_move(opponent_token)
    if block_move is not None:
        return block_move

    preferred_order = [3, 4, 2, 5, 1, 6, 0]
    for col in preferred_order:
        if col in valid_cols:
            return col
            
    return random.choice(valid_cols)


def get_connectfour_bot_move(game: ConnectFourGame) -> int:
    """コネクトフォーのBotの思考ロジック (斜め判定強化版)"""
    valid_cols = [c for c in range(COLS) if game.board[0][c] == CF_EMPTY]
    if not valid_cols:
        return -1

    my_token = game.current_player_token
    opponent_token = CF_P1_TOKEN if my_token == CF_P2_TOKEN else CF_P2_TOKEN

    def check_move(token_to_check):
        """指定されたトークンが、次にどこかに置けば勝てる手を探す"""
        for col in valid_cols:
            temp_board = [row[:] for row in game.board]
            
            row = -1
            for r in range(ROWS - 1, -1, -1):
                if temp_board[r][col] == CF_EMPTY:
                    temp_board[r][col] = token_to_check
                    row = r
                    break
            if row == -1: continue

            for c in range(COLS - 3):
                if all(temp_board[row][c+i] == token_to_check for i in range(4)): return col
            if row <= ROWS - 4:
                if all(temp_board[row+i][col] == token_to_check for i in range(4)): return col
            for r_start in range(ROWS - 3):
                for c_start in range(COLS - 3):
                    if all(temp_board[r_start+i][c_start+i] == token_to_check for i in range(4)): return col
            for r_start in range(3, ROWS):
                for c_start in range(COLS - 3):
                    if all(temp_board[r_start-i][c_start+i] == token_to_check for i in range(4)): return col
        return None

    win_move = check_move(my_token)
    if win_move is not None:
        return win_move

    block_move = check_move(opponent_token)
    if block_move is not None:
        return block_move

    preferred_order = [3, 4, 2, 5, 1, 6, 0]
    for col in preferred_order:
        if col in valid_cols:
            return col
            
    return random.choice(valid_cols)

async def update_cf_board_and_reactions(message: discord.Message, game: ConnectFourGame):
    """コネクトフォーの盤面を更新する（リアクションは変更しない）"""
    embed = create_connectfour_embed(game)
    await message.edit(embed=embed)

# --- Game View & UI Classes (Othello, ConnectFour, High&Low) ---
class HighLowChoiceView(discord.ui.View):
    def __init__(self, game_id):
        super().__init__(timeout=60.0)
        self.game_id = game_id
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        game = active_highlow_games.get(self.game_id)
        if not game or interaction.user.id not in game.players:
            await interaction.response.send_message("このゲームの参加者ではありません。", ephemeral=True); return False
        if game.choices[interaction.user.id] is not None:
            await interaction.response.send_message("あなたは既に入力済みです。", ephemeral=True); return False
        return True
    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        game = active_highlow_games.get(self.game_id)
        if not game: return
        game.choices[interaction.user.id] = choice
        await interaction.response.send_message(f"あなたは「{choice.upper()}」を選びました。相手の選択を待っています...", ephemeral=True)
        if game.has_everyone_chosen():
            original_message = interaction.message
            await self.process_results(original_message, game)
            for item in self.children: item.disabled = True
            await original_message.edit(view=self); self.stop()
    async def process_results(self, message: discord.Message, game):
        host_id, opponent_id = game.players
        host_choice, opp_choice = game.choices[host_id], game.choices[opponent_id]
        new_card = random.randint(1, 13)
        while new_card == game.current_card: new_card = random.randint(1, 13)
        host_correct = (host_choice == 'high' and new_card > game.current_card) or (host_choice == 'low' and new_card < game.current_card)
        opp_correct = (opp_choice == 'high' and new_card > game.current_card) or (opp_choice == 'low' and new_card < game.current_card)
        result_desc = (f"ベット額: `{game.bet}pt`\n\n現在のカード: **{game.get_card_display()}**\n"
                       f"次のカードは... **{game.get_card_display(new_card)}**！\n\n"
                       f"【各プレイヤーの選択】\n"
                       f"<@{host_id}>: `{host_choice.upper()}` → **{'正解！' if host_correct else 'ハズレ'}**\n"
                       f"<@{opponent_id}>: `{opp_choice.upper()}` → **{'正解！' if opp_correct else 'ハズレ'}**")
        winner_id, loser_id = None, None
        if host_correct and not opp_correct: winner_id, loser_id = host_id, opponent_id
        elif not host_correct and opp_correct: winner_id, loser_id = opponent_id, host_id
        if winner_id:
            winnings = game.bet * 2
            update_player_points(winner_id, game.bet) 
            result_embed = create_embed("ハイアンドロー 結果", f"{result_desc}\n\n🏆 <@{winner_id}> が `{winnings}pt` を獲得！", discord.Color.gold(), "success")
        elif host_correct and opp_correct:
            update_player_points(host_id, game.bet); update_player_points(opponent_id, game.bet)
            result_embed = create_embed("ハイアンドロー 結果", f"{result_desc}\n\n🤝 引き分け！ベットしたポイントは返却されます。", discord.Color.light_grey(), "info")
        else:
            result_embed = create_embed("ハイアンドロー 結果", f"{result_desc}\n\n💥 両者ハズレ！ベットしたポイントは没収されます。", discord.Color.red(), "danger")
        await message.edit(embed=result_embed, view=None)
        if message.id in active_highlow_games: del active_highlow_games[message.id]
    @discord.ui.button(label="ハイ (High)", style=discord.ButtonStyle.success, emoji="🔼")
    async def high_button(self, i, b): await self.handle_choice(i, "high")
    @discord.ui.button(label="ロー (Low)", style=discord.ButtonStyle.danger, emoji="🔽")
    async def low_button(self, i, b): await self.handle_choice(i, "low")

class HighLowRecruitmentView(discord.ui.View):
    def __init__(self, host, opponent, bet_amount):
        super().__init__(timeout=120.0)
        self.host, self.opponent, self.bet_amount, self.message = host, opponent, bet_amount, None
    @discord.ui.button(label="承認する", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, i, b):
        if i.user.id != self.opponent.id: return await i.response.send_message("対戦相手に指名された人のみ承認できます。", ephemeral=True)
        if get_player_points(self.opponent.id) < self.bet_amount: return await i.response.send_message(f"ポイントが不足しています。このゲームには`{self.bet_amount}pt`必要です。", ephemeral=True)
        await i.response.defer()
        update_player_points(self.host.id, -self.bet_amount); update_player_points(self.opponent.id, -self.bet_amount)
        game = HighLow対戦Game(self.host.id, self.opponent.id, self.bet_amount, i.message.id)
        active_highlow_games[i.message.id] = game
        view = HighLowChoiceView(i.message.id)
        desc = (f"ベット額: `{self.bet_amount}pt`\n現在のカード: **{game.get_card_display()}**\n\n"
                f"<@{self.host.id}> と <@{self.opponent.id}> は、次のカードがハイかローか選んでください。\n"
                f"（ボタンはあなたにしか見えません）")
        embed = create_embed(f"ハイアンドロー対戦！", desc, discord.Color.blue(), "pending")
        await i.message.edit(content=None, embed=embed, view=view); self.stop()
    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel_button(self, i, b):
        if i.user.id != self.host.id: return await i.response.send_message("募集者のみがキャンセルできます。", ephemeral=True)
        await i.response.edit_message(embed=create_embed("キャンセル", f"{self.host.mention}が募集を取り消しました。", color=discord.Color.red(), status="danger"), view=None); self.stop()
    async def on_timeout(self):
        if self.message and not self.is_finished():
            try: await self.message.edit(embed=create_embed("タイムアウト", "この募集は時間切れになりました。", color=discord.Color.orange(), status="warning"), view=None)
            except: pass

class ConnectFourRecruitmentView(discord.ui.View):
    def __init__(self, host: discord.Member, opponent: discord.Member | None):
        super().__init__(timeout=300.0)
        self.host, self.opponent, self.message = host, opponent, None
        if self.opponent is not None: self.bot_match_button.disabled = True
    async def start_game(self, interaction: discord.Interaction, final_opponent: discord.Member):
        for item in self.children: item.disabled = True
        try: await interaction.message.edit(view=self)
        except discord.HTTPException: pass
        game = ConnectFourGame(self.host.id, final_opponent.id)
        game.channel_id = interaction.channel.id
        game.message_id = interaction.message.id
        active_connectfour_games[interaction.message.id] = game
        embed = create_connectfour_embed(game)
        game_message = await interaction.message.edit(content=None, embed=embed, view=None)
        if not bot.user.id in game.players.values():
            game.afk_task = asyncio.create_task(connectfour_afk_timeout(game))
        if game.get_current_player_id() == bot.user.id:
            asyncio.create_task(self.trigger_bot_turn(game_message, game))
        else:  
            for i in range(COLS):
                await game_message.add_reaction(CONNECTFOUR_MARKERS[i])
        self.stop()
    async def trigger_bot_turn(self, message: discord.Message, game: ConnectFourGame):
        """Botのターンを非同期で実行する (AI強化・バグ修正版)"""
        await asyncio.sleep(random.uniform(0.8, 1.5))
        bot_col = get_connectfour_bot_move(game)   
        if bot_col != -1:
            game.drop_token(bot_col) 
            if game.check_win():
                await send_connectfour_result_message(message.channel, game, message, "normal")
                return     
            if game.is_board_full():
                await send_connectfour_result_message(message.channel, game, message, "draw")
                return        
            game.switch_player()       
        await update_cf_board_and_reactions(message, game)
    @discord.ui.button(label="承認する", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, i, b):
        if (self.opponent and i.user.id != self.opponent.id) or (not self.opponent and i.user.id == self.host.id):
            return await i.response.send_message("この操作は許可されていません。", ephemeral=True)
        await i.response.defer(); await self.start_game(i, i.user)
    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel_button(self, i, b):
        if i.user.id != self.host.id: return await i.response.send_message("募集者のみがキャンセルできます。", ephemeral=True)
        await i.response.edit_message(embed=create_embed("キャンセル", f"{self.host.mention}が募集を取り消しました。", color=discord.Color.red(), status="danger"), view=None); self.stop()
    @discord.ui.button(label="Botと対戦", style=discord.ButtonStyle.secondary)
    async def bot_match_button(self, i, b):
        if i.user.id != self.host.id: return await i.response.send_message("募集者のみがBotと対戦を開始できます。", ephemeral=True)
        await i.response.defer(); await self.start_game(i, bot.user)
    async def on_timeout(self):
        if self.message and not self.is_finished():
            try: await self.message.edit(embed=create_embed("タイムアウト", "この募集は時間切れになりました。", color=discord.Color.orange(), status="warning"), view=None)
            except: pass

# --- API & Other Helpers ---
async def load_weather_city_codes():
    global weather_city_id_map
    if os.path.exists(WEATHER_CITY_CODES_FILE_PATH):
        try:
            with open(WEATHER_CITY_CODES_FILE_PATH, 'r', encoding='utf-8') as f: weather_city_id_map = json.load(f)
            if weather_city_id_map: print(f"Loaded {len(weather_city_id_map)} weather city codes from local cache."); return
        except Exception as e: print(f"Error loading cached city codes: {e}")
    print("Fetching weather city codes from API...")
    try:
        async with aiohttp.ClientSession() as session, session.get(PRIMARY_AREA_XML_URL) as response:
            if response.status == 200:
                xml_text = await response.text(); root = ET.fromstring(xml_text); temp_map = {}
                for pref in root.findall('.//pref'):
                    for city in pref.findall('.//city'):
                        city_title, city_id = city.get('title'), city.get('id')
                        if city_title and city_id:
                            temp_map[city_title] = city_id
                            if (pref_title := pref.get('title')) and pref_title != city_title:
                                temp_map[f"{pref_title}{city_title}"] = city_id
                weather_city_id_map = temp_map
                with open(WEATHER_CITY_CODES_FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(weather_city_id_map, f, ensure_ascii=False, indent=2)
                print(f"Fetched and cached {len(weather_city_id_map)} city codes.")
            else: print(f"Failed to fetch city codes: HTTP {response.status}")
    except Exception as e: print(f"Error fetching city codes: {e}")

async def _resize_image_if_too_large(image_fp: io.BytesIO, target_format: str, max_size_bytes: int = MAX_FILE_SIZE_BYTES, min_dimension: int = MIN_IMAGE_DIMENSION, initial_aggressiveness: float = 0.9, subsequent_resize_factor: float = 0.85, max_iterations: int = 7) -> tuple[io.BytesIO | None, bool]:
    image_fp.seek(0, io.SEEK_END); current_size = image_fp.tell(); image_fp.seek(0)
    if current_size <= max_size_bytes: return image_fp, False
    current_fp, resized = image_fp, False
    for iteration in range(max_iterations):
        current_fp.seek(0)
        try:
            img = Image.open(current_fp)
            w, h = img.width, img.height
            if min(w, h) <= min_dimension: break
            current_fp.seek(0, io.SEEK_END); iter_size = current_fp.tell(); current_fp.seek(0)
            factor = subsequent_resize_factor
            if iteration == 0 and iter_size > max_size_bytes:
                factor = max(0.1, min(math.sqrt(max_size_bytes / iter_size) * initial_aggressiveness, 0.95))
            new_w, new_h = int(w * factor), int(h * factor)
            if new_w < min_dimension or new_h < min_dimension:
                ratio = w / h if h != 0 else 1
                if new_w < min_dimension: new_w, new_h = min_dimension, int(min_dimension / ratio)
                else: new_w, new_h = int(min_dimension * ratio), min_dimension
                if new_w >= w and new_h >= h: break
            output_fp = io.BytesIO()
            if target_format.upper() == 'GIF':
                frames, durations, loop = [], [], img.info.get('loop', 0)
                try:
                    while True:
                        frame = img.copy().convert("RGBA"); frame.thumbnail((new_w, new_h), Image.Resampling.LANCZOS)
                        frames.append(frame); durations.append(img.info.get('duration', 100)); img.seek(img.tell() + 1)
                except EOFError: pass
                if frames: frames[0].save(output_fp, format="GIF", save_all=True, append_images=frames[1:], duration=durations, loop=loop, disposal=2, optimize=True)
                else: break
            else:
                resized_img = img.copy(); resized_img.thumbnail((new_w, new_h), Image.Resampling.LANCZOS)
                params = {'optimize': True}
                if target_format.upper() == 'JPEG': params['quality'] = 85
                elif target_format.upper() == 'PNG': params['compress_level'] = 7
                resized_img.save(output_fp, format=target_format.upper(), **params)
            output_fp.seek(0, io.SEEK_END); new_size = output_fp.tell(); output_fp.seek(0)
            if current_fp != image_fp: current_fp.close()
            current_fp, resized = output_fp, True
            if new_size <= max_size_bytes: return current_fp, resized
        except Exception as e: print(f"Error during image resize iteration: {e}"); return image_fp, False
    return current_fp, resized

def _process_and_composite_image(img_bytes: bytes, tmpl_data: dict) -> io.BytesIO | None:
    try:
        base_image = Image.open(io.BytesIO(img_bytes))
        target_w, target_h = tmpl_data['target_size']
        processed = ImageOps.fit(base_image, (target_w, target_h), Image.Resampling.LANCZOS)
        overlay_path = os.path.join(TEMPLATES_BASE_PATH, tmpl_data['name'])
        if not os.path.exists(overlay_path): print(f"Overlay template not found: {overlay_path}"); return None
        overlay = Image.open(overlay_path).convert("RGBA")
        if overlay.size != (target_w, target_h): overlay = overlay.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if processed.mode != 'RGBA': processed = processed.convert('RGBA')
        final = Image.alpha_composite(processed, overlay)
        buf = io.BytesIO(); final.save(buf, "PNG"); buf.seek(0)
        return buf
    except Exception as e: print(f"Error during image compositing: {e}"); return None

def _create_gaming_gif(img_bytes: bytes, duration_ms: int = 50, max_size: tuple = (256, 256)) -> io.BytesIO | None:
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA"); img.thumbnail(max_size, Image.Resampling.LANCZOS)
        frames = []
        for i in range(36):
            h, s, v = img.convert("HSV").split(); h_array = np.array(h, dtype=np.int16)
            shifted_h = Image.fromarray(np.mod(h_array + int((i*10)*(255.0/360.0)), 256).astype(np.uint8), 'L')
            frames.append(Image.merge("HSV", (shifted_h, s, v)).convert("RGBA"))
        buf = io.BytesIO(); frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=duration_ms, loop=0, disposal=2, optimize=True)
        buf.seek(0); return buf
    except Exception as e: print(f"Error creating gaming GIF: {e}"); traceback.print_exc(); return None

async def generate_gemini_text_response(prompt_parts: list) -> str:
    if not gemini_text_model_instance or GEMINI_API_UNAVAILABLE: return "Error: Gemini Text API is not available."
    try:
        response = await asyncio.to_thread(gemini_text_model_instance.generate_content, prompt_parts, request_options={'timeout': 120})
        if hasattr(response, 'text') and response.text: return response.text
        if response.candidates and response.candidates[0].finish_reason: return f"Could not generate response. Reason: {response.candidates[0].finish_reason.name}"
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason: return f"Prompt blocked. Reason: {response.prompt_feedback.block_reason.name}"
        print(f"Unexpected Gemini text response format: {response}"); return "Could not generate response. Unexpected format."
    except Exception as e: print(f"Gemini Text API Error: {type(e).__name__} - {e}"); traceback.print_exc(); return f"Gemini Text API Error: {type(e).__name__} - {e}"

async def generate_summary_with_gemini(text: str, num_points: int = 3) -> str:
    prompt = f"以下の文章を日本語で{num_points}個の短い箇条書きに要約してください:\n\n{text}"
    return await generate_gemini_text_response([prompt])

async def generate_voicevox_audio(text_to_speak: str, speaker_id: int, api_key: str) -> io.BytesIO | None:
    if not api_key or api_key == "YOUR_VOICEVOX_API_KEY_PLACEHOLDER": print("VoiceVox API key not configured."); return None
    params = {"text": text_to_speak, "speaker": str(speaker_id), "key": api_key}
    try:
        async with aiohttp.ClientSession() as session, session.get(VOICEVOX_API_BASE_URL, params=params, timeout=60) as r:
            if r.status == 200 and r.content_type in ('audio/wav', 'audio/x-wav'): return io.BytesIO(await r.read())
            else: print(f"VoiceVox API request failed (Status {r.status}): {(await r.text())[:500]}"); return None
    except Exception as e: print(f"Error during VoiceVox API call: {e}"); traceback.print_exc(); return None

async def process_audio_with_rvc(ctx: commands.Context, status_message: discord.Message, audio_bytes_io: io.BytesIO, original_filename_base: str, input_file_extension: str):
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes_io.getvalue()), format=input_file_extension)
        if len(audio) > 45000:
            await status_message.edit(embed=create_embed("エラー", f"音声が長すぎます ({len(audio)/1000:.1f}秒)。45秒以下の音声にしてください。", discord.Color.orange(), "warning")); return False
    except Exception as e: 
        await status_message.edit(embed=create_embed("エラー", f"音声ファイルの長さ確認中に問題が発生: {e}", discord.Color.red(), "danger")); return False
    finally: audio_bytes_io.seek(0)
    rvc_script = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    rvc_model = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    if not all(os.path.exists(p) for p in [rvc_script, rvc_model]):
        await status_message.edit(embed=create_embed("内部エラー", "RVC関連ファイルが見つかりません。", discord.Color.red(), "danger")); return False
    await status_message.edit(embed=create_embed("RVC処理中", "やまかわボイチェンで変換しています...\n(目安: 20-50秒)", discord.Color.red(), "pending"))
    unique_id = f"{ctx.author.id}_{ctx.message.id}_{datetime.datetime.now().timestamp()}"
    input_path = os.path.abspath(os.path.join(RVC_INPUT_AUDIO_DIR, f"in_{unique_id}.{input_file_extension}"))
    output_path = os.path.abspath(os.path.join(RVC_OUTPUT_AUDIO_DIR, f"out_{unique_id}.wav"))
    try:
        with open(input_path, 'wb') as f: f.write(audio_bytes_io.getbuffer())
        command = [sys.executable, rvc_script, "--f0up_key", str(RVC_FIXED_TRANSPOSE), "--input_path", input_path, "--opt_path", output_path, "--model_name", RVC_MODEL_NAME_WITH_EXT]
        if os.path.exists(index_path := os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, f"{os.path.splitext(RVC_MODEL_NAME_WITH_EXT)[0]}.index")):
            command.extend(["--feature_path", index_path])
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=RVC_PROJECT_ROOT_PATH)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            print(f"RVC STDERR: {stderr.decode('utf-8', errors='ignore').strip()}")
            await status_message.edit(embed=create_embed("RVCエラー", "音声変換プロセスでエラーが発生しました。", discord.Color.red(), "danger")); return False
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            completed_embed = create_embed("音声変換完了", f"{STATUS_EMOJIS['info']} うまくいかない場合はBGMを抜いてみてください", discord.Color.green(), "success")
            await status_message.edit(embed=completed_embed, attachments=[discord.File(output_path, filename=f"rvc_{original_filename_base}.wav")]); return True
        else: await status_message.edit(embed=create_embed("エラー", "変換は成功しましたが、出力ファイルが見つかりませんでした。", discord.Color.red(), "danger")); return False
    except Exception as e: 
        await status_message.edit(embed=create_embed("予期せぬエラー", "音声変換処理中にエラーが発生しました。", discord.Color.red(), "danger"))
        print(f"Error in RVC process: {e}"); traceback.print_exc(); return False
    finally:
        for p in [input_path, output_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except Exception as e_rem: print(f"Failed to delete temp file {p}: {e_rem}")

# ========================== BACKGROUND TASKS ==========================
@tasks.loop(minutes=5)
async def cleanup_finished_games_task():
    current_time_jst = datetime.datetime.now(JST)
    
    # Othello cleanup
    othello_games_to_remove_ids = []
    for msg_id, game_session_data in list(active_games.items()):
        game_obj = game_session_data.get("game")
        if game_obj and game_obj.game_over and (current_time_jst - game_obj.last_move_time > datetime.timedelta(hours=1)):
            othello_games_to_remove_ids.append(msg_id)
            if game_obj.afk_task and not game_obj.afk_task.done():
                game_obj.afk_task.cancel()
    for msg_id in othello_games_to_remove_ids:
        if msg_id in active_games: del active_games[msg_id]
    if othello_games_to_remove_ids:
        print(f"Cleaned up {len(othello_games_to_remove_ids)} old finished othello games.")

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
                    await game_msg_obj.edit(embed=create_embed("じゃんけん", "このじゃんけんゲームは時間切れにより終了しました。", discord.Color.orange(), "warning"), view=None)
            except Exception as e_clean_msg:
                print(f"Error cleaning up Janken message {msg_id}: {e_clean_msg}")
            del active_janken_games[msg_id]
            print(f"Cleaned up stale Janken game (ID: {msg_id}).")

# ========================== DISCORD EVENTS ==========================
@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name} ({bot.user.id})')
    load_settings(); load_game_points() 
    load_login_bonus_data()
    await load_weather_city_codes()
    print(f"Settings loaded. Allowed channels: {len(allowed_channels)}")
    print(f"Game points loaded for {len(game_points)} players.")
    gemini_status = "Available" if not GEMINI_API_UNAVAILABLE else "Not Available"; print(f"Gemini API Status: {gemini_status}")
    vv_status = "Available" if VOICEVOX_API_KEY and VOICEVOX_API_KEY != "YOUR_VOICEVOX_API_KEY_PLACEHOLDER" else "Not Available"; print(f"VoiceVox API Status: {vv_status}")
    if weather_city_id_map: print(f"Tsukumijima Weather city codes loaded: {len(weather_city_id_map)} cities.")
    else: print("WARNING: Tsukumijima Weather city codes not loaded.")
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands.')
    except Exception as e:
        print(f"Slash command sync failed: {e}")
    
    if not cleanup_finished_games_task.is_running():
        cleanup_finished_games_task.start()
        
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="杉山啓太Bot by(*'▽')"))
    print("Bot is ready and watching.")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot or not message.guild: return
    original_content = message.content
    content_lower_stripped = original_content.strip().lower()
    
    if content_lower_stripped.startswith("setchannel"):
        _content_backup = message.content
        message.content = f"{get_dummy_prefix(bot, message)}setchannel" 
        await bot.process_commands(message)
        message.content = _content_backup; return
        
    if message.channel.id not in allowed_channels: return
    
    command_parts = original_content.split(" ", 1)
    potential_command_name = command_parts[0].lower()
    
    is_othello_subcommand = False
    if potential_command_name == "othello" and len(command_parts) > 1:
        sub_command_parts = command_parts[1].split(" ", 1)
        sub_command_name = sub_command_parts[0].lower()
        if sub_command_name == "leave":
            potential_command_name = "leave"
            is_othello_subcommand = True
        elif sub_command_name in ["point", "points"]:
            potential_command_name = "othello point"
            is_othello_subcommand = True
            
    command_obj = bot.get_command(potential_command_name)
    if command_obj:
        print(f"Prefix-less command '{potential_command_name}' from '{message.author.name}'. Processing...")
        _content_backup_cmd = message.content
        prefix_to_use = get_dummy_prefix(bot, message)
        
        if is_othello_subcommand:
            message.content = f"{prefix_to_use}{potential_command_name}"
        else:
            message.content = f"{prefix_to_use}{original_content}"
            
        print(f"  Modified content: '{message.content}'")
        await bot.process_commands(message)
        message.content = _content_backup_cmd

@bot.event
async def on_error(event, *args, **kwargs):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if isinstance(exc_value, commands.CommandOnCooldown): return
    
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    embed = create_embed(
        f"未捕捉エラー発生: `{event}`",
        f"引数: `{args}`\nキーワード引数: `{kwargs}`\n\n```python\n{tb_text[:1800]}```",
        discord.Color.dark_red(),
        status="danger"
    )

    channel_to_send = None
    for arg in args:
        if isinstance(arg, (discord.Message, discord.Interaction, discord.Reaction)):
            channel_to_send = getattr(arg, 'channel', None) or getattr(arg.message, 'channel', None)
            break

    if channel_to_send:
        try: await channel_to_send.send(embed=embed)
        except Exception as e: print(f"CRITICAL: Failed to send on_error log to Discord channel: {e}")
    else:
        print(f"--- UNHANDLED ERROR (event: {event}) ---")
        traceback.print_exc()
        print("--- (Could not determine which channel to send the error to) ---")
    traceback.print_exc()

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    _, _ = reaction, user
    
    if user == bot.user or user.bot:
        return

    # --- じゃんけんの処理 ---
    if reaction.message.id in active_janken_games:
        game_data = active_janken_games.get(reaction.message.id)
        if game_data and user.id != game_data["host_id"] and game_data.get("game_status") == "opponent_recruiting":
            opponent_hand = EMOJI_TO_HAND.get(str(reaction.emoji))
            if not opponent_hand: return
            original_message = game_data.get("message")
            if not original_message:
                if reaction.message.id in active_janken_games: del active_janken_games[reaction.message.id]
                return
            game_data.update({"opponent_id": user.id, "opponent_hand": opponent_hand, "game_status": "finished"})
            host_id, host_hand = game_data["host_id"], game_data["host_hand"]
            winner_id, loser_id, result_text = None, None, "🤝 引き分け！"
            if (host_hand == "rock" and opponent_hand == "scissors") or (host_hand == "scissors" and opponent_hand == "paper") or (host_hand == "paper" and opponent_hand == "rock"):
                winner_id, loser_id = host_id, user.id
                result_text = f"🏆 <@{host_id}> の勝ち！"
            elif host_hand != opponent_hand:
                winner_id, loser_id = user.id, host_id
                result_text = f"🏆 <@{user.id}> の勝ち！"
            points_text = ""
            if winner_id and loser_id:
                update_player_points(winner_id, JANKEN_WIN_POINTS); update_player_points(loser_id, JANKEN_LOSE_POINTS)
                points_text = f"<@{winner_id}>: `{JANKEN_WIN_POINTS:+d}pt`\n<@{loser_id}>: `{JANKEN_LOSE_POINTS:+d}pt`"
            else:
                update_player_points(host_id, JANKEN_DRAW_POINTS); update_player_points(user.id, JANKEN_DRAW_POINTS)
                points_text = f"<@{host_id}>: `{JANKEN_DRAW_POINTS:+d}pt`\n<@{user.id}>: `{JANKEN_DRAW_POINTS:+d}pt`"
            try:
                await original_message.clear_reactions()
                host_user = await bot.fetch_user(host_id)
                desc = f"{host_user.mention}: {HAND_EMOJIS[host_hand]}\n{user.mention}: {HAND_EMOJIS[opponent_hand]}\n\n**{result_text}**"
                result_embed = create_embed("じゃんけん 結果", desc, discord.Color.gold(), "success")
                result_embed.add_field(name="ポイント変動", value=points_text.strip(), inline=False)
                await original_message.reply(embed=result_embed, mention_author=False)
            except Exception as e: print(f"じゃんけんゲームの終了処理中にエラー: {e}")
            finally:
                if reaction.message.id in active_janken_games: del active_janken_games[reaction.message.id]
        return

    # --- コネクトフォーの処理 ---
    if reaction.message.id in active_connectfour_games:
        game = active_connectfour_games.get(reaction.message.id)
        if not game: return

        if game.afk_task and not game.afk_task.done():
            game.afk_task.cancel()

        if game.game_over or user.id != game.get_current_player_id():
            return
        
        try:
            await reaction.remove(user)
        except discord.HTTPException:
            pass

        try:
            chosen_col = CONNECTFOUR_MARKERS.index(str(reaction.emoji))
        except ValueError:
            return

        if not game.drop_token(chosen_col):
            if not bot.user.id in game.players.values():
                game.afk_task = asyncio.create_task(connectfour_afk_timeout(game))
            return

        if game.check_win() or game.is_board_full():
            await send_connectfour_result_message(reaction.message.channel, game, reaction.message, "normal")
            return

        game.switch_player()
        
        if game.get_current_player_id() == bot.user.id:
            await update_cf_board_and_reactions(reaction.message, game)
            await asyncio.sleep(random.uniform(0.5, 1.2))
            
            bot_col = get_connectfour_bot_move(game)
            if bot_col != -1:
                game.drop_token(bot_col)
            
            if game.check_win() or game.is_board_full():
                await send_connectfour_result_message(reaction.message.channel, game, reaction.message, "normal")
                return
            
            game.switch_player()

        await update_cf_board_and_reactions(reaction.message, game)
        
        if not game.game_over and not bot.user.id in game.players.values():
            game.afk_task = asyncio.create_task(connectfour_afk_timeout(game))
        
        return

    # --- オセロの処理 ---
    if reaction.message.id in active_games:
        game_session = active_games[reaction.message.id]
        game = game_session["game"]
        if game.game_over or user.id != game.get_current_player_id():
            try: await reaction.remove(user)
            except: pass
            return
        chosen_move = next((coord for coord, marker in game.valid_moves_with_markers.items() if str(reaction.emoji) == marker), None)
        try: await reaction.remove(user)
        except: pass
        if chosen_move and game.make_move(chosen_move[0], chosen_move[1], game.current_player):
            if game.afk_task and not game.afk_task.done(): game.afk_task.cancel()
            game.switch_player(); game.check_game_status()
            await reaction.message.edit(embed=create_othello_board_embed(game_session))
            if game.game_over: await send_othello_result_message(reaction.message.channel, game_session, reaction.message)
            else:
                if game.get_current_player_id() == bot.user.id:
                    await update_reactions_for_next_turn(reaction.message, set())
                    asyncio.create_task(make_bot_move(reaction.message, game_session))
                else:
                    await update_reactions_for_next_turn(reaction.message, set(game.valid_moves_with_markers.values()))
                    if not bot.user.id in game.players.values(): game.afk_task = asyncio.create_task(othello_afk_timeout(game))
        return

# ========================== COMMANDS ==========================

@bot.command(name="othello", aliases=["おせろ", "オセロ"])
async def othello_command(ctx: commands.Context, opponent: discord.Member = None):
    host = ctx.author
    if opponent and (opponent == host or (opponent.bot and opponent.id != bot.user.id)):
        msg = "自分自身とは対戦できません。" if opponent == host else "そのBotとは対戦できません。"
        await ctx.send(embed=create_embed("エラー", msg, discord.Color.orange(), "warning"), delete_after=10); return

    for msg_id, game_data in active_games.items():
        game = game_data.get("game")
        if game and not game.game_over:
            players = game.players.values()
            is_host_playing = host.id in players
            is_opponent_playing = opponent and not opponent.bot and opponent.id in players
            if is_host_playing or is_opponent_playing:
                link = f"https://discord.com/channels/{ctx.guild.id}/{game.channel_id}/{msg_id}"
                who = "あなた" if is_host_playing else f"{opponent.display_name}さん"
                await ctx.send(embed=create_embed("エラー", f"{who}は既に参加中のオセロゲームがあります。\n[ゲームへ移動]({link})", discord.Color.orange(), "warning"), delete_after=20); return
    
    desc = f"{host.mention} さん、オセロの盤面サイズを選択してください。\n\n**盤面の大きさでポイント配分が変わります**"
    view = OthelloSizeSelectView(host, opponent)
    await ctx.send(embed=create_embed("オセロ 盤面選択", desc, discord.Color.green(), "info"), view=view)


@bot.command(name="othello point", aliases=["point", "ポイント"])
async def game_points_command(ctx: commands.Context):
    human_players_points = {pid: p for pid, p in game_points.items() if bot.user and int(pid) != bot.user.id}
    points = get_player_points(ctx.author.id)
    sorted_points = sorted(human_players_points.items(), key=lambda item: item[1], reverse=True)
    
    embed = create_embed("ゲームポイントランキング", color=discord.Color.gold(), status="success")
    rank_text = []
    user_rank_info = f"\nあなたの順位: {ctx.author.mention} - {points}pt (ランキング外または未プレイ)"
    user_found = False

    for i, (pid, pval) in enumerate(sorted_points[:10]):
        rank, medal = i + 1, ""
        if rank == 1: medal = "🥇 "
        elif rank == 2: medal = "🥈 "
        elif rank == 3: medal = "🥉 "
        try: user = await bot.fetch_user(int(pid))
        except discord.NotFound: user = None
        user_display = user.mention if user else f"ID:{pid}"
        rank_text.append(f"{medal}{rank}位 {user_display} - {pval}pt")
        if user and user.id == ctx.author.id:
            user_rank_info = f"\nあなたの順位: **{medal}{rank}位** {user.mention} - **{pval}pt**"
            user_found = True
            
    if not rank_text: rank_text.append("まだポイントを持っているプレイヤーがいません。")
    if not user_found and points > 0:
        for i, (pid, pval) in enumerate(sorted_points):
            if int(pid) == ctx.author.id:
                user_rank_info = f"\nあなたの順位: **{i+1}位** {ctx.author.mention} - **{points}pt**"; break
                
    embed.description = "\n".join(rank_text) + user_rank_info
    embed.set_footer(text="このポイントはオセロ・じゃんけん・賭けで共通です。")
    await ctx.send(embed=embed)

@bot.command(name="leave", aliases=["退出","たいしゅつ"])
async def leave_game_command(ctx: commands.Context):
    player_id = ctx.author.id
    game_session, message_id, game_type = None, None, None

    for mid, g_session in active_games.items():
        game_obj = g_session.get("game")
        if game_obj and player_id in game_obj.players.values() and not game_obj.game_over:
            game_session, message_id, game_type = g_session, mid, "othello"
            break
    
    if not game_session:
        for mid, g_session in active_connectfour_games.items():
            if g_session and player_id in g_session.players.values() and not g_session.game_over:
                game_session, message_id, game_type = g_session, mid, "connectfour"
                break
            
    if not game_session:
        await ctx.send(embed=create_embed("エラー", "あなたが参加中のゲームはありません。", color=discord.Color.orange(), status="warning"), delete_after=10); return

    game_obj = game_session if game_type == "connectfour" else game_session.get("game")
    
    class ConfirmLeaveView(discord.ui.View):
        def __init__(self, author, gs, mid, g_type, g_obj):
            super().__init__(timeout=30.0)
            self.author, self.game_session, self.message_id, self.game_type, self.game_obj = author, gs, mid, g_type, g_obj
            self.message = None
            
        @discord.ui.button(label="はい、離脱します", style=discord.ButtonStyle.danger)
        async def confirm(self, i: discord.Interaction, b: discord.ui.Button):
            await i.response.defer()
            channel = bot.get_channel(self.game_obj.channel_id)
            if not channel: return
            
            try:
                board_message = await channel.fetch_message(self.message_id)
                if self.game_type == "othello":
                    self.game_obj.game_over = True
                    setattr(self.game_obj, 'ended_by_action', 'leave')
                    opponent_id = next((pid for pid in self.game_obj.players.values() if pid != self.author.id), None)
                    if opponent_id:
                        self.game_obj.winner = next((color for color, pid in self.game_obj.players.items() if pid == opponent_id), EMPTY)
                    await send_othello_result_message(channel, self.game_session, board_message, "leave")
                
                elif self.game_type == "connectfour":
                    self.game_obj.game_over = True
                    opponent_id = next((pid for pid in self.game_obj.players.values() if pid != self.author.id), None)
                    if opponent_id:
                        self.game_obj.winner = next((token for token, pid in self.game_obj.players.items() if pid == opponent_id), None)
                    await send_connectfour_result_message(channel, self.game_obj, board_message, "leave")
                
                await i.message.delete()
            except discord.NotFound:
                await i.followup.send(embed=create_embed("エラー", "元のゲームメッセージが見つかりませんでした。", color=discord.Color.red(), status="danger"), ephemeral=True)
            self.stop()

        @discord.ui.button(label="いいえ", style=discord.ButtonStyle.secondary)
        async def cancel(self, i: discord.Interaction, b: discord.ui.Button):
            await i.message.delete()
            await i.response.send_message(embed=create_embed("キャンセル", "離脱をキャンセルしました。", color=discord.Color.blue(), status="info"), ephemeral=True, delete_after=5)
            self.stop()
        
        async def on_timeout(self):
            if hasattr(self, 'message') and self.message:
                try: await self.message.delete()
                except: pass

    view = ConfirmLeaveView(ctx.author, game_session, message_id, game_type, game_obj)
    message = await ctx.send(embed=create_embed("確認", f"ゲーム #{game_obj.game_id} を本当に離脱しますか？", color=discord.Color.orange(), status="warning"), view=view)
    view.message = message

@bot.command(name="highlow", aliases=["hl", "ハイロー"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def highlow_command(ctx: commands.Context, bet_amount_str: str, opponent: discord.Member):
    host = ctx.author
    if opponent == host or opponent.bot:
        return await ctx.send(embed=create_embed("エラー", "有効な対戦相手を指定してください。", discord.Color.orange(), "warning"))

    try:
        bet_amount = int(bet_amount_str)
        if bet_amount <= 0:
            return await ctx.send(embed=create_embed("エラー", "ベット額は1以上の整数で指定してください。", discord.Color.orange(), "warning"))
    except ValueError:
        return await ctx.send(embed=create_embed("エラー", "ベット額は有効な数値で入力してください。", discord.Color.orange(), "warning"))

    host_points = get_player_points(host.id)
    if host_points < bet_amount:
        return await ctx.send(embed=create_embed("ポイント不足", f"あなたのポイントが不足しています。({host_points}pt)", discord.Color.orange(), "warning"))

    desc = (f"{host.mention} が <@{opponent.id}> にベット `{bet_amount}pt` でハイアンドロー対戦を申し込みました。\n\n"
            f"承認すると、お互いの所持ポイントから `{bet_amount}pt` が引かれます。")
    embed = create_embed("ハイアンドロー 対戦者募集", desc, discord.Color.purple(), "info")
    view = HighLowRecruitmentView(host, opponent, bet_amount)
    message = await ctx.send(content=opponent.mention, embed=embed, view=view)
    view.message = message

@highlow_command.error
async def highlow_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=create_embed("引数不足", "ベット額と対戦相手を指定してください。\n例: `highlow 100 @ユーザー`", discord.Color.orange(), "warning"))
    else:
        await help_command_error(ctx, error)

@bot.command(name="connectfour", aliases=["cf", "四目並べ","4moku","4nara","よんもく","4目並べ"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def connectfour_command(ctx: commands.Context, opponent: discord.Member = None):
    host = ctx.author
    if opponent and (opponent == host or (opponent.bot and opponent.id != bot.user.id)):
        msg = "自分自身とは対戦できません。" if opponent == host else "そのBotとは対戦できません。"
        await ctx.send(embed=create_embed("エラー", msg, discord.Color.orange(), "warning"), delete_after=10); return
    
    desc = (f"{host.mention} さんがコネクトフォーの対戦相手を募集しています。\n\n"
            f"**ルール:** テトリスのように上からコマを落とし、\n先に自分の色を**縦・横・斜めに4つ**揃えた方の勝ちです。")

    view = ConnectFourRecruitmentView(host, opponent)
    message = await ctx.send(embed=create_embed("コネクトフォー 対戦者募集", desc, discord.Color.blue(), "info"), view=view)
    view.message = message

# ================================== LOGIN BONUS COMMAND ==================================
def get_player_rank(player_id: int) -> int:
    """プレイヤーのポイントランキング順位を取得する。未参加の場合は-1を返す。"""
    human_players_points = {pid: p for pid, p in game_points.items() if int(pid) != bot.user.id}
    if str(player_id) not in human_players_points: return -1
    sorted_players = sorted(human_players_points.items(), key=lambda item: item[1], reverse=True)
    try:
        rank = [p[0] for p in sorted_players].index(str(player_id)) + 1
        return rank
    except ValueError: return -1

def calculate_login_bonus(rank: int, consecutive_days: int) -> int:
    """順位と連続ログイン日数から報酬ポイントを計算する"""
    base_points = 30 
    rank_bonus = 0
    if rank == 1: rank_bonus = 30 
    elif 2 <= rank <= 3: rank_bonus = 20  
    elif 4 <= rank <= 10: rank_bonus = 10  
    consecutive_bonus = (consecutive_days - 1) * 10  
    return max(30, base_points + rank_bonus + consecutive_bonus) 

class LoginBonusView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180.0)
        self.user_id = user_id
        self.message = None
    async def on_timeout(self):
        if self.message:
            for item in self.children: item.disabled = True
            try: await self.message.edit(view=self)
            except: pass
    @discord.ui.button(label="今後のログボ", style=discord.ButtonStyle.secondary, emoji=STATUS_EMOJIS.get("info"))
    async def show_future_bonus(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user.id != self.user_id:
            await i.response.send_message(embed=create_embed("エラー", "コマンドを実行した本人のみ操作できます。", discord.Color.orange(), "warning"), ephemeral=True); return
        await i.response.defer(ephemeral=True)
        user_data = login_bonus_data.get(str(self.user_id), {})
        current_rank = get_player_rank(self.user_id)
        today_str, last_login_str = datetime.datetime.now(JST).strftime("%Y-%m-%d"), user_data.get("last_login", "")
        consecutive_days = user_data.get("consecutive_days", 0)
        start_day = consecutive_days + 1 if last_login_str == today_str else consecutive_days
        embed = create_embed(f"今後のログインボーナス予測", f"現在の順位: `{current_rank if current_rank > 0 else '圏外'}`", discord.Color.teal(), "info")
        future_text = []
        for day_offset in range(1, 8):
            future_consecutive = (start_day + day_offset -1) % 10 or 10
            points = calculate_login_bonus(current_rank, future_consecutive)
            day_text = "明日" if day_offset == 1 else f"{day_offset}日後"
            future_text.append(f"▫️ **{day_text} ({future_consecutive}日目)**: `+{points}pt`")
        embed.add_field(name="今後7日間の報酬", value="\n".join(future_text), inline=False)
        embed.set_footer(text="※順位は毎日変動するため、実際の報酬とは異なる場合があります。")
        await i.followup.send(embed=embed, ephemeral=True)
    async def on_error(self, i: discord.Interaction, e: Exception, item: discord.ui.Item): await send_error_embed(i, e)

@bot.command(name="login", aliases=["bonus", "daily", "ログイン", "ログボ"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def login_bonus_command(ctx: commands.Context):
    user_id_str = str(ctx.author.id)
    today = datetime.datetime.now(JST)
    user_data = login_bonus_data.get(user_id_str, {"last_login": "2000-01-01", "consecutive_days": 0})
    
    if user_data["last_login"] == today.strftime("%Y-%m-%d"):
        desc = f"{STATUS_EMOJIS['warning']} 今日のログインボーナスは既に受け取っています。\n毎日0時にリセットされます。"
        view = LoginBonusView(ctx.author.id)
        message = await ctx.send(embed=create_embed("ログイン済み", desc, discord.Color.orange(), "warning"), view=view)
        view.message = message
        return

    last_login_date = datetime.datetime.strptime(user_data["last_login"], "%Y-%m-%d").date()
    consecutive_days = (user_data["consecutive_days"] % 10) + 1 if last_login_date == today.date() - datetime.timedelta(days=1) else 1
    
    current_rank = get_player_rank(ctx.author.id)
    points_to_add = calculate_login_bonus(current_rank, consecutive_days)
    update_player_points(ctx.author.id, points_to_add)
    
    login_bonus_data[user_id_str] = {"last_login": today.strftime("%Y-%m-%d"), "consecutive_days": consecutive_days}
    save_login_bonus_data()

    desc = (f"{STATUS_EMOJIS['success']} **{consecutive_days}日目**のログインボーナスです！\n"
            f"{STATUS_EMOJIS['pending']} `+{points_to_add}pt` を獲得しました！\n\n"
            "**連続ログイン**や**ランキング順位**でポイントが増減します。")
    embed = create_embed("ログインボーナス", desc, discord.Color.gold(), "success")
    embed.add_field(name="現在のポイント", value=f"`{get_player_points(ctx.author.id)}pt`", inline=True)
    embed.add_field(name="現在の順位", value=f"`{current_rank if current_rank > 0 else '圏外'}`", inline=True)
    
    view = LoginBonusView(ctx.author.id)
    message = await ctx.send(embed=embed, view=view)
    view.message = message

@login_bonus_command.error
async def login_bonus_command_error(ctx, error): await help_command_error(ctx, error) 

# ================================== OTHER COMMANDS ==================================

def is_owner_or_admin():
    async def predicate(ctx):
        if ctx.author.id == 1102557945889300480:
            return True
        if ctx.author.guild_permissions.administrator:
            return True
        return False
    return commands.check(predicate)

@bot.command()
@commands.guild_only()
@is_owner_or_admin() 
async def sync(ctx: commands.Context, guild_id: int = None):
    if guild_id:
        guild = discord.Object(id=guild_id)
    else:
        guild = ctx.guild

    bot.tree.copy_global_to(guild=guild)
    try:
        synced = await bot.tree.sync(guild=guild)
        await ctx.send(f"`{len(synced)}`個のスラッシュコマンドをこのサーバーに同期しました。")
        print(f"Synced {len(synced)} commands to guild {guild.id}")
    except discord.errors.Forbidden as e:
        await ctx.send(f"エラー: Botがこのサーバーでスラッシュコマンドを作成する権限を持っていません。\n`{e}`")
    except Exception as e:
        await ctx.send(f"同期中に予期せぬエラーが発生しました。\n`{e}`")

@bot.command(name="help", aliases=["へるぷ","ヘルプ"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def help_command(ctx: commands.Context):
    embed = create_embed(
        "ヘルプ", 
        "下のボタンを押してコマンド一覧を表示します。",
        discord.Color(0x3498db),
        "info"
    )
    class HelpView(discord.ui.View):
        def __init__(self): super().__init__(timeout=180.0); self.message = None 
        @discord.ui.button(label="コマンド一覧を表示", style=discord.ButtonStyle.primary)
        async def show_commands_button(self, i: discord.Interaction, b: discord.ui.Button):
            cmd_embed = create_embed("杉山啓太Bot コマンド一覧", "", discord.Color(0x3498db), "info")
            cmds = [
                ("`watermark` + [画像]", "画像にウォーターマークを合成します。"), ("`/imakita`", "過去30分のチャットを3行で要約します。(スラッシュコマンド)"),
                ("`5000 [上] [下]`", "「5000兆円欲しい！」画像を生成します。"), ("`gaming` + [画像]", "画像をゲーミング風GIFに変換します。"),
                ("`othello (@相手)`", "オセロをプレイします。"), ("`janken`", "じゃんけんゲームを開始します。"),
                ("`bet [金額]`", "ポイントを賭けてダイスゲームに挑戦します。"), ("`text [文字]`", "やまかわサムネ風の黄色い文字画像を生成します。"),
                ("`text2 [文字]`", "やまかわサムネ風の青い文字画像を生成します。"), ("`text3 [文字]`", "Noto Serifフォントの赤い文字画像を生成します。"),
                ("`voice [文字/音声]`", "テキストまたは音声を変換します。"), ("`ping`", "Botの応答速度を表示します。"),
                ("`tenki [地名]`", "日本の都市の天気予報を表示します。"), ("`info (@相手)`", "ユーザー情報を表示します。"),
                ("`rate [金額] [通貨]`", "外貨を日本円に換算します。"), ("`shorturl [URL]`", "URLを短縮します。"),
                ("`amazon [URL]`", "AmazonのURLを短縮します。"), ("`totusi [文字列]`", "突然の死ジェネレーター。"),
                ("`time (国コード)`", "世界時計。"), ("`help`", "このヘルプを表示します。"),
            ]
            for name, value in cmds: cmd_embed.add_field(name=name, value=value, inline=False)
            font_ok = "✅" if os.path.exists(TEXT_IMAGE_FONT_PATH_DEFAULT) else "❌"; noto_ok = "✅" if os.path.exists(TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD) else "❌"
            cmd_embed.add_field(name="API/Font Status", value=f"Gemini: {'✅' if not GEMINI_API_UNAVAILABLE else '❌'} | VoiceVox: {'✅' if VOICEVOX_API_KEY else '❌'}\nFont(Default): {font_ok} | Font(Noto): {noto_ok}", inline=False)
            await i.response.send_message(embed=cmd_embed, ephemeral=True)
            try: await i.message.delete()
            except: pass; self.stop()
        async def on_timeout(self):
            if self.message:
                for item in self.children: item.disabled = True
                try: await self.message.edit(view=self)
                except: pass
        async def on_error(self, i: discord.Interaction, e: Exception, item: discord.ui.Item): await send_error_embed(i, e)
    view = HelpView()
    message = await ctx.send(embed=embed, view=view)
    view.message = message

# imakita
@help_command.error
async def help_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown): 
        await ctx.send(embed=create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending"), delete_after=5)
    else: 
        await send_error_embed(ctx, error)


class ImakitaDetailView(discord.ui.View):
    def __init__(self, original_interaction: discord.Interaction):
        super().__init__(timeout=300.0)
        self.original_interaction = original_interaction
        self.last_pressed = 0
        self.message = None

    async def fetch_and_summarize(self, interaction: discord.Interaction, time_deltas, title):
        current_time = datetime.datetime.now().timestamp()
        if current_time - self.last_pressed < 30:
            await interaction.response.send_message("現在読み込み中です。もう少々お待ちください。", ephemeral=True, delete_after=10)
            return
        self.last_pressed = current_time

        await interaction.response.defer(ephemeral=True)

        now = discord.utils.utcnow()
        full_summary = ""

        for start_minutes, end_minutes in time_deltas:
            after_time = now - datetime.timedelta(minutes=start_minutes)
            before_time = now - datetime.timedelta(minutes=end_minutes)
            
            history = [
                f"<@{m.author.id}>: {m.clean_content}"
                async for m in self.original_interaction.channel.history(limit=200, before=before_time, after=after_time)
                if m.author != bot.user and not m.author.bot and m.clean_content
            ]
            
            if not history:
                continue

            prompt = (
                "以下のDiscordのチャット履歴を、重要な点を【最大3つ】の短い箇条書きで要約してください。"
                "ユーザー名は<@ユーザーID>の形式になっています。そのまま出力に含めてください。"
                "「以下に要約します」のような前置きは絶対に含めないでください。\n\n"
                "--- 履歴 ---\n"
                + "\n".join(reversed(history))
            )
            summary_text = await generate_gemini_text_response([prompt])
            
            if not summary_text.startswith("Error:") and not summary_text.startswith("Could not"):
                time_range_str = f"{start_minutes}～{end_minutes}分前"
                full_summary += f"### {time_range_str}\n{summary_text}\n\n"

        if not full_summary:
            full_summary = "詳細な要約を生成できるメッセージがありませんでした。"

        embed = create_embed(title, full_summary, discord.Color.blue(), "info", "Gemini")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="さらに詳しく", style=discord.ButtonStyle.primary)
    async def detail_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        time_deltas = [
            (30, 15), (15, 10), (10, 5), (5, 0) 
        ]
        await self.fetch_and_summarize(interaction, time_deltas, "詳細な要約（過去30分）")
        button.disabled = True
        if self.message:
            await self.message.edit(view=self)

@bot.tree.command(name="imakita", description="過去30分のチャットを3行で要約します。")
async def imakita_slash_command(interaction: discord.Interaction):
    global imakita_request_timestamps

    current_time = datetime.datetime.now().timestamp()
    while imakita_request_timestamps and imakita_request_timestamps[0] < current_time - IMAKITA_RATE_LIMIT_SECONDS:
        imakita_request_timestamps.popleft()

    if len(imakita_request_timestamps) >= IMAKITA_RATE_LIMIT_COUNT:
        return await interaction.response.send_message(
            f"APIリクエストが集中しています。しばらくお待ちください。(あと約 {int(IMAKITA_RATE_LIMIT_SECONDS - (current_time - imakita_request_timestamps[0]))}秒)",
            ephemeral=True
        )

    await interaction.response.defer(ephemeral=True, thinking=True)
    imakita_request_timestamps.append(current_time)

    if not hasattr(interaction.channel, 'history'):
        return await interaction.followup.send("このチャンネルではメッセージ履歴を取得できません。", ephemeral=True)

    after_time = discord.utils.utcnow() - datetime.timedelta(minutes=30)
    
    history = [
        f"<@{m.author.id}>: {m.clean_content}"
        async for m in interaction.channel.history(limit=200, after=after_time)
        if m.author != bot.user and not m.author.bot and m.clean_content
    ]

    if not history:
        return await interaction.followup.send("過去30分にメッセージはありませんでした。", ephemeral=True)

    prompt = (
        "以下のDiscordのチャット履歴を、重要な点を3つの短い箇条書きで要約してください。"
        "ユーザー名は<@ユーザーID>の形式になっています。そのまま出力に含めてください。"
        "「以下に要約します」のような前置きは不要です。\n\n"
        "--- 履歴 ---\n"
        + "\n".join(reversed(history))
    )
    summary = await generate_gemini_text_response([prompt])
    

    if summary.startswith("Error:") or summary.startswith("Could not"):
        embed = create_embed("要約エラー", summary, discord.Color.red(), "danger", "Gemini")
        return await interaction.followup.send(embed=embed, ephemeral=True)

    embed = create_embed("今北産業（過去30分）", summary, discord.Color.green(), "success", "Gemini")
    view = ImakitaDetailView(interaction)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    view.message = await interaction.original_response()

@bot.command(name="setchannel")
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.guild)
async def setchannel_command(ctx: commands.Context):
    cid = ctx.channel.id
    if cid in allowed_channels:
        allowed_channels.remove(cid)
        desc, color, status = f"このチャンネル <#{cid}> でのコマンド利用を**禁止**しました。", discord.Color.red(), "danger"
    else:
        allowed_channels.add(cid)
        desc, color, status = f"このチャンネル <#{cid}> でのコマンド利用を**許可**しました。", discord.Color.green(), "success"
    save_settings()
    await ctx.send(embed=create_embed("設定変更完了", desc, color, status))

@setchannel_command.error
async def setchannel_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions): await ctx.send(embed=create_embed("権限エラー", "このコマンドを実行するには管理者権限が必要です。", discord.Color.red(), "danger"))
    else: await send_error_embed(ctx, error)

@bot.command(name="watermark", aliases=["ウォーターマーク","うぉーたーまーく"])
@commands.cooldown(1, 15, commands.BucketType.user)
async def watermark_command(ctx: commands.Context):
    if not ctx.message.attachments or not ctx.message.attachments[0].content_type.startswith("image/"):
        await ctx.send(embed=create_embed("引数エラー", "画像を添付してください。", discord.Color.orange(), "warning")); return
    attachment = ctx.message.attachments[0]
    async with ctx.typing():
        image_bytes = await attachment.read()
        try:
            uw, uh = Image.open(io.BytesIO(image_bytes)).size
            if uw == 0 or uh == 0: await ctx.send(embed=create_embed("エラー", "無効な画像サイズです。", discord.Color.orange(), "warning")); return
            uploaded_ratio = uw / uh if uh != 0 else 0
        except Exception as e: await send_error_embed(ctx, e); return
        valid_templates = [t for t in TEMPLATES_DATA if 'match_ratio_wh' in t and os.path.exists(os.path.join(TEMPLATES_BASE_PATH, t['name']))]
        if not valid_templates: await ctx.send(embed=create_embed("エラー", "利用可能なテンプレートが見つかりませんでした。", discord.Color.orange(), "warning")); return
        valid_templates.sort(key=lambda t: abs(t['match_ratio_wh'] - uploaded_ratio))
        candidates = valid_templates[:min(4, len(valid_templates))]
        if not candidates: await ctx.send(embed=create_embed("エラー", "アスペクト比の近いテンプレートが見つかりませんでした。", discord.Color.orange(), "warning")); return
        selected = random.choice(candidates)
        processed_io = await asyncio.to_thread(_process_and_composite_image, image_bytes, selected)
        if processed_io:
            final_io, resized = await _resize_image_if_too_large(processed_io, "PNG")
            if final_io:
                file = discord.File(fp=final_io, filename=f"wm_{os.path.splitext(attachment.filename)[0]}.png")
                embed = create_embed("ウォーターマーク加工完了", f"使用テンプレート: `{selected['name']}`{' (リサイズ済)' if resized else ''}", discord.Color.blue(), "success")
                embed.set_image(url=f"attachment://{file.filename}")
                await ctx.send(embed=embed, file=file)
                if processed_io != final_io: processed_io.close()
                final_io.close()
            else: await ctx.send(embed=create_embed("エラー", "画像の最終処理に失敗しました。", discord.Color.red(), "danger"))
        else: await ctx.send(embed=create_embed("エラー", "画像の加工に失敗しました。", discord.Color.red(), "danger"))

@bot.command(name="5000", aliases=["5000兆円"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def five_k_choyen_command(ctx: commands.Context, top_text: str, bottom_text: str, *options: str):
    params = {"top": top_text, "bottom": bottom_text, "hoshii": "true" if "hoshii" in options else "false", "rainbow": "true" if "rainbow" in options else "false"}
    url = f"https://gsapi.cbrx.io/image?{urllib.parse.urlencode(params)}"
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as s, s.get(url) as r:
                if r.status == 200:
                    embed = create_embed("5000兆円欲しい！", "", discord.Color.gold(), "success", "5000choyen-api")
                    embed.set_image(url=url); await ctx.send(embed=embed)
                else: await ctx.send(embed=create_embed("エラー", f"画像生成に失敗しました。(APIステータス: {r.status})", discord.Color.red(), "danger", "5000choyen-api"))
        except Exception as e: await send_error_embed(ctx, e)

@five_k_choyen_command.error
async def five_k_choyen_error(ctx, e):
    if isinstance(e, commands.MissingRequiredArgument): await ctx.send(embed=create_embed("引数不足", "引数が不足しています。\n例: `5000 上の文字 下の文字`", discord.Color.orange(), "warning"))
    else: await help_command_error(ctx, e) 

@bot.command(name="gaming", aliases=["ゲーミング","げーみんぐ"])
@commands.cooldown(1, 15, commands.BucketType.user)
async def gaming_command(ctx: commands.Context):
    if not ctx.message.attachments or not ctx.message.attachments[0].content_type.startswith("image/"):
        await ctx.send(embed=create_embed("エラー", "画像を添付してください。", discord.Color.orange(), "warning")); return
    attachment = ctx.message.attachments[0]
    async with ctx.typing():
        gif_io = await asyncio.to_thread(_create_gaming_gif, await attachment.read())
        if gif_io:
            final_io, resized = await _resize_image_if_too_large(gif_io, "GIF")
            if final_io:
                file = discord.File(fp=final_io, filename=f"gaming_{os.path.splitext(attachment.filename)[0]}.gif")
                embed = create_embed("ゲーミングGIF生成完了", f"うまくいかない場合は、カラー画像を添付してください。{' (リサイズ済)' if resized else ''}", discord.Color.purple(), "success")
                embed.set_image(url=f"attachment://{file.filename}")
                await ctx.send(embed=embed, file=file)
                if gif_io != final_io: gif_io.close()
                final_io.close()
            else: await ctx.send(embed=create_embed("エラー", "画像の最終処理に失敗しました。", discord.Color.red(), "danger"))
        else: await ctx.send(embed=create_embed("エラー", "ゲーミングGIFの生成に失敗しました。", discord.Color.red(), "danger"))

# # VOICE COMMAND
@bot.command(name="voice", aliases=["ボイス", "ぼいす", "ボイチェン"])
@commands.cooldown(1, 20, commands.BucketType.user)
async def rvc_voice_convert_command(ctx: commands.Context, *, text_input: str = None):
    allowed_guild_ids = {1355073968532619376, 1369344086326116453}
    if ctx.guild.id not in allowed_guild_ids:
        await ctx.send(embed=create_embed("コマンド利用不可", "このサーバーではこのコマンドは使えません。", discord.Color.red(), "danger"))
        return

    if not ctx.message.attachments and not text_input:
        await ctx.send(embed=create_embed("引数エラー", "音声ファイルを添付するか、変換したいテキストを入力してください。\n例: `voice こんにちは`", discord.Color.orange(), "warning")); return

    status_message = await ctx.reply(embed=create_embed("処理開始", "音声処理を開始します...", discord.Color.light_grey(), "pending"), mention_author=False)
    
    audio_bytes_io, original_filename_base, input_file_extension = None, "text_to_speech", "wav"

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not (attachment.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a'))):
            await status_message.edit(embed=create_embed("エラー", "対応している音声ファイル形式は `.wav`, `.mp3`, `.flac`, `.m4a` です。", discord.Color.orange(), "warning")); return
        audio_bytes_io = io.BytesIO(await attachment.read())
        original_filename_base, ext = os.path.splitext(attachment.filename)
        input_file_extension = ext.lstrip('.').lower()
    elif text_input:
        if not VOICEVOX_API_KEY:
            await status_message.edit(embed=create_embed("APIエラー", "テキストからの音声変換機能は現在利用できません。", discord.Color.red(), "danger")); return
        
        await status_message.edit(embed=create_embed("音声生成中...", f"「{text_input[:30]}{'...' if len(text_input)>30 else ''}」をVoiceVoxで音声生成中...", discord.Color.green(), "pending", "VoiceVox API"))
        generated_audio_stream = await generate_voicevox_audio(text_input, VOICEVOX_SPEAKER_ID, VOICEVOX_API_KEY)
        if generated_audio_stream:
            audio_bytes_io = generated_audio_stream
        else:
            await status_message.edit(embed=create_embed("APIエラー", "VoiceVoxでの音声生成に失敗しました。\nAPIエラーか、テキストが長すぎる可能性があります。", discord.Color.red(), "danger", "VoiceVox API")); return
    
    if audio_bytes_io and audio_bytes_io.getbuffer().nbytes > 0:
        await process_audio_with_rvc(ctx, status_message, audio_bytes_io, original_filename_base, input_file_extension)
    else:
        await status_message.edit(embed=create_embed("エラー", "音声データの準備に失敗しました。", discord.Color.red(), "danger"))
    
    if audio_bytes_io: audio_bytes_io.close()

# # PING COMMAND
@bot.command(name="ping", aliases=["ピング","接続速度","ぴんぐ"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def ping_command(ctx: commands.Context):
    await ctx.send(embed=create_embed("Ping", f"現在の応答速度: **{bot.latency * 1000:.2f}ms**", discord.Color.green(), "success"))

@ping_command.error
async def ping_command_error(ctx, error): await help_command_error(ctx, error) 

@bot.command(name="tenki", aliases=["weather","てんき","天気","テンキ"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def tenki_command(ctx: commands.Context, *, city_name_query: str):
    async with ctx.typing():
        city_id = None
        if not weather_city_id_map: await load_weather_city_codes()
        query_lower = city_name_query.lower()
        city_id = next((cid for name, cid in weather_city_id_map.items() if query_lower == name.lower()), None)
        
        if not city_id and not GEMINI_API_UNAVAILABLE:
            city_list_excerpt = "\n".join([f"- {name} (ID: {cid})" for name, cid in list(weather_city_id_map.items())[:150]])
            prompt_gemini = (f"日本の地名「{city_name_query}」に最も近いと思われる都市のIDを、以下のリストから一つだけ選んで、そのID（数字6桁）のみを返してください。\n"
                           f"日本の地名ではない、またはリストから適切なIDが見つからない場合は「不明」とだけ返してください。\nリストは:\n{city_list_excerpt}\n\n"
                           f"ユーザー入力地名: {city_name_query}\n最も近いID:")
            id_response_gemini = await generate_gemini_text_response([prompt_gemini])
            if id_response_gemini.strip().isdigit() and any(cid == id_response_gemini.strip() for cid in weather_city_id_map.values()):
                city_id = id_response_gemini.strip(); print(f"Weather: Gemini suggested City ID for '{city_name_query}': {city_id}")
        
        if not city_id:
            await ctx.send(embed=create_embed("エラー", f"都市「{city_name_query}」が見つかりませんでした。\nこのコマンドは日本国内の地名のみ利用可能です。", discord.Color.orange(), "warning")); return

        try:
            async with aiohttp.ClientSession() as s, s.get(f"{WEATHER_API_BASE_URL}{city_id}") as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("error"): await ctx.send(embed=create_embed("APIエラー", data.get("error"), discord.Color.red(), "danger", "つくもAPI")); return
                    if data.get("forecasts"):
                        embed = create_embed(f"{data.get('location', {}).get('city', city_name_query)} の天気予報", "", discord.Color.blue(), "success", "つくもAPI")
                        for forecast in data["forecasts"][:3]:
                            date = f"{forecast.get('dateLabel', '不明')} ({forecast.get('date')[-5:]})"
                            temp_max = forecast.get("temperature", {}).get("max", {}).get("celsius", "--")
                            temp_min = forecast.get("temperature", {}).get("min", {}).get("celsius", "--")
                            value_str = f"{forecast.get('telop', '情報なし')} (最高:{temp_max}°C / 最低:{temp_min}°C)"
                            embed.add_field(name=date, value=value_str, inline=False)
                        await ctx.send(embed=embed)
                    else: await ctx.send(embed=create_embed("エラー", f"「{city_name_query}」(ID:{city_id}) の天気予報データを取得できませんでした。", discord.Color.orange(), "warning", "つくもAPI"))
                else: await ctx.send(embed=create_embed("APIエラー", f"天気情報の取得に失敗しました。(HTTP: {r.status})", discord.Color.red(), "danger", "つくもAPI"))
        except Exception as e: await send_error_embed(ctx, e)

@tenki_command.error
async def tenki_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument): await ctx.send(embed=create_embed("引数不足", "都市名を指定してください。\n例: `tenki 東京`", discord.Color.orange(), "warning"))
    else: await help_command_error(ctx, error)

@bot.command(name="info",aliases=["詳細", "いんふぉ"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def info_command(ctx: commands.Context, member: discord.Member = None):
    target = member or ctx.author
    embed = create_embed(f"{target.display_name} の情報", "", target.color or discord.Color.default(), "info")
    if target.avatar: embed.set_thumbnail(url=target.avatar.url)
    embed.add_field(name="ユーザー名", value=f"`{target.name}`", inline=True)
    embed.add_field(name="ユーザーID", value=f"`{target.id}`", inline=True)
    embed.add_field(name="Bot?", value="はい" if target.bot else "いいえ", inline=True)
    embed.add_field(name="アカウント作成日", value=f"<t:{int(target.created_at.timestamp())}:D>", inline=True)
    if isinstance(target, discord.Member) and target.joined_at:
        embed.add_field(name="サーバー参加日", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
    
    badges = []
    flags = target.public_flags
    
    if flags.staff: badges.append(USER_BADGES_EMOJI.get('staff'))
    if flags.partner: badges.append(USER_BADGES_EMOJI.get('partner'))
    if flags.hypesquad: badges.append(USER_BADGES_EMOJI.get('hypesquad'))
    if flags.hypesquad_bravery: badges.append(USER_BADGES_EMOJI.get('hypesquad_bravery'))
    if flags.hypesquad_brilliance: badges.append(USER_BADGES_EMOJI.get('hypesquad_brilliance'))
    if flags.hypesquad_balance: badges.append(USER_BADGES_EMOJI.get('hypesquad_balance'))
    if flags.bug_hunter: badges.append(USER_BADGES_EMOJI.get('bug_hunter'))
    if flags.bug_hunter_level_2: badges.append(USER_BADGES_EMOJI.get('bug_hunter_level_2'))
    if flags.early_supporter: badges.append(USER_BADGES_EMOJI.get('early_supporter'))
    if flags.early_verified_bot_developer: badges.append(USER_BADGES_EMOJI.get('early_verified_bot_developer'))
    if flags.verified_bot_developer: badges.append(USER_BADGES_EMOJI.get('verified_bot_developer'))
    if flags.discord_certified_moderator: badges.append(USER_BADGES_EMOJI.get('discord_certified_moderator'))
    if flags.active_developer: badges.append(USER_BADGES_EMOJI.get('active_developer'))
    
    if isinstance(target, discord.Member):
        if target.premium_since:
            badges.append(USER_BADGES_EMOJI.get('booster'))
        
        if target.avatar and target.avatar.is_animated():
             badges.append(USER_BADGES_EMOJI.get('nitro'))
        elif target.banner:
             badges.append(USER_BADGES_EMOJI.get('nitro'))


    if badges:
        unique_badges = []
        for b in badges:
            if b and b not in unique_badges:
                unique_badges.append(b)
        if unique_badges:
            embed.add_field(name="バッジ", value=" ".join(unique_badges), inline=False)
    
    if isinstance(target, discord.Member):
        roles = [r.mention for r in sorted(target.roles, key=lambda r: r.position, reverse=True) if r.name != "@everyone"]
        if roles:
            roles_str = " ".join(roles)
            embed.add_field(name=f"ロール ({len(roles)})", value=roles_str[:1020] + "..." if len(roles_str) > 1024 else roles_str, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="rate",aliases=["レート", "れーと","為替"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def rate_command(ctx: commands.Context, amount_str: str, currency_code: str):
    try: amount = float(amount_str)
    except ValueError: await ctx.send(embed=create_embed("入力エラー", "金額は有効な数値で入力してください。", discord.Color.orange(), "warning")); return
    
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as s, s.get(EXCHANGE_RATE_API_URL) as r:
                if r.status == 200:
                    data = await r.json()
                    target_rate_key = f"{currency_code.upper()}_JPY"
                    if target_rate_key in data and isinstance(data[target_rate_key], (int, float)):
                        rate, jpy = data[target_rate_key], amount * data[target_rate_key]
                        time_str = data.get('datetime', '')
                        try: time_str = datetime.datetime.fromisoformat(time_str.replace("Z", "+00:00")).astimezone(JST).strftime('%Y-%m-%d %H:%M') + " JST"
                        except: pass
                        desc = f"**{amount:,.2f} {currency_code.upper()}** は **{jpy:,.2f} 円**です。\n(レート: 1 {currency_code.upper()} = {rate:,.3f} JPY | {time_str}時点)"
                        await ctx.send(embed=create_embed("為替レート変換", desc, discord.Color.gold(), "success", "exchange-rate-api.krnk.org"))
                    else:
                        available = sorted([k.split('_')[0] for k,v in data.items() if k.endswith("_JPY") and isinstance(v,(int,float))])
                        await ctx.send(embed=create_embed("エラー", f"通貨「{currency_code.upper()}」のレートが見つかりません。\n利用可能(対JPY): `{', '.join(available[:15])}...`", discord.Color.orange(), "warning", "exchange-rate-api.krnk.org"))
                else: await ctx.send(embed=create_embed("APIエラー", f"為替レートAPIへのアクセスに失敗しました (HTTP: {r.status})", discord.Color.red(), "danger", "exchange-rate-api.krnk.org"))
        except Exception as e: await send_error_embed(ctx, e)

@rate_command.error
async def rate_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument): await ctx.send(embed=create_embed("引数不足", "金額と通貨コードを指定してください。\n例: `rate 100 USD`", discord.Color.orange(), "warning"))
    else: await help_command_error(ctx, error)

@bot.command(name="shorturl", aliases=["short","たんしゅく","短縮","タンシュク"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def shorturl_command(ctx: commands.Context, *, url_to_shorten: str):
    if not (url_to_shorten.startswith("http://") or url_to_shorten.startswith("https://")): url_to_shorten = "http://" + url_to_shorten
    params = {"url": url_to_shorten}
    if SHORTURL_API_KEY and SHORTURL_API_KEY != "YOUR_XGD_API_KEY_PLACEHOLDER": params["key"] = SHORTURL_API_KEY
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as s, s.get(f"{SHORTURL_API_ENDPOINT}?{urllib.parse.urlencode(params)}") as r:
                response_text = await r.text()
                if r.status == 200:
                    short_url = None
                    try:
                        data = json.loads(response_text)
                        if isinstance(data, dict) and data.get("status") == 200 and data.get("shorturl"): short_url = data['shorturl']
                    except json.JSONDecodeError:
                        if response_text.startswith("https://x.gd/") or response_text.startswith("http://x.gd/"): short_url = response_text
                    if short_url: await ctx.send(embed=create_embed("短縮URLを生成しました", f"```{short_url}```", discord.Color.teal(), "success", "x.gd"))
                    else: await ctx.send(embed=create_embed("エラー", f"URLの短縮に失敗しました。\nAPI応答: `{response_text[:200]}`", discord.Color.orange(), "warning", "x.gd"))
                else: await ctx.send(embed=create_embed("APIエラー", f"URL短縮APIへのアクセスに失敗しました (HTTP: {r.status})。", discord.Color.red(), "danger", "x.gd"))
        except Exception as e: await send_error_embed(ctx, e)

@shorturl_command.error
async def shorturl_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument): await ctx.send(embed=create_embed("引数不足", "短縮したいURLを指定してください。\n例: `shorturl https://google.com`", discord.Color.orange(), "warning"))
    else: await help_command_error(ctx, error)

@bot.command(name="amazon")
@commands.cooldown(1, 5, commands.BucketType.user)
async def amazon_command(ctx: commands.Context, *, amazon_url: str):
    parsed_url = urllib.parse.urlparse(amazon_url)
    if not (parsed_url.scheme in ["http", "https"] and any(domain in parsed_url.netloc for domain in ["amazon.co.jp", "amzn.asia", "amazon.com"])):
        await ctx.send(embed=create_embed("URLエラー", "有効なAmazonのURLを指定してください。", discord.Color.orange(), "warning")); return
    marketplace_id = "6" if "amazon.co.jp" in parsed_url.netloc else "1"
    params = { "longUrl": urllib.parse.quote_plus(amazon_url), "marketplaceId": marketplace_id }
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as s, s.get(f"{AMAZON_SHORTURL_ENDPOINT}?{urllib.parse.urlencode(params, safe='/:')}", headers={ "User-Agent": "Mozilla/5.0" }) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("isOk") and data.get("shortUrl"):
                        await ctx.send(embed=create_embed("Amazon短縮URLを生成しました", f"```{data['shortUrl']}```", discord.Color.from_rgb(255, 153, 0), "success", "Amazon Associates"))
                    else: await ctx.send(embed=create_embed("エラー", f"URLの短縮に失敗しました。\nAPI応答: `{data.get('error', {}).get('message', '不明なエラー')}`", discord.Color.orange(), "warning", "Amazon Associates"))
                else: await ctx.send(embed=create_embed("APIエラー", f"APIへのアクセスに失敗しました (HTTP: {r.status})。", discord.Color.red(), "danger", "Amazon Associates"))
        except Exception as e: await send_error_embed(ctx, e)

@bot.command(name="totusi",aliases=["突然の死", "とつし","突死"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def totusi_command(ctx: commands.Context, *, text: str):
    text_clean = text.replace("　", " ")
    char_display_width = sum(2 if unicodedata.east_asian_width(c) in ('F', 'W', 'A') else 1 for c in text_clean)
    arrow_count = min(15, max(3, math.ceil(char_display_width / 1.5)))
    line1 = "＿" + "人" * arrow_count + "＿"
    line2 = f"＞　**{text_clean}**　＜"
    line3 = "￣" + ("Y^" * (arrow_count // 2)) + ("Y" if arrow_count % 2 != 0 else "") + ("^Y" * (arrow_count//2)) + "￣"
    await ctx.send(embed=create_embed("突然の死", f"{line1}\n{line2}\n{line3}", discord.Color.light_grey(), "success"))

@totusi_command.error
async def totusi_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument): await ctx.send(embed=create_embed("引数不足", "AAにする文字列を指定してください。\n例: `totusi すごい`", discord.Color.orange(), "warning"))
    else: await help_command_error(ctx, error)

@bot.command(name="time",  aliases=["時間", "たいむ", "タイム", "じかん"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def time_command(ctx: commands.Context, country_code: str = None):
    class TimeHelpView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60)
        @discord.ui.button(label="国コード一覧を表示", style=discord.ButtonStyle.secondary)
        async def show_timezones(self, i: discord.Interaction, b: discord.ui.Button):
            help_text = "\n".join([f"`{code}`: {tz.split('/')[-1].replace('_', ' ')}" for code, tz in sorted(TIMEZONE_MAP.items())])
            await i.response.send_message(embed=create_embed("Timeコマンド ヘルプ", f"利用可能な国/地域コード (一部):\n{help_text}", discord.Color.blue(), "info"), ephemeral=True); self.stop()

    if not country_code:
        desc = (f"現在の日本時間は **{datetime.datetime.now(JST).strftime('%H:%M:%S')}** です。\n\n"
                f"{STATUS_EMOJIS['info']} 国コードを指定すると、その国の時刻を表示できます。(例: `time US`)")
        await ctx.send(embed=create_embed("現在時刻 (日本時間)", desc, discord.Color.blue(), "info"), view=TimeHelpView()); return

    target_tz_name = TIMEZONE_MAP.get(country_code.upper())
    if not target_tz_name:
        desc = "利用可能な国コードの一覧は下のボタンから確認できます。"
        await ctx.send(embed=create_embed("無効な国コード", f"`{country_code}` は見つかりませんでした。\n{desc}", discord.Color.orange(), "warning"), view=TimeHelpView()); return
    
    try:
        target_dt = datetime.datetime.now(pytz.timezone(target_tz_name))
        offset_str = f"UTC{target_dt.utcoffset().total_seconds() / 3600:+g}"
        desc = f"**{target_dt.strftime('%Y-%m-%d %H:%M:%S')}** ({offset_str})"
        await ctx.send(embed=create_embed(f"{target_tz_name.split('/')[-1].replace('_', ' ')} の現在時刻", desc, discord.Color.blue(), "success"))
    except Exception as e: await send_error_embed(ctx, e)

@bot.command(name="bet", aliases=["賭け", "かけ", "ベッド", "べっど"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def bet_command(ctx: commands.Context, amount_str: str):
    try:
        amount = int(amount_str)
    except ValueError:
        await ctx.send(embed=create_embed("エラー", "賭け金は整数で指定してください。", discord.Color.orange(), "warning"))
        return

    current_points = get_player_points(ctx.author.id)

    if amount <= 0:
        await ctx.send(embed=create_embed("エラー", "賭け金は1ポイント以上で指定してください。", discord.Color.orange(), "warning"))
        return
    if current_points < amount:
        await ctx.send(embed=create_embed("ポイント不足", f"ポイントが不足しています。\nあなたのポイント: `{current_points}pt`", discord.Color.orange(), "warning"))
        return
    
    async with ctx.typing():
        await asyncio.sleep(random.uniform(0.5, 1.0)) 
        dice_roll = random.randint(1, 6)
        
        message, payout_multiplier = BET_DICE_PAYOUTS[dice_roll]
        points_change = int(amount * payout_multiplier)
        update_player_points(ctx.author.id, points_change)
        
        title = f"ダイスベット結果: {dice_roll}"
        description = f"{ctx.author.mention} が `{amount}pt` をベット！\n\n**結果**\n{message}"
        
        embed = create_embed(title, description, discord.Color.purple(), "info")
        
        embed.add_field(name="ポイント変動", value=f"`{'+' if points_change >=0 else ''}{points_change}pt`", inline=True)
        embed.add_field(name="現在のポイント", value=f"`{get_player_points(ctx.author.id)}pt`", inline=True)
        
        await ctx.send(embed=embed)


@bet_command.error
async def bet_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument): await ctx.send(embed=create_embed("引数不足", "賭け金を指定してください。\n例: `bet 10`", discord.Color.orange(), "warning"))
    else: await help_command_error(ctx, error)

# ================================== JANKEN COMMAND (with Buttons) ==================================
class JankenChoiceView(discord.ui.View):
    def __init__(self, host_id: int):
        super().__init__(timeout=60.0)
        self.host_id = host_id
        self.message = None

    async def on_timeout(self):
        if self.message and not self.is_finished():
            embed_timeout = create_embed("じゃんけん タイムアウト", "ホストが手を選ばなかったため、じゃんけんはキャンセルされました。", discord.Color.orange(), "warning")
            try: await self.message.edit(embed=embed_timeout, view=None)
            except: pass
            if self.message.id in active_janken_games: del active_janken_games[self.message.id]

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user.id != self.host_id:
            await i.response.send_message(embed=create_embed("エラー", "じゃんけんの開始者のみが手を選べます。", discord.Color.orange(), "warning"), ephemeral=True)
            return False
        return True

    async def handle_choice(self, i: discord.Interaction, choice: str):
        self.stop()
        game_data = active_janken_games.get(i.message.id)
        if not game_data: return await i.response.edit_message(embed=create_embed("エラー", "このじゃんけんゲームは既に終了またはキャンセルされています。", discord.Color.red(), "danger"), view=None)
        
        game_data["host_hand"] = choice
        game_data["game_status"] = "opponent_recruiting"
        
        desc = f"{i.user.mention} が手を選びました！\n参加する人はリアクションで手を選んでください。"
        embed = create_embed("じゃんけん 対戦相手募集", desc, discord.Color.green(), "info")
        try:
            await i.message.edit(embed=embed, view=None) 
            await i.message.clear_reactions()
            for emoji in HAND_EMOJIS.values(): await i.message.add_reaction(emoji)
        except discord.HTTPException as e:
            print(f"Error updating Janken message: {e}")
            if i.message.id in active_janken_games: del active_janken_games[i.message.id]

    @discord.ui.button(label="グー", style=discord.ButtonStyle.primary, emoji="✊")
    async def rock_button(self, i: discord.Interaction, b: discord.ui.Button): await i.response.defer(); await self.handle_choice(i, "rock")
    @discord.ui.button(label="チョキ", style=discord.ButtonStyle.primary, emoji="✌️")
    async def scissors_button(self, i: discord.Interaction, b: discord.ui.Button): await i.response.defer(); await self.handle_choice(i, "scissors")
    @discord.ui.button(label="パー", style=discord.ButtonStyle.primary, emoji="✋")
    async def paper_button(self, i: discord.Interaction, b: discord.ui.Button): await i.response.defer(); await self.handle_choice(i, "paper")
    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel_button(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.defer(); self.stop()
        if i.message.id in active_janken_games:
            embed = create_embed("じゃんけん キャンセル", "じゃんけんはホストによってキャンセルされました。", discord.Color.red(), "danger")
            try: await i.message.edit(embed=embed, view=None)
            except: pass
            del active_janken_games[i.message.id]
    async def on_error(self, i: discord.Interaction, e: Exception, item: discord.ui.Item): await send_error_embed(i, e)


@bot.command(name="janken", aliases=["じゃんけん","ジャンケン"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def janken_command(ctx: commands.Context):
    desc = f"{ctx.author.mention} がじゃんけんを開始しました。\nまずあなたが出す手を下のボタンで選んでください。"
    embed = create_embed("じゃんけん", desc, discord.Color.blue(), "pending")
    view = JankenChoiceView(ctx.author.id) 
    try:
        game_message = await ctx.reply(embed=embed, view=view, mention_author=False)
        view.message = game_message
        active_janken_games[game_message.id] = {
            "host_id": ctx.author.id, "host_hand": None, "opponent_id": None, "opponent_hand": None,
            "channel_id": ctx.channel.id, "message": game_message, "game_status": "host_choosing"
        }
    except discord.HTTPException as e: print(f"Failed to send janken initial message: {e}")

@janken_command.error
async def janken_command_error(ctx, error): await help_command_error(ctx, error) # Cooldownを共通

# ================================== TEXT COMMANDS & HELPERS ==================================
async def _run_waifu2x(input_path: str, output_path: str) -> bool:
    if not WAIFU2X_CAFFE_PATH or not os.path.exists(WAIFU2X_CAFFE_PATH):
        print("waifu2x-caffe-cui.exe path is not set or not found. Skipping upscaling.")
        return False
    command = [WAIFU2X_CAFFE_PATH, "-i", input_path, "-o", output_path, "-m", "noise_scale", "-n", "1", "-s", "2.0"]
    try:
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            print(f"Error running waifu2x. Return code: {process.returncode}")
            print(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
            return False
        return True
    except Exception as e:
        print(f"Error running waifu2x: {e}")
        return False

async def _generate_text_image_styled(ctx: commands.Context, args: str, font_path: str, params: dict):
    """★★★★★ 最終修正: フィルターベースの安定描画ロジックに回帰し、全問題を修正 ★★★★★"""
    try:
        make_square, text_to_render = False, args.strip()
        if text_to_render.lower().endswith(" square"):
            make_square, text_to_render = True, text_to_render[:-7].strip()
        
        if not text_to_render:
            await ctx.send(embed=create_embed("引数エラー", "画像にするテキスト内容が空です。", discord.Color.orange(), "warning")); return
        if not os.path.exists(font_path):
            await ctx.send(embed=create_embed("内部エラー", f"フォントファイルが見つかりません: `{os.path.basename(font_path)}`", discord.Color.red(), "danger")); return

        processing_msg = await ctx.send(embed=create_embed("画像生成中...", "テキスト画像を生成しています...", discord.Color.blue(), "pending"))

        mode_params = params['square'] if make_square else params['normal']
        font = ImageFont.truetype(font_path, TEXT_IMAGE_FONT_SIZE_COMMON)
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
            
            current_x = 0
            for char in line:
                char_bbox = font.getbbox(char)
                draw.text((current_x - char_bbox[0], -bbox[1]), char, font=font, fill=255)
                current_x += font.getlength(char) + spacing

            line_images.append(line_img)
            max_line_width = max(max_line_width, line_img.width)
            total_line_height += line_img.height
        
        text_mask = Image.new("L", (max_line_width, total_line_height))
        current_y = 0
        for img in line_images:
            x_pos = (max_line_width - img.width) // 2
            text_mask.paste(img, (x_pos, current_y))
            current_y += img.height

        if make_square:
            bbox = text_mask.getbbox()
            if bbox:
                padding = mode_params.get('padding', 0)
                size = SQUARE_IMAGE_SIZE - padding * 2
                text_mask = text_mask.crop(bbox).resize((size, size), Image.Resampling.LANCZOS)
        
        await processing_msg.edit(embed=create_embed("画像生成中...", "縁取り処理をしています...", discord.Color.blue(), "pending"))
        
        inner_thickness = mode_params['inner_thickness']
        outer_thickness = mode_params.get('outer_thickness', 0)
        
        padding_for_filter = inner_thickness + outer_thickness + 5
        padded_mask = Image.new("L", (text_mask.width + padding_for_filter * 2, text_mask.height + padding_for_filter * 2))
        padded_mask.paste(text_mask, (padding_for_filter, padding_for_filter))

        text_layer_mask = padded_mask.copy()
        inner_outline_mask = padded_mask.filter(ImageFilter.MaxFilter(inner_thickness * 2 + 1))
        
        if outer_thickness > 0:
            outer_outline_mask = padded_mask.filter(ImageFilter.MaxFilter((inner_thickness + outer_thickness) * 2 + 1))
        else:
            outer_outline_mask = None

        final_size = outer_outline_mask.size if outer_outline_mask else inner_outline_mask.size
        final_image = Image.new("RGBA", final_size, (0, 0, 0, 0))

        if outer_outline_mask and (outer_color := mode_params.get('outer_color')):
            final_image.paste(Image.new("RGBA", final_size, outer_color), (0, 0), outer_outline_mask)
        
        final_image.paste(Image.new("RGBA", final_size, mode_params['inner_color']), (0, 0), inner_outline_mask)
        final_image.paste(Image.new("RGBA", final_size, mode_params['text_color']), (0, 0), text_layer_mask)
        
        if final_bbox := final_image.getbbox():
            final_image = final_image.crop(final_bbox)
            
        if WAIFU2X_CAFFE_PATH and os.path.exists(WAIFU2X_CAFFE_PATH):
            pass
        
        img_byte_arr = io.BytesIO(); final_image.save(img_byte_arr, format='PNG'); img_byte_arr.seek(0)
        
        resized_io, resized_flag = await _resize_image_if_too_large(img_byte_arr, "PNG")
        if not resized_io:
            await processing_msg.edit(embed=create_embed("エラー", "画像のリサイズに失敗しました。", discord.Color.red(), "danger")); img_byte_arr.close(); return
        
        file = discord.File(fp=resized_io, filename="text_image.png")
        desc = f"{STATUS_EMOJIS['info']} 改行はコンマ`,`区切りで スタンプ化は `square` をつけてください"
        embed = create_embed(params['title'], desc, params['embed_color'], "success")
        embed.set_image(url="attachment://text_image.png")
        await processing_msg.edit(content=None, embed=embed, attachments=[file])
        img_byte_arr.close(); resized_io.close()

    except Exception as e:
        if 'processing_msg' in locals():
            await processing_msg.edit(content=None, embed=create_embed("エラー", "画像生成中に予期せぬエラーが発生しました。", discord.Color.red(), "danger"))
        await send_error_embed(ctx, e)

@bot.command(name="text", aliases=["テキスト"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def text_command(ctx: commands.Context, *, args: str):
    params = {
        'title': "やまかわサムネ風テキスト", 'embed_color': discord.Color.yellow(),
        'normal': { 'text_color': NORMAL_TEXT_COLOR_YELLOW, 'inner_color': NORMAL_OUTLINE_COLOR_BLACK, 'inner_thickness': NORMAL_OUTLINE_THICKNESS_BLACK,
                    'outer_color': NORMAL_OUTLINE_COLOR_WHITE, 'outer_thickness': NORMAL_OUTLINE_THICKNESS_WHITE, 'spacing': NORMAL_LETTER_SPACING },
        'square': { 'text_color': SQUARE_TEXT_COLOR_YELLOW, 'inner_color': SQUARE_OUTLINE_COLOR_BLACK, 'inner_thickness': SQUARE_OUTLINE_THICKNESS_BLACK,
                    'outer_color': SQUARE_OUTLINE_COLOR_WHITE, 'outer_thickness': SQUARE_OUTLINE_THICKNESS_WHITE, 'spacing': SQUARE_LETTER_SPACING, 'padding': SQUARE_PADDING_FOR_OUTLINE }
    }
    await _generate_text_image_styled(ctx, args, TEXT_IMAGE_FONT_PATH_DEFAULT, params)

@bot.command(name="text2", aliases=["テキスト2"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def text2_command(ctx: commands.Context, *, args: str):
    params = {
        'title': "やまかわ青文字テキスト", 'embed_color': discord.Color.blue(),
        'normal': { 'text_color': NORMAL_TEXT_COLOR_BLUE, 'inner_color': NORMAL_OUTLINE_COLOR_BLACK, 'inner_thickness': NORMAL_OUTLINE_THICKNESS_BLACK,
                    'outer_color': NORMAL_OUTLINE_COLOR_WHITE, 'outer_thickness': NORMAL_OUTLINE_THICKNESS_WHITE, 'spacing': NORMAL_LETTER_SPACING },
        'square': { 'text_color': SQUARE_TEXT_COLOR_BLUE, 'inner_color': SQUARE_OUTLINE_COLOR_BLACK, 'inner_thickness': SQUARE_OUTLINE_THICKNESS_BLACK,
                    'outer_color': SQUARE_OUTLINE_COLOR_WHITE, 'outer_thickness': SQUARE_OUTLINE_THICKNESS_WHITE, 'spacing': SQUARE_LETTER_SPACING, 'padding': SQUARE_PADDING_FOR_OUTLINE }
    }
    await _generate_text_image_styled(ctx, args, TEXT_IMAGE_FONT_PATH_DEFAULT, params)

@bot.command(name="text3", aliases=["テキスト3"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def text3_command(ctx: commands.Context, *, args: str):
    params = {
        'title': "やまかわ赤文字テキスト", 'embed_color': discord.Color.from_rgb(0xC3, 0x02, 0x03),
        'normal': { 'text_color': NORMAL_TEXT3_COLOR_RED, 'inner_color': NORMAL_TEXT3_OUTLINE_COLOR_WHITE, 'inner_thickness': NORMAL_TEXT3_OUTLINE_THICKNESS_WHITE, 'spacing': NORMAL_LETTER_SPACING },
        'square': { 'text_color': SQUARE_TEXT3_COLOR_RED, 'inner_color': SQUARE_TEXT3_OUTLINE_COLOR_WHITE, 'inner_thickness': SQUARE_TEXT3_OUTLINE_THICKNESS_WHITE, 'spacing': SQUARE_LETTER_SPACING, 'padding': SQUARE_PADDING_FOR_OUTLINE }
    }
    await _generate_text_image_styled(ctx, args, TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD, params)

async def text_common_error_handler(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument): await ctx.send(embed=create_embed("引数不足", "画像にするテキストを指定してください。", discord.Color.orange(), "warning"))
    else: await help_command_error(ctx, error) 
text_command.error = text2_command.error = text3_command.error = text_common_error_handler

# ========================== BOT EXECUTION ==========================
if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_PLACEHOLDER":
        print("CRITICAL ERROR: DISCORD_BOT_TOKEN not set."); sys.exit(1)
    
    if not all(os.path.exists(p) for p in [TEXT_IMAGE_FONT_PATH_DEFAULT, TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD]):
        print("CRITICAL WARNING: Font files are missing. Text commands will fail.")
    
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("CRITICAL ERROR: Invalid Discord Bot Token.")
    except Exception as e:
        print(f"CRITICAL ERROR during bot execution: {e}")
        traceback.print_exc()
