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

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_BASE_URL = "https://weather.tsukumijima.net/api/forecast/city/"
PRIMARY_AREA_XML_URL = "https://weather.tsukumijima.net/primary_area.xml"
WEATHER_CITY_CODES_FILE_PATH = os.path.join(BASE_DIR, "weather_city_codes.json")
weather_city_id_map = {}
EXCHANGE_RATE_API_URL = "https://exchange-rate-api.krnk.org/api/rate"
SHORTURL_API_ENDPOINT = "https://xgd.io/V1/shorten"
SHORTURL_API_KEY = os.getenv("SHORTURL_API_KEY")
AMAZON_SHORTURL_ENDPOINT = "https://www.amazon.co.jp/associates/sitestripe/getShortUrl"
VOICEVOX_API_KEY = os.getenv("VOICEVOX_API_KEY")
VOICEVOX_SPEAKER_ID = 11
VOICEVOX_API_BASE_URL = "https://deprecatedapis.tts.quest/v2/voicevox/audio/"

_DUMMY_PREFIX_VALUE = "!@#$%^&SUGIYAMA_BOT_DUMMY_PREFIX_XYZ_VERY_UNIQUE"
def get_dummy_prefix(bot, message): return _DUMMY_PREFIX_VALUE

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

imakita_request_timestamps = deque()
IMAKITA_RATE_LIMIT_COUNT = 13
IMAKITA_RATE_LIMIT_SECONDS = 60

GREEN_SQUARE = "<:o_0:1387735237173182544>"
BLACK_STONE  = "<:o_2:1387735312129593445>"
WHITE_STONE  = "<:o_1:1387735281775411220>"
MARKERS = ["<:0_o:1387735948812488734>","<:1_o:1387735961374560368>","<:2_o:1387735974582423663>","<:3_o:1387735988629147710>","<:4_o:1387736001157398568>","<:5_o:1387736014591758367>","<:6_o:1387736028684750868>","<:7_o:1387736046099501077>","<:8_o:1387736058783072266>","<:9_o:1387736070518603776>","<:o_A:1380638761288859820>","<:o_B:1380638762941419722>","<:o_C:1380638764782850080>","<:o_D:1380638769216225321>","<:o_E:1380638771178897559>","<:o_F:1380638773926301726>","<:o_G:1380638776103010365>","<:o_H:1380643990784966898>","<:o_I:1380644006093918248>","<:o_J:1380644004181577849>","<:o_K:1380644001652281374>","<:o_L:1380643998841966612>","<:o_M:1380643995855622254>","<:o_N:1380643993431314432>","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"]
active_games = {}
othello_recruitments = {}
OTHELLO_AFK_TIMEOUT_SECONDS = 180

active_janken_games = {}
HAND_EMOJIS = {"rock": "✊", "scissors": "✌️", "paper": "✋"}
EMOJI_TO_HAND = {v: k for k, v in HAND_EMOJIS.items()}
JANKEN_TIMEOUT_HOST_CHOICE_SECONDS = 60.0
JANKEN_TIMEOUT_OPPONENT_CHOICE_SECONDS = 120.0
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
    "active_developer": "<:activedeveloper:1383253229189730374>", "nitro": "<:nitro:1383252018532974642>",
    "hypesquad_balance": "<:balance:1383251792413851688>", "hypesquad_bravery": "<:bravery:1383251749623693392>",
    "hypesquad_brilliance": "<:brilliance:1383251723610624174>", "premium": "<:booster:1383251702144176168>",
    "partner": "<:partnerserver:1383251682070364210>", "early_verified_bot_developer": "<:earlyverifiedbot:1383251648348160030>",
    "bug_hunter": "<:bugHunter:1383251633567170683>", "bug_hunter_level_2": "<:bugHunter:1383251633567170683>",
    "early_supporter": "<:earlysupporter:1383251618379727031>", "staff": "<:staff:1383251602680578111>",
    "discord_certified_moderator": "<:moderator:1383251587438215218>", "verified_bot": "✅"
}
TIMEZONE_MAP = {
    "JP": "Asia/Tokyo", "US": "America/New_York", "GB": "Europe/London", "EU": "Europe/Brussels",
    "DE": "Europe/Berlin", "FR": "Europe/Paris", "IT": "Europe/Rome", "CA": "America/Toronto",
    "AU": "Australia/Sydney", "CN": "Asia/Shanghai", "IN": "Asia/Kolkata", "BR": "America/Sao_Paulo",
    "RU": "Europe/Moscow", "KR": "Asia/Seoul", "ZA": "Africa/Johannesburg", "MX": "America/Mexico_City",
    "ID": "Asia/Jakarta", "TR": "Europe/Istanbul", "SA": "Asia/Riyadh", "AR": "America/Argentina/Buenos_Aires",
    "ES": "Europe/Madrid", "NL": "Europe/Amsterdam", "US-PST": "America/Los_Angeles", 
    "US-CST": "America/Chicago", "US-MST": "America/Denver"
}

TEXT_IMAGE_FONT_PATH_DEFAULT = os.path.join(BASE_DIR, "assets", "fonts", "MochiyPopOne-Regular.ttf")
TEXT_IMAGE_TEXT_COLOR_DEFAULT = (255, 255, 0) 
TEXT_IMAGE_OUTLINE_COLOR_BLACK_DEFAULT = (0, 0, 0)
TEXT_IMAGE_OUTLINE_COLOR_WHITE_DEFAULT = (255, 255, 255)
TEXT_IMAGE_OUTLINE_THICKNESS_BLACK_DEFAULT = 7
TEXT_IMAGE_OUTLINE_THICKNESS_WHITE_DEFAULT = 5

TEXT_IMAGE_TEXT_COLOR_BLUE = (50, 150, 255) 

TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD = os.path.join(BASE_DIR, "assets", "fonts", "NotoSerifJP-Black.ttf")
TEXT_IMAGE_TEXT_COLOR_RED_NOTO = (0xC3, 0x02, 0x03)
TEXT_IMAGE_OUTLINE_COLOR_WHITE_NOTO = (255, 255, 255)
TEXT_IMAGE_OUTLINE_THICKNESS_WHITE_NOTO = 7 

TEXT_IMAGE_FONT_SIZE_COMMON = 110
TEXT_IMAGE_PADDING_COMMON = 35 
TEXT_IMAGE_LETTER_SPACING_ADJUST_COMMON = -0.10
TEXT_IMAGE_LINE_HEIGHT_MULTIPLIER_COMMON = 0.95 
TEXT_IMAGE_VERTICAL_OFFSET_COMMON = -10 
TEXT_MASK_ADDITIONAL_MARGIN_COMMON = TEXT_IMAGE_FONT_SIZE_COMMON 

TEXT_IMAGE_BLUR_RADIUS_FACTOR_BLACK = 0.35 
TEXT_IMAGE_THRESHOLD_BLACK = 90          
TEXT_IMAGE_BLUR_RADIUS_FACTOR_WHITE = 0.35 
TEXT_IMAGE_THRESHOLD_WHITE = 90              

BET_DICE_PAYOUTS = {
    1: ("大凶... 賭け金は没収です。", -1.0), 2: ("凶。賭け金の半分を失いました。", -0.5),
    3: ("小吉。賭け金の半分を失いました。", -0.5), 4: ("吉！賭け金はそのまま戻ってきます。", 0.0),
    5: ("中吉！賭け金が1.5倍になりました。", 0.5), 6: ("大吉！おめでとうございます！賭け金が2倍になりました！", 1.0)
}

for t_data in TEMPLATES_DATA:
    if 'match_ratio_wh' not in t_data:
        try:
            parts = t_data['user_ratio_str'].split('/')
            if len(parts) == 2 and float(parts[1]) != 0: t_data['match_ratio_wh'] = float(parts[0]) / float(parts[1])
            else: raise ValueError("Invalid ratio")
        except Exception as e: print(f"Template ratio error: {t_data['name']} - {e}"); t_data['match_ratio_wh'] = 1.0

gemini_text_model_instance = None
GEMINI_API_UNAVAILABLE = False
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_PLACEHOLDER":
    try: genai.configure(api_key=GEMINI_API_KEY); gemini_text_model_instance = genai.GenerativeModel(GEMINI_TEXT_MODEL_NAME)
    except Exception as e: print(f"Gemini init error: {e}"); GEMINI_API_UNAVAILABLE = True
else: GEMINI_API_UNAVAILABLE = True

intents = discord.Intents.default(); intents.message_content = True; intents.reactions = True; intents.members = True
bot = commands.Bot(command_prefix=get_dummy_prefix, intents=intents, help_command=None)

for d in [RVC_INPUT_AUDIO_DIR, RVC_OUTPUT_AUDIO_DIR, os.path.join(BASE_DIR, "assets", "fonts"), TEMPLATES_BASE_PATH]:
    os.makedirs(d, exist_ok=True)

# ========================== HELPER FUNCTIONS (Order is important!) ==========================

# --- Custom Embeds Helper ---
STATUS_EMOJIS = {
    "success": "<:status_success:1389613617560682666>", "danger": "<:status_danger:1389613631968247838>",
    "info": "<:status_info:1389613655640899734>", "warning": "<:status_warning:1389613669515661394>",
    "pending": "<:status_pending:1389613644089655296>"
}
BOT_ICON_URL = "https://raw.githubusercontent.com/y-exe/sugiyama-bot/main/icon.jpg"

def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue(), status: str = "info", api_source: str = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"{STATUS_EMOJIS.get(status, '')} {title}",
        description=description,
        color=color
    )
    footer_text = "杉山啓太Bot"
    if api_source: footer_text += f" / {api_source}"
    embed.set_footer(text=footer_text, icon_url=BOT_ICON_URL)
    embed.timestamp = datetime.datetime.now(JST)
    return embed

async def send_error_embed(ctx: commands.Context, error: Exception):
    error_traceback = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    description = f"開発者(<@427420959211257856>)に報告してください。\n```{error_traceback[:1800]}```"
    embed = create_embed("エラーが発生しました", description, discord.Color.red(), status="danger")
    try: await ctx.reply(embed=embed, mention_author=False)
    except discord.HTTPException: await ctx.send(embed=embed)


# --- Point System ---
def load_game_points():
    global game_points
    try:
        if os.path.exists(GAME_POINTS_FILE_PATH):
            with open(GAME_POINTS_FILE_PATH, 'r', encoding='utf-8') as f: game_points = json.load(f)
        else: game_points = {}; save_game_points()
    except json.JSONDecodeError: game_points = {}; save_game_points(); print(f"Corrupted game points file at {GAME_POINTS_FILE_PATH}, created new.")
    except Exception as e: print(f"Error loading game points: {e}"); game_points = {}

def save_game_points():
    try:
        with open(GAME_POINTS_FILE_PATH, 'w', encoding='utf-8') as f: json.dump(game_points, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Error saving game points: {e}")

def get_player_points(player_id: int) -> int: return game_points.get(str(player_id), 0)

def update_player_points(player_id: int, points_change: int):
    player_id_str = str(player_id); current_points = game_points.get(player_id_str, 0)
    new_points = max(0, current_points + points_change)
    game_points[player_id_str] = new_points; save_game_points()

# --- Settings ---
def load_settings():
    global allowed_channels
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f: settings_data = json.load(f); allowed_channels = set(settings_data.get("allowed_channels", []))
        else: allowed_channels = set(); save_settings()
    except Exception as e: print(f"Error loading settings: {e}"); allowed_channels = set()

def save_settings():
    try:
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f: json.dump({"allowed_channels": list(allowed_channels)}, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Error saving settings: {e}")

# --- Othello Game Logic ---
EMPTY = 0; BLACK = 1; WHITE = 2; BOARD_SIZE = 8
class OthelloGame:
    _next_game_id_counter = 1; _active_game_ids = set()
    def __init__(self): self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]; self.board[3][3],self.board[3][4],self.board[4][3],self.board[4][4] = WHITE,BLACK,BLACK,WHITE; self.current_player = BLACK; self.valid_moves_with_markers={}; self.game_over=False; self.winner=None; self.last_pass=False; self.players={}; self.channel_id=None; self.last_move_time=datetime.datetime.now(JST); self.game_id=OthelloGame._assign_game_id_static(); self.afk_task=None; self.message_id=None
    @staticmethod
    def _assign_game_id_static(): gid=OthelloGame._next_game_id_counter; OthelloGame._active_game_ids.add(gid); OthelloGame._next_game_id_counter+=1; return gid
    @staticmethod
    def _release_game_id_static(gid): OthelloGame._active_game_ids.discard(gid)
    def is_on_board(self,r,c): return 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE
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
        for r_idx in range(BOARD_SIZE):
            for c_idx in range(BOARD_SIZE):
                if self.board[r_idx][c_idx]==EMPTY and self.get_flips(r_idx,c_idx,p): cvc.append((r_idx,c_idx)); self.valid_moves_with_markers[(r_idx,c_idx)]=MARKERS[mi] if mi<len(MARKERS) else "❓"; mi+=1
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
        else: self.last_pass=True; self.switch_player(); 
        if not self.calculate_valid_moves(self.current_player): self.game_over=True
        if self.game_over: self.determine_winner()
    def determine_winner(self): bs=sum(r.count(BLACK) for r in self.board); ws=sum(r.count(WHITE) for r in self.board); self.winner = BLACK if bs>ws else (WHITE if ws>bs else EMPTY)
    def get_current_player_id(self): return self.players.get(self.current_player)
    def get_opponent_player_id(self): return self.players.get(WHITE if self.current_player==BLACK else BLACK)

def get_initial_board_text():
    temp_game = OthelloGame(); board_str = ""
    for r_idx in range(BOARD_SIZE):
        for c_idx in range(BOARD_SIZE):
            if temp_game.board[r_idx][c_idx] == BLACK: board_str += BLACK_STONE
            elif temp_game.board[r_idx][c_idx] == WHITE: board_str += WHITE_STONE
            else: board_str += GREEN_SQUARE
        board_str += "\n"
    return board_str.strip()

async def send_othello_board_message(channel: discord.TextChannel, game_session: dict, message_to_update: discord.Message, is_first_turn: bool = False, recruitment_message_content: str = None):
    game = game_session["game"]
    if not game.game_over:
        game.calculate_valid_moves(game.current_player)

    p_black_id = game_session["players"].get(BLACK)
    p_white_id = game_session["players"].get(WHITE)
    current_player_id_from_session = game_session["players"].get(game.current_player)

    p_black_user = await bot.fetch_user(p_black_id) if p_black_id else None
    p_white_user = await bot.fetch_user(p_white_id) if p_white_id else None
    current_player_user = await bot.fetch_user(current_player_id_from_session) if current_player_id_from_session else None

    p_black_mention = f"{p_black_user.mention if p_black_user else f'Player Black ({p_black_id})'} (Pt: {get_player_points(p_black_id)})"
    p_white_mention = f"{p_white_user.mention if p_white_user else f'Player White ({p_white_id})'} (Pt: {get_player_points(p_white_id)})"
    current_player_mention = current_player_user.mention if current_player_user else f"Player ({current_player_id_from_session})"

    title_line = f"オセロゲーム #{game.game_id} | {BLACK_STONE} {p_black_mention} vs {WHITE_STONE} {p_white_mention}"
    board_str = ""
    for r_idx in range(BOARD_SIZE):
        for c_idx in range(BOARD_SIZE):
            coord = (r_idx, c_idx)
            if not game.game_over and coord in game.valid_moves_with_markers: board_str += game.valid_moves_with_markers[coord]
            elif game.board[r_idx][c_idx] == BLACK: board_str += BLACK_STONE
            elif game.board[r_idx][c_idx] == WHITE: board_str += WHITE_STONE
            else: board_str += GREEN_SQUARE
        board_str += "\n"
    
    black_score = sum(r.count(BLACK) for r in game.board)
    white_score = sum(r.count(WHITE) for r in game.board)
    score_line = f"スコア: {BLACK_STONE} {black_score} - {WHITE_STONE} {white_score}"
    
    embed = create_embed(title_line, f"{board_str.strip()}\n{score_line}", discord.Color.green(), api_source="reference オセロ君")
    
    turn_mention = ""
    if game.game_over:
        winner_text = "引き分け"; points_changed_text = ""
        if game.winner != EMPTY: 
            winner_id = game.players.get(game.winner)
            loser_id = game.players.get(WHITE if game.winner == BLACK else BLACK)
            winner_user = await bot.fetch_user(winner_id) if winner_id else None
            loser_user = await bot.fetch_user(loser_id) if loser_id else None
            winner_stone = BLACK_STONE if game.winner == BLACK else WHITE_STONE
            winner_text = f"{winner_stone} {(winner_user.mention if winner_user else f'ID:{winner_id}')} の勝ち！"
            
            if not getattr(game, 'ended_by_action', False) and winner_id and loser_id :
                score_diff = abs(black_score - white_score)
                points_change_winner = (score_diff * 3) + 10
                points_change_loser = max(0, 20 - score_diff)
                update_player_points(winner_id, points_change_winner)
                update_player_points(loser_id, points_change_loser)
                points_changed_text = f" ({winner_user.name if winner_user else f'ID:{winner_id}'} +{points_change_winner}pt, {loser_user.name if loser_user else f'ID:{loser_id}'} +{points_change_loser}pt)"
        
        elif game.winner == EMPTY and not getattr(game, 'ended_by_action', False):
            points_for_draw = 5 
            if p_black_id and p_white_id:
                update_player_points(p_black_id, points_for_draw); update_player_points(p_white_id, points_for_draw)
                points_changed_text = f" (両者 +{points_for_draw}pt)"
            winner_text = "引き分け！"
        
        embed.add_field(name="ゲーム終了！", value=f"{winner_text}{points_changed_text}", inline=False)
        
        if message_to_update and message_to_update.id in active_games:
            game_session_data = active_games.get(message_to_update.id)
            if game_session_data:
                game_obj_to_clean = game_session_data.get("game")
                if game_obj_to_clean and game_obj_to_clean.afk_task and not game_obj_to_clean.afk_task.done():
                    game_obj_to_clean.afk_task.cancel()
                OthelloGame._release_game_id_static(game.game_id)
                if message_to_update.id in active_games: del active_games[message_to_update.id]
    elif recruitment_message_content:
        embed.description = recruitment_message_content
    else:
        turn_mention = current_player_mention
        embed.add_field(name="手番", value=turn_mention, inline=False)
        embed.add_field(name="\u200b", value=f"{STATUS_EMOJIS['warning']} 処理が多いとレート制限にかかる可能性があるので落ち着いてプレイしてください", inline=False)

    if message_to_update:
        try: await message_to_update.edit(content=turn_mention if turn_mention else "", embed=embed, view=None if game.game_over or recruitment_message_content else message_to_update.view)
        except discord.HTTPException as e: print(f"Failed to edit othello message {message_to_update.id}: {e}")
    
    if message_to_update and game and not game.game_over and not recruitment_message_content:
        current_bot_reactions = [str(r.emoji) for r in message_to_update.reactions if r.me]
        new_valid_markers_emojis = list(game.valid_moves_with_markers.values())
        to_add = [emoji for emoji in new_valid_markers_emojis if emoji not in current_bot_reactions]
        to_remove = [emoji for emoji in current_bot_reactions if emoji not in new_valid_markers_emojis]
        if is_first_turn:
            try: await message_to_update.clear_reactions()
            except: pass
            to_add = new_valid_markers_emojis; to_remove = []
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
         except: pass
    return message_to_update

# --- Weather API (Tsukumijima) ---
async def load_weather_city_codes():
    global weather_city_id_map
    if os.path.exists(WEATHER_CITY_CODES_FILE_PATH):
        try:
            with open(WEATHER_CITY_CODES_FILE_PATH, 'r', encoding='utf-8') as f: weather_city_id_map = json.load(f)
            if weather_city_id_map: print(f"Loaded {len(weather_city_id_map)} weather city codes from local cache."); return
        except Exception as e: print(f"Error loading cached city codes: {e}")
    print("Fetching weather city codes from API...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PRIMARY_AREA_XML_URL) as response:
                if response.status == 200:
                    xml_text = await response.text(); root = ET.fromstring(xml_text); temp_map = {}
                    for pref_element in root.findall('.//pref'):
                        pref_title = pref_element.get('title')
                        for city_element in pref_element.findall('.//city'):
                            city_title = city_element.get('title'); city_id = city_element.get('id')
                            if city_title and city_id:
                                temp_map[city_title] = city_id
                                if pref_title and pref_title != city_title: temp_map[f"{pref_title}{city_title}"] = city_id
                    weather_city_id_map = temp_map
                    with open(WEATHER_CITY_CODES_FILE_PATH, 'w', encoding='utf-8') as f: json.dump(weather_city_id_map, f, ensure_ascii=False, indent=2)
                    print(f"Fetched and cached {len(weather_city_id_map)} city codes.")
                else: print(f"Failed to fetch city codes: HTTP {response.status}")
    except Exception as e: print(f"Error fetching city codes: {e}")

# --- Image Processing & Other Helpers ---

async def _resize_image_if_too_large(
    image_fp: io.BytesIO, 
    target_format: str, 
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
    min_dimension: int = MIN_IMAGE_DIMENSION, 
    initial_aggressiveness: float = 0.9,
    subsequent_resize_factor: float = 0.85, 
    max_iterations: int = 7
) -> tuple[io.BytesIO | None, bool]:
    image_fp.seek(0, io.SEEK_END); current_size = image_fp.tell(); image_fp.seek(0)
    if current_size <= max_size_bytes: return image_fp, False

    current_fp_to_process = image_fp
    resized_overall = False
    is_gif = target_format.upper() == "GIF"

    for iteration in range(max_iterations):
        current_fp_to_process.seek(0)
        try:
            img = Image.open(current_fp_to_process)
            original_width, original_height = img.width, img.height

            if min(original_width, original_height) <= min_dimension:
                if current_fp_to_process.tell() > MAX_FILE_SIZE_BYTES: 
                    print(f"Image dimensions ({original_width}x{original_height}) too small for further effective resizing, but size ({current_fp_to_process.tell()} bytes) still too large.")
                break 

            current_fp_to_process.seek(0, io.SEEK_END); current_iteration_size = current_fp_to_process.tell(); current_fp_to_process.seek(0)
            
            resize_this_iteration_factor = subsequent_resize_factor
            if iteration == 0 and current_iteration_size > max_size_bytes:
                area_ratio = MAX_FILE_SIZE_BYTES / current_iteration_size
                dimension_ratio_estimate = math.sqrt(area_ratio) * initial_aggressiveness
                resize_this_iteration_factor = max(0.1, min(dimension_ratio_estimate, 0.95))

            new_width = int(original_width * resize_this_iteration_factor)
            new_height = int(original_height * resize_this_iteration_factor)

            if new_width < min_dimension or new_height < min_dimension:
                aspect_ratio_orig = original_width / original_height
                if new_width < min_dimension and new_height < min_dimension:
                    if new_width / aspect_ratio_orig >= min_dimension: 
                         new_width = min_dimension
                         new_height = int(new_width / aspect_ratio_orig) if aspect_ratio_orig != 0 else min_dimension
                    elif new_height * aspect_ratio_orig >= min_dimension: 
                         new_height = min_dimension
                         new_width = int(new_height * aspect_ratio_orig) if aspect_ratio_orig !=0 else min_dimension
                    else: 
                        if original_width > original_height:
                            new_width = min_dimension
                            new_height = int(new_width / aspect_ratio_orig) if aspect_ratio_orig !=0 else min_dimension
                        else:
                            new_height = min_dimension
                            new_width = int(new_height * aspect_ratio_orig) if aspect_ratio_orig !=0 else min_dimension
                elif new_width < min_dimension:
                    new_width = min_dimension
                    new_height = int(new_width / aspect_ratio_orig) if aspect_ratio_orig != 0 else min_dimension
                else: # new_height < min_dimension
                    new_height = min_dimension
                    new_width = int(new_height * aspect_ratio_orig) if aspect_ratio_orig != 0 else min_dimension
                
                new_width = max(new_width, 1); new_height = max(new_height, 1)
                if new_width >= original_width and new_height >= original_height: break # No effective downscale

            output_fp = io.BytesIO()
            
            if is_gif:
                frames = []; durations = []; loop = img.info.get('loop', 0); disposal = 2
                try:
                    img.seek(0)
                    while True:
                        frame_copy = img.copy().convert("RGBA")
                        frame_copy.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                        frames.append(frame_copy)
                        durations.append(img.info.get('duration', 100))
                        img.seek(img.tell() + 1)
                except EOFError: pass
                if not frames: break
                frames[0].save(output_fp, format="GIF", save_all=True, append_images=frames[1:], duration=durations, loop=loop, disposal=disposal, optimize=True)
            else:
                resized_img = img.copy() 
                resized_img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                save_params = {'optimize': True}
                if target_format.upper() == 'JPEG': save_params['quality'] = 85
                elif target_format.upper() == 'PNG': save_params['compress_level'] = 7
                resized_img.save(output_fp, format=target_format.upper(), **save_params)

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
        base_image = Image.open(io.BytesIO(img_bytes))
        target_width, target_height = tmpl_data['target_size']
        processed_base_image = ImageOps.fit(base_image, (target_width, target_height), Image.Resampling.LANCZOS)
        overlay_path = os.path.join(TEMPLATES_BASE_PATH, tmpl_data['name'])
        if not os.path.exists(overlay_path): print(f"Overlay template not found: {overlay_path}"); return None
        overlay_image = Image.open(overlay_path).convert("RGBA")
        if overlay_image.size != (target_width, target_height): overlay_image = overlay_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        if processed_base_image.mode != 'RGBA': processed_base_image = processed_base_image.convert('RGBA')
        final_image = Image.alpha_composite(processed_base_image, overlay_image)
        output_buffer = io.BytesIO(); final_image.save(output_buffer, "PNG"); output_buffer.seek(0)
        return output_buffer
    except Exception as e_composite: print(f"Error during image compositing: {e_composite}"); return None

def _create_gaming_gif(img_bytes: bytes, duration_ms: int = 50, max_size: tuple = (256, 256)) -> io.BytesIO | None:
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        frames = []
        for i in range(36):
            h, s, v = img.convert("HSV").split()
            h_array = np.array(h, dtype=np.int16)
            hue_shift_amount = int((i * 10) * (255.0 / 360.0))
            shifted_h_array = np.mod(h_array + hue_shift_amount, 256).astype(np.uint8)
            shifted_h_image = Image.fromarray(shifted_h_array, 'L')
            gaming_frame_hsv = Image.merge("HSV", (shifted_h_image, s, v))
            frames.append(gaming_frame_hsv.convert("RGBA"))
        output_buffer = io.BytesIO()
        frames[0].save(output_buffer, format="GIF", save_all=True, append_images=frames[1:], duration=duration_ms, loop=0, disposal=2, optimize=True)
        output_buffer.seek(0); return output_buffer
    except Exception as e_gif: print(f"Error creating gaming GIF: {e_gif}"); traceback.print_exc(); return None

# --- Gemini Helpers ---
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

# --- VoiceVox & RVC Helpers ---
async def generate_voicevox_audio(text_to_speak: str, speaker_id: int, api_key: str) -> io.BytesIO | None:
    if not api_key or api_key == "YOUR_VOICEVOX_API_KEY_PLACEHOLDER": print("VoiceVox API key not configured."); return None
    print(f"Attempting VoiceVox TTS. API Key: '{api_key[:5]}...', Speaker ID: {speaker_id}")
    params_dict = {"text": text_to_speak, "speaker": str(speaker_id), "key": api_key}
    print(f"Requesting VoiceVox TTS for text: '{text_to_speak[:50]}...'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(VOICEVOX_API_BASE_URL, params=params_dict, timeout=aiohttp.ClientTimeout(total=60)) as response:
                print(f"VoiceVox API response status: {response.status}, Content-Type: {response.content_type}")
                if response.status == 200:
                    if response.content_type in ('audio/wav', 'audio/x-wav'):
                        audio_data = await response.read(); print(f"VoiceVox TTS success, received {len(audio_data)} bytes."); return io.BytesIO(audio_data)
                    else: print(f"VoiceVox API returned 200 OK but with unexpected Content-Type ({response.content_type}): {(await response.text())[:200]}"); return None
                else: print(f"VoiceVox API request failed (Status {response.status}): {(await response.text())[:500]}"); return None
    except Exception as e: print(f"Error during VoiceVox API call: {e}"); traceback.print_exc(); return None

async def process_audio_with_rvc(ctx: commands.Context, audio_bytes_io: io.BytesIO, original_filename_base: str, input_file_extension_no_dot: str):
    try: 
        temp_audio_stream = io.BytesIO(audio_bytes_io.getvalue()); temp_audio_stream.seek(0)
        audio_segment = AudioSegment.from_file(temp_audio_stream, format=input_file_extension_no_dot)
        duration_seconds = len(audio_segment) / 1000.0; temp_audio_stream.close()
        if duration_seconds > 45.0: await ctx.send(f"エラー: 音声長すぎ ({duration_seconds:.1f}s > 45s)"); return False
    except Exception as e_dur: await ctx.send(f"音声長確認エラー: {e_dur}"); return False
    finally: audio_bytes_io.seek(0)

    rvc_script = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    rvc_model = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    processing_msg = await ctx.send("やまかわボイチェン処理中..."); success = False
    return success 

# ========================== DISCORD EVENTS ==========================
@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name} ({bot.user.id})')
    load_settings(); load_game_points() 
    await load_weather_city_codes()

    print(f"Settings loaded. Allowed channels: {len(allowed_channels)}")
    print(f"Game points loaded for {len(game_points)} players.")
    gemini_status = "Available" if not GEMINI_API_UNAVAILABLE else "Not Available"; print(f"Gemini API Status: {gemini_status}")
    vv_status = "Available" if VOICEVOX_API_KEY and VOICEVOX_API_KEY != "YOUR_VOICEVOX_API_KEY_PLACEHOLDER" else "Not Available"; print(f"VoiceVox API Status: {vv_status}")
    if weather_city_id_map: print(f"Tsukumijima Weather city codes loaded: {len(weather_city_id_map)} cities.")
    else: print("WARNING: Tsukumijima Weather city codes not loaded.")

    default_font_ok = True; noto_font_ok = True
    if not os.path.exists(TEXT_IMAGE_FONT_PATH_DEFAULT): print(f"CRITICAL WARNING: Default text font not found: {TEXT_IMAGE_FONT_PATH_DEFAULT}"); default_font_ok = False
    else: print(f"Default text font found: {TEXT_IMAGE_FONT_PATH_DEFAULT}")
    if not os.path.exists(TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD): print(f"WARNING: Noto Serif font not found: {TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD}. 'text3' will fail."); noto_font_ok = False
    else: print(f"Noto Serif font for text3 found: {TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD}")
    if not default_font_ok: print("CRITICAL: Default font for text commands is missing.")

    print("--- RVC Checks ---")
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
        if sub_command_name == "leave": potential_command_name = "leave"; command_parts = [potential_command_name]; is_othello_subcommand = True
        elif sub_command_name in ["point", "points"]: potential_command_name = "othello_points"; command_parts = [potential_command_name]; is_othello_subcommand = True
    command_obj = bot.get_command(potential_command_name)
    if command_obj:
        print(f"Prefix-less command '{potential_command_name}' from '{message.author.name}'. Processing..."); _content_backup_cmd = message.content
        prefix_to_use = get_dummy_prefix(bot, message)
        if is_othello_subcommand: message.content = f"{prefix_to_use}{potential_command_name}"
        elif len(command_parts) > 1: message.content = f"{prefix_to_use}{potential_command_name} {command_parts[1]}".strip()
        else: message.content = f"{prefix_to_use}{potential_command_name}"
        print(f"  Modified content: '{message.content}'"); await bot.process_commands(message); message.content = _content_backup_cmd

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user == bot.user: return
    message = reaction.message; message_id = message.id

    if message_id in active_games:
        game_session = active_games.get(message_id)
        if not game_session:
            print(f"Error: Message ID {message_id} in active_games but no session found.")
            return
        game = game_session["game"]
        if user.id not in game.players.values() or game.game_over:
            if user.id != bot.user.id:
                try: await reaction.remove(user)
                except: pass
            return
        if user.id != game.players.get(game.current_player):
            try: await reaction.remove(user)
            except: pass
            return
        chosen_move = next((coord for coord, marker_emoji in game.valid_moves_with_markers.items() if str(reaction.emoji) == marker_emoji), None)
        if chosen_move:
            print(f"DEBUG: Othello move by {user.name}: {chosen_move} with emoji {reaction.emoji}")
            if game.make_move(chosen_move[0], chosen_move[1], game.current_player):
                if game.afk_task and not game.afk_task.done(): game.afk_task.cancel()
                game.switch_player(); game.check_game_status()
                await send_othello_board_message(message.channel, game_session, message_to_update=message)
                if not game.game_over: game.afk_task = asyncio.create_task(othello_afk_timeout(game))
            else: print(f"DEBUG: Othello make_move failed for {chosen_move}")
        else: print(f"DEBUG: Othello invalid reaction emoji {reaction.emoji} by {user.name}")
        if user.id != bot.user.id:
            try: await reaction.remove(user)
            except discord.HTTPException: pass
        return

    if message_id in othello_recruitments:
        rec_info = othello_recruitments[message_id]
        host_id = rec_info["host_id"]
        
        if str(reaction.emoji) == "❌" and user.id == host_id:
            if message_id in othello_recruitments: del othello_recruitments[message_id]
            try:
                await message.edit(content=f"{user.mention}がオセロの募集を取り消しました。", view=None)
                await message.clear_reactions()
            except discord.HTTPException: 
                pass
            return

        if str(reaction.emoji) == "✅" and user.id != host_id:
            if rec_info.get("opponent_id"): 
                try:
                    await reaction.remove(user)
                except discord.HTTPException:
                    pass
                return 
            
            rec_info["opponent_id"] = user.id
            players_list = [host_id, user.id]
            random.shuffle(players_list)
            game_instance = OthelloGame()
            game_instance.players = {BLACK: players_list[0], WHITE: players_list[1]}
            game_instance.channel_id = message.channel.id
            game_session = {"game": game_instance, "players": game_instance.players, "host_id": host_id, "channel_id": message.channel.id}
            
            active_games[message.id] = game_session 
            game_instance.message_id = message.id 
            if message_id in othello_recruitments:
                del othello_recruitments[message_id]

            print(f"DEBUG: Othello game {game_instance.game_id} started via recruitment. Message ID: {message_id}")
            await send_othello_board_message(message.channel, game_session, message_to_update=message, is_first_turn=True)
            if not game_instance.game_over:
                game_instance.afk_task = asyncio.create_task(othello_afk_timeout(game_instance))
            return 

        elif user.id != host_id: 
             try:
                 await reaction.remove(user)
             except discord.HTTPException:
                 pass
        return

    if message_id in active_games:
        return


    if message_id in active_janken_games: 
        game_data = active_janken_games[message_id]
        if game_data["game_status"] == "opponent_recruiting" and user.id != game_data["host_id"] and not user.bot:
            if str(reaction.emoji) in HAND_EMOJIS.values() and game_data["opponent_id"] is None: # First valid opponent
                game_data["opponent_id"] = user.id
                game_data["opponent_hand"] = EMOJI_TO_HAND[str(reaction.emoji)]
                game_data["game_status"] = "finished"

                try:
                    host_user = await bot.fetch_user(game_data["host_id"])
                    opponent_user = user
                except discord.NotFound:
                    print(f"Janken: Could not find user for host {game_data['host_id']} or opponent {user.id}")
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
                    if game_data["message"]: 
                        await game_data["message"].edit(embed=embed_result, view=None) 
                except discord.HTTPException as e:
                    print(f"Error editing Janken result message: {e}")
                
                if message_id in active_janken_games: del active_janken_games[message_id]
            
            elif game_data["opponent_id"] is not None and user.id != game_data["opponent_id"]: 
                try: await reaction.remove(user) 
                except: pass
            elif str(reaction.emoji) not in HAND_EMOJIS.values(): 
                try: await reaction.remove(user)
                except: pass
            return # Janken logic handled
        elif game_data["game_status"] == "opponent_recruiting" and user.id == game_data["host_id"]:
            try: await reaction.remove(user)
            except: pass
            return

async def othello_afk_timeout(game: OthelloGame):

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
            points_for_winner_afk = 10  
            points_lost_by_afk = -15    

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
# # HELP COMMAND
class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180.0) 
        self.message = None 

    @discord.ui.button(label="コマンド一覧を表示", style=discord.ButtonStyle.primary)
    async def show_commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed("杉山啓太Bot コマンド一覧", "", discord.Color(0x3498db), "info")
        cmds = [
            ("`watermark` + [画像]", "画像にウォーターマークを合成します。"),
            ("`/imakita`", "過去30分のチャットを3行で要約します。(スラッシュコマンド)"),
            ("`5000 [上] [下]`", "「5000兆円欲しい！」画像を生成します。"),
            ("`gaming` + [画像]", "画像をゲーミング風GIFに変換します。"),
            ("`othello (@相手)`", "オセロをプレイします。"),
            ("`janken`", "じゃんけんゲームを開始します。"),
            ("`bet [金額]`", "ポイントを賭けてダイスゲームに挑戦します。"),
            ("`text [文字]`", "やまかわサムネ風の黄色い文字画像を生成します。"),
            ("`text2 [文字]`", "やまかわサムネ風の青い文字画像を生成します。"),
            ("`text3 [文字]`", "Noto Serifフォントの赤い文字画像を生成します。"),
            ("`voice [文字/音声]`", "テキストまたは音声を変換します。"),
            ("`ping`", "Botの応答速度を表示します。"),
            ("`tenki [地名]`", "日本の都市の天気予報を表示します。"),
            ("`info (@相手)`", "ユーザー情報を表示します。"),
            ("`rate [金額] [通貨]`", "外貨を日本円に換算します。"),
            ("`shorturl [URL]`", "URLを短縮します。"),
            ("`amazon [URL]`", "AmazonのURLを短縮します。"),
            ("`totusi [文字列]`", "突然の死ジェネレーター。"),
            ("`time (国コード)`", "世界時計。"),
            ("`help`", "このヘルプを表示します。"),
        ]
        for name, value in cmds:
            embed.add_field(name=name, value=value, inline=False)
        
        font_status_default = "✅" if os.path.exists(TEXT_IMAGE_FONT_PATH_DEFAULT) else "❌"
        font_status_noto = "✅" if os.path.exists(TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD) else "❌"
        embed.add_field(name="API/Font Status", value=f"Gemini: {'✅' if not GEMINI_API_UNAVAILABLE else '❌'} | VoiceVox: {'✅' if VOICEVOX_API_KEY else '❌'}\nFont(Default): {font_status_default} | Font(Noto): {font_status_noto}", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            await interaction.message.delete()
        except discord.HTTPException:
            pass
        
        self.stop()
    
    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

@bot.command(name="help")
@commands.cooldown(1, 5, commands.BucketType.user)
async def help_command(ctx: commands.Context):
    embed = create_embed(
        "ヘルプ", 
        "下のボタンを押してコマンド一覧を表示します。",
        discord.Color(0x3498db),
        "info"
    )
    view = HelpView()
    message = await ctx.reply(embed=embed, view=view, mention_author=False)
    view.message = message 

@help_command.error
async def help_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else:
        await send_error_embed(ctx, error)

# # SETCHANNEL COMMAND
@bot.command(name="setchannel")
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.guild)
async def setchannel_command(ctx: commands.Context):
    cid = ctx.channel.id
    if cid in allowed_channels:
        allowed_channels.remove(cid)
        desc = f"このチャンネル <#{cid}> でのコマンド利用を**禁止**しました。"
        embed = create_embed("設定変更完了", desc, discord.Color.red(), "success")
    else:
        allowed_channels.add(cid)
        desc = f"このチャンネル <#{cid}> でのコマンド利用を**許可**しました。"
        embed = create_embed("設定変更完了", desc, discord.Color.green(), "success")
    save_settings()
    await ctx.reply(embed=embed, mention_author=False)

@setchannel_command.error
async def setchannel_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = create_embed("権限エラー", "このコマンドを実行するには管理者権限が必要です。", discord.Color.red(), "danger")
        await ctx.reply(embed=embed, mention_author=False)
    else:
        await send_error_embed(ctx, error)

# # WATERMARK COMMAND
@bot.command(name="watermark")
@commands.cooldown(1, 15, commands.BucketType.user)
async def watermark_command(ctx: commands.Context):
    if not ctx.message.attachments or not ctx.message.attachments[0].content_type.startswith("image/"):
        embed = create_embed("引数エラー", "画像を添付してください。", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False); return
    attachment = ctx.message.attachments[0]
    
    if not TEMPLATES_DATA:
        embed = create_embed("内部エラー", "ウォーターマークのテンプレートが設定されていません。", discord.Color.red(), "danger")
        await ctx.reply(embed=embed, mention_author=False); return

    async with ctx.typing():
        image_bytes = await attachment.read()
        try:
            uploaded_image = Image.open(io.BytesIO(image_bytes)); uw, uh = uploaded_image.size
            if uw == 0 or uh == 0: await ctx.reply(embed=create_embed("エラー", "無効な画像サイズです。", discord.Color.orange(), "warning"), mention_author=False); return
            uploaded_ratio = uw / uh
        except Exception as e: await send_error_embed(ctx, e); return

        valid_templates_with_diff = []
        for template_info in TEMPLATES_DATA:
            if 'match_ratio_wh' in template_info and os.path.exists(os.path.join(TEMPLATES_BASE_PATH, template_info['name'])):
                diff = abs(template_info['match_ratio_wh'] - uploaded_ratio)
                valid_templates_with_diff.append({"diff": diff, "data": template_info})
        
        if not valid_templates_with_diff: await ctx.reply(embed=create_embed("エラー", "利用可能なウォーターマークテンプレートが見つかりませんでした。", discord.Color.orange(), "warning"), mention_author=False); return

        valid_templates_with_diff.sort(key=lambda x: x["diff"])
        num_to_select_from = 4
        candidate_templates_info = [item["data"] for item in valid_templates_with_diff[:num_to_select_from]]
        if not candidate_templates_info: await ctx.reply(embed=create_embed("エラー", "アスペクト比の近いテンプレート候補が見つかりませんでした。", discord.Color.orange(), "warning"), mention_author=False); return
        
        selected_template_data = random.choice(candidate_templates_info)
        
        processed_image_io = await asyncio.to_thread(_process_and_composite_image, image_bytes, selected_template_data)

        if processed_image_io:
            final_image_io, resized_flag = await _resize_image_if_too_large(processed_image_io, "PNG")
            if final_image_io is None: await ctx.reply(embed=create_embed("エラー", "画像の最終処理に失敗しました。", discord.Color.red(), "danger"), mention_author=False); return

            file = discord.File(fp=final_image_io, filename=f"wm_{os.path.splitext(attachment.filename)[0]}.png")
            desc = f"使用テンプレート: `{selected_template_data['name']}`{' (リサイズ済)' if resized_flag else ''}"
            embed = create_embed("ウォーターマーク加工完了", desc, discord.Color.blue(), "success")
            embed.set_image(url=f"attachment://{file.filename}")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            if processed_image_io != final_image_io : processed_image_io.close()
            final_image_io.close()
        else: await ctx.reply(embed=create_embed("エラー", "画像の加工に失敗しました。", discord.Color.red(), "danger"), mention_author=False)

# 5000 COMMAND
@bot.command(name="5000")
@commands.cooldown(1, 5, commands.BucketType.user)
async def five_k_choyen_command(ctx: commands.Context, top_text: str, bottom_text: str, *options: str):
    options_list = [opt.lower() for opt in options]
    params = {"top": top_text, "bottom": bottom_text, "hoshii": "true" if "hoshii" in options_list else "false", "rainbow": "true" if "rainbow" in options_list else "false"}
    url = f"https://gsapi.cbrx.io/image?{urllib.parse.urlencode(params)}"
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as s, s.get(url) as r:
                if r.status == 200:
                    embed = create_embed("5000兆円欲しい！", "", discord.Color.gold(), "success", "5000choyen-api")
                    embed.set_image(url=url)
                    await ctx.reply(embed=embed, mention_author=False)
                else:
                    embed = create_embed("エラー", f"画像生成に失敗しました。(APIステータス: {r.status})", discord.Color.red(), "danger", "5000choyen-api")
                    await ctx.reply(embed=embed, mention_author=False)
        except Exception as e: await send_error_embed(ctx, e)

@five_k_choyen_command.error
async def five_k_choyen_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed("引数不足", "引数が不足しています。\n例: `5000 上の文字 下の文字`", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else: await send_error_embed(ctx, error)

# # GAMING COMMAND
@bot.command(name="gaming")
@commands.cooldown(1, 15, commands.BucketType.user)
async def gaming_command(ctx: commands.Context):
    if not ctx.message.attachments or not ctx.message.attachments[0].content_type.startswith("image/"):
        embed = create_embed("エラー", "画像を添付してください。", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False); return
    attachment = ctx.message.attachments[0]

    async with ctx.typing():
        image_bytes = await attachment.read()
        gif_buffer_io = await asyncio.to_thread(_create_gaming_gif, image_bytes)
        if gif_buffer_io is None: await ctx.reply(embed=create_embed("エラー", "ゲーミングGIFの生成に失敗しました。", discord.Color.red(), "danger"), mention_author=False); return
        
        final_image_io, resized_flag = await _resize_image_if_too_large(gif_buffer_io, "GIF")
        if final_image_io is None: await ctx.reply(embed=create_embed("エラー", "画像の最終処理に失敗しました。", discord.Color.red(), "danger"), mention_author=False); return

        file = discord.File(fp=final_image_io, filename=f"gaming_{os.path.splitext(attachment.filename)[0]}.gif")
        desc = f"うまくいかない場合は、カラー画像を添付してください。{' (リサイズ済)' if resized_flag else ''}"
        embed = create_embed("ゲーミングGIF生成完了", desc, discord.Color.purple(), "success")
        embed.set_image(url=f"attachment://{file.filename}")
        await ctx.reply(embed=embed, file=file, mention_author=False)
        if gif_buffer_io != final_image_io : gif_buffer_io.close()
        final_image_io.close()


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
        except ValueError: 
            rank_text_parts.append(f"{rank}位 ID:{player_id_str} (取得エラー) - {player_points_val}pt")
        except discord.NotFound:
             rank_text_parts.append(f"{rank}位 ID:{player_id_str} (不明なユーザー) - {player_points_val}pt")


    if not rank_text_parts: rank_text_parts.append("まだポイントを持っているプレイヤーがいません。")
    
    if not user_found_in_top and points > 0: 
        for i, (pid_str, p_points_val) in enumerate(sorted_points_data):
            if int(pid_str) == ctx.author.id:
                user_rank_info = f"\nあなたの順位: **{i+1}位** {ctx.author.mention} - **{points}pt**"
                break
                
    embed.description = "\n".join(rank_text_parts) + user_rank_info
    embed.set_footer(text="このポイントはオセロ(othello)・じゃんけん(janken)・賭け(bet)で共通です。")
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
            score_diff_leave = abs(bs - ws) if bs != ws else 1 
            point_message = ""

            if opponent_id and player_id_to_leave:
                points_for_opponent_leave = 15 
                points_lost_by_leaver = -20 

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
            if board_message_to_update:
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
    while imakita_request_timestamps and imakita_request_timestamps[0] < current_time - IMAKITA_RATE_LIMIT_SECONDS:
        imakita_request_timestamps.popleft()

    if len(imakita_request_timestamps) >= IMAKITA_RATE_LIMIT_COUNT:
        await interaction.response.send_message(
            f"APIリクエストが集中しています。しばらく時間をおいて再度お試しください。(あと約 {int(IMAKITA_RATE_LIMIT_SECONDS - (current_time - imakita_request_timestamps[0]))}秒)",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    imakita_request_timestamps.append(current_time) 

    if not hasattr(interaction.channel, 'history'):
         return await interaction.followup.send("このチャンネルではメッセージ履歴を取得できません。", ephemeral=True)

    after_time = discord.utils.utcnow() - datetime.timedelta(minutes=30)
    c_list = [f"{m.author.display_name}: {m.content}" async for m in interaction.channel.history(limit=200, after=after_time) if m.author != bot.user and not m.author.bot and m.content]
    if not c_list: return await interaction.followup.send("過去30分にメッセージはありませんでした。", ephemeral=True)
    
    summary = await generate_summary_with_gemini("\n".join(reversed(c_list)), 3)
    msg = f"**今北産業:**\n{summary}" if not summary.startswith("Error:") else f"要約エラー:\n{summary}"
    await interaction.followup.send(msg, ephemeral=True)

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
                    if response.content_type in ('audio/wav', 'audio/x-wav'): 
                        audio_data = await response.read()
                        print(f"VoiceVox TTS success, received {len(audio_data)} bytes of {response.content_type} data.")
                        return io.BytesIO(audio_data)
                    else:
                        try:
                            error_text = await response.text()
                            print(f"VoiceVox API returned 200 OK but with unexpected Content-Type ({response.content_type}): {error_text[:200]}")
                        except UnicodeDecodeError: 
                            print(f"VoiceVox API returned 200 OK but with unexpected Content-Type ({response.content_type}) and non-text body.")
                        return None
                elif response.status == 403: 
                    error_text = ""
                    try: error_text = await response.text()
                    except UnicodeDecodeError: error_text = "(Failed to decode error response as text)"
                    print(f"VoiceVox API request failed with status 403 (Forbidden).")
                    print(f"  Response Text: {error_text[:500]}")
                    return None
                else: 
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
async def process_audio_with_rvc(ctx: commands.Context, status_message: discord.Message, audio_bytes_io: io.BytesIO, original_filename_base: str, input_file_extension_no_dot: str):
    try:
        # --- このブロック全体をインデント ---
        temp_audio_stream = io.BytesIO(audio_bytes_io.getvalue())
        temp_audio_stream.seek(0)
        audio_segment = AudioSegment.from_file(temp_audio_stream, format=input_file_extension_no_dot)
        duration_seconds = len(audio_segment) / 1000.0
        print(f"Audio duration for RVC: {duration_seconds:.2f} seconds")
        temp_audio_stream.close()

        if duration_seconds > 45.0:
            embed = create_embed("エラー", f"音声が長すぎます ({duration_seconds:.1f}秒)。45秒以下の音声にしてください。", discord.Color.orange(), "warning")
            await status_message.edit(embed=embed)
            return False
        # ------------------------------------
    except Exception as e_dur:
        embed = create_embed("エラー", f"音声ファイルの長さ確認中に問題が発生しました: {e_dur}", discord.Color.red(), "danger")
        await status_message.edit(embed=embed)
        return False
    finally:
        audio_bytes_io.seek(0)

    # RVC Paths and command construction
    rvc_script = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_INFER_SCRIPT_SUBPATH)
    rvc_model = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, RVC_MODEL_NAME_WITH_EXT)
    rvc_index_file_name_no_ext, _ = os.path.splitext(RVC_MODEL_NAME_WITH_EXT)
    rvc_index_full_path = os.path.join(RVC_PROJECT_ROOT_PATH, RVC_MODEL_DIR_IN_PROJECT, f"{rvc_index_file_name_no_ext}.index")

    if not os.path.exists(rvc_script) or not os.path.exists(rvc_model):
        embed = create_embed("内部エラー", "RVC関連ファイルが見つかりません。管理者に連絡してください。", discord.Color.red(), "danger")
        await status_message.edit(embed=embed); return False

    # Status message update
    processing_embed = create_embed("RVC処理中", "やまかわボイチェンで変換しています...\nしばらくお待ちください... (目安:20~50秒)", discord.Color.red(), "pending")
    await status_message.edit(embed=processing_embed)
    
    timestamp = datetime.datetime.now(JST).strftime("%Y%m%d%H%M%S%f"); unique_id = f"{ctx.author.id}_{ctx.message.id}_{timestamp}"
    input_filename_rvc = f"input_{unique_id}.{input_file_extension_no_dot}"
    output_filename_rvc = f"output_{unique_id}.wav" # RVCはwavで出力されることが多いので固定
    input_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_INPUT_AUDIO_DIR, input_filename_rvc))
    output_filepath_abs_rvc = os.path.abspath(os.path.join(RVC_OUTPUT_AUDIO_DIR, output_filename_rvc))
    
    success_flag = False
    try:
        with open(input_filepath_abs_rvc, 'wb') as f_out:
            f_out.write(audio_bytes_io.getbuffer())
        
        command = [sys.executable, rvc_script, "--f0up_key", str(RVC_FIXED_TRANSPOSE), "--input_path", input_filepath_abs_rvc, "--opt_path", output_filepath_abs_rvc, "--model_name", RVC_MODEL_NAME_WITH_EXT]
        if os.path.exists(rvc_index_full_path): command.extend(["--feature_path", rvc_index_full_path])
        
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=RVC_PROJECT_ROOT_PATH)
        stdout_bytes, stderr_bytes = await process.communicate()
        if stdout_bytes: print(f"--- RVC STDOUT ---\n{stdout_bytes.decode('utf-8', errors='ignore').strip()}\n------------------")
        if stderr_bytes: print(f"--- RVC STDERR ---\n{stderr_bytes.decode('utf-8', errors='ignore').strip()}\n------------------")

        if process.returncode != 0:
            error_embed = create_embed("RVCエラー", "音声変換プロセスでエラーが発生しました。詳細はログを確認してください。", discord.Color.red(), "danger")
            await status_message.edit(embed=error_embed)
        elif os.path.exists(output_filepath_abs_rvc) and os.path.getsize(output_filepath_abs_rvc) > 0:
            success_embed = create_embed("音声変換完了", f"{STATUS_EMOJIS['info']} うまくいかない場合はBGMを抜いてみてください", discord.Color.green(), "success")
            await status_message.edit(embed=success_embed)
            await ctx.reply(file=discord.File(output_filepath_abs_rvc, filename=f"rvc_{original_filename_base}.wav"), mention_author=False)
            success_flag = True
        else:
            error_embed = create_embed("エラー", "変換は成功しましたが、出力ファイルが見つかりませんでした。", discord.Color.red(), "danger")
            await status_message.edit(embed=error_embed)
            
    except Exception as e:
        await status_message.edit(embed=create_embed("予期せぬエラー", "音声変換処理中にエラーが発生しました。", discord.Color.red(), "danger"))
        print(f"Unexpected error in process_audio_with_rvc: {e}"); traceback.print_exc()
    finally:
        if os.path.exists(input_filepath_abs_rvc):
            try: os.remove(input_filepath_abs_rvc)
            except Exception as e_rem: print(f"Failed to delete RVC input temp file: {e_rem}")
        if os.path.exists(output_filepath_abs_rvc):
            try: os.remove(output_filepath_abs_rvc)
            except Exception as e_rem: print(f"Failed to delete RVC output temp file: {e_rem}")
            
    return success_flag


# # VOICE COMMAND
@bot.command(name="voice")
@commands.cooldown(1, 20, commands.BucketType.user)
async def rvc_voice_convert_command(ctx: commands.Context, *, text_input: str = None):
    if not ctx.message.attachments and not text_input:
        embed = create_embed("引数エラー", "音声ファイルを添付するか、変換したいテキストを入力してください。\n例: `voice こんにちは`", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False); return

    audio_bytes_io = None
    original_filename_base = "text_to_speech"
    input_file_extension = "wav"

    processing_embed = create_embed("処理開始", "音声処理を開始します...", discord.Color.light_grey(), "pending")
    status_message = await ctx.reply(embed=processing_embed, mention_author=False)

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not (attachment.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a'))):
            embed = create_embed("エラー", "対応している音声ファイル形式は `.wav`, `.mp3`, `.flac`, `.m4a` です。", discord.Color.orange(), "warning")
            await status_message.edit(embed=embed); return
        audio_bytes_io = io.BytesIO(); await attachment.save(audio_bytes_io); audio_bytes_io.seek(0)
        original_filename_base, ext = os.path.splitext(attachment.filename)
        input_file_extension = ext.lstrip('.').lower()

    elif text_input:
        if not VOICEVOX_API_KEY:
            embed = create_embed("APIエラー", "テキストからの音声変換機能は現在利用できません。", discord.Color.red(), "danger")
            await status_message.edit(embed=embed); return
        
        processing_embed.description = f"「{text_input[:30]}{'...' if len(text_input)>30 else ''}」をVoiceVoxで音声生成中..."
        processing_embed.color = discord.Color.green()
        await status_message.edit(embed=processing_embed)
        
        generated_audio_stream = await generate_voicevox_audio(text_input, VOICEVOX_SPEAKER_ID, VOICEVOX_API_KEY)
        if generated_audio_stream:
            audio_bytes_io = generated_audio_stream
            processing_embed.description += f"\n{STATUS_EMOJIS['success']} VoiceVoxでの音声生成完了。RVC処理を開始します..."
            processing_embed.color = discord.Color.red()
            await status_message.edit(embed=processing_embed)
        else:
            embed = create_embed("APIエラー", "VoiceVoxでの音声生成に失敗しました。\nAPIエラーか、テキストが長すぎる可能性があります。", discord.Color.red(), "danger", "VoiceVox API")
            await status_message.edit(embed=embed); return
    
    if audio_bytes_io and audio_bytes_io.getbuffer().nbytes > 0:
        await process_audio_with_rvc(ctx, status_message, audio_bytes_io, original_filename_base, input_file_extension)
    else:
        embed = create_embed("エラー", "音声データの準備に失敗しました。", discord.Color.red(), "danger")
        await status_message.edit(embed=embed)
    
    if audio_bytes_io: audio_bytes_io.close()

# # PING COMMAND
@bot.command(name="ping")
@commands.cooldown(1, 5, commands.BucketType.user)
async def ping_command(ctx: commands.Context):
    latency = bot.latency * 1000
    embed = create_embed("Ping", f"現在の応答速度: **{latency:.2f}ms**", discord.Color.green(), "success")
    await ctx.reply(embed=embed, mention_author=False)

@ping_command.error
async def ping_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else: await send_error_embed(ctx, error)

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
def draw_text_layered_outline(draw, base_pos, char_text, font, 
                              text_color,          
                              inner_outline_color,  
                              inner_outline_radius, 
                              outer_outline_color, 
                              outer_outline_radius): 
    x, y = base_pos
    
    for dx_outer in range(-outer_outline_radius, outer_outline_radius + 1):
        for dy_outer in range(-outer_outline_radius, outer_outline_radius + 1):
            if dx_outer*dx_outer + dy_outer*dy_outer <= outer_outline_radius*outer_outline_radius :
                 draw.text((x + dx_outer, y + dy_outer), char_text, font=font, fill=outer_outline_color)
    
    for dx_inner in range(-inner_outline_radius, inner_outline_radius + 1):
        for dy_inner in range(-inner_outline_radius, inner_outline_radius + 1):
            if dx_inner*dx_inner + dy_inner*dy_inner <= inner_outline_radius*inner_outline_radius:
                draw.text((x + dx_inner, y + dy_inner), char_text, font=font, fill=inner_outline_color)
    
    # Layer 3: Main text
    draw.text((x, y), char_text, font=font, fill=text_color)

# ========================== TEXT COMMAND DRAWING HELPER ==========================
async def _generate_text_image_styled(ctx: commands.Context, args: str, 
                                     font_path: str, text_color: tuple, 
                                     inner_outline_color: tuple, inner_outline_thickness: int, 
                                     outer_outline_color: tuple, outer_outline_thickness: int,
                                     embed_color: discord.Color, embed_title: str):
    try:
        make_square = False
        text_to_render = args.strip()
        if text_to_render.lower().endswith(" square"):
            text_to_render = text_to_render[:-7].strip(); make_square = True
        
        if not text_to_render:
            embed = create_embed("引数エラー", "画像にするテキスト内容が空です。", discord.Color.orange(), "warning")
            await ctx.reply(embed=embed, mention_author=False); return

        if not os.path.exists(font_path):
            embed = create_embed("内部エラー", f"フォントファイルが見つかりません: `{os.path.basename(font_path)}`", discord.Color.red(), "danger")
            await ctx.reply(embed=embed, mention_author=False); return

        async with ctx.typing():
            font = ImageFont.truetype(font_path, TEXT_IMAGE_FONT_SIZE_COMMON)
            
            lines_input = text_to_render.split(',')
            max_text_content_width = 0; current_y_for_layout = 0; line_layout_data = []
            letter_spacing_abs = int(TEXT_IMAGE_FONT_SIZE_COMMON * TEXT_IMAGE_LETTER_SPACING_ADJUST_COMMON)
            dummy_draw = ImageDraw.Draw(Image.new("L",(1,1)))
            try:
                ascent, descent = font.getmetrics()
                font_standard_height = ascent + descent
            except AttributeError:
                font_standard_height = TEXT_IMAGE_FONT_SIZE_COMMON

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
                        if i < len(line_text) - 1:
                            line_actual_width += letter_spacing_abs
                        max_char_actual_height_in_line = max(max_char_actual_height_in_line, char_h)
                line_height_for_next = int(max_char_actual_height_in_line * TEXT_IMAGE_LINE_HEIGHT_MULTIPLIER_COMMON) if max_char_actual_height_in_line > 0 else int(font_standard_height * TEXT_IMAGE_LINE_HEIGHT_MULTIPLIER_COMMON)
                line_layout_data.append({"text": line_text, "chars_info": current_line_chars_info, "render_width": line_actual_width, "y_start_in_block": current_y_for_layout, "height_for_next_line": line_height_for_next})
                max_text_content_width = max(max_text_content_width, line_actual_width)
                current_y_for_layout += line_height_for_next
            total_text_content_height = current_y_for_layout
            if max_text_content_width <= 0 or total_text_content_height <= 0:
                await ctx.reply(embed=create_embed("エラー", "テキスト内容から有効なサイズを計算できませんでした。", discord.Color.orange(), "warning"), mention_author=False); return

            outline_total_radius = inner_outline_thickness + (outer_outline_thickness if outer_outline_color else 0)
            temp_canvas_margin = outline_total_radius + TEXT_MASK_ADDITIONAL_MARGIN_COMMON
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
                        text_mask_draw_temp.text((current_x_char_draw, draw_y_char), line_str[i], font=font, fill=255)
                        current_x_char_draw += char_info['width'] + letter_spacing_abs
            
            cropped_outer_layer, cropped_inner_layer, cropped_text_layer_main = None, None, None
            
            if outer_outline_color and outer_outline_thickness > 0:
                radius_for_outer = inner_outline_thickness + outer_outline_thickness
                dilated_mask_outer = text_mask_on_temp_canvas.copy()
                for _ in range(radius_for_outer): dilated_mask_outer = dilated_mask_outer.filter(ImageFilter.MaxFilter(3))
                bbox_outer = dilated_mask_outer.getbbox()
                if bbox_outer: cropped_outer_layer = dilated_mask_outer.crop(bbox_outer)

            if inner_outline_thickness > 0:
                dilated_mask_inner = text_mask_on_temp_canvas.copy()
                for _ in range(inner_outline_thickness): dilated_mask_inner = dilated_mask_inner.filter(ImageFilter.MaxFilter(3))
                bbox_inner = dilated_mask_inner.getbbox()
                if bbox_inner: cropped_inner_layer = dilated_mask_inner.crop(bbox_inner)
            
            bbox_text_main = text_mask_on_temp_canvas.getbbox()
            if bbox_text_main: cropped_text_layer_main = text_mask_on_temp_canvas.crop(bbox_text_main)
            
            content_final_width, content_final_height = 0,0
            if cropped_outer_layer: content_final_width, content_final_height = cropped_outer_layer.size
            elif cropped_inner_layer: content_final_width, content_final_height = cropped_inner_layer.size
            elif cropped_text_layer_main: content_final_width, content_final_height = cropped_text_layer_main.size
            else: await ctx.reply(embed=create_embed("エラー", "描画コンテンツ生成不可。", discord.Color.orange(), "warning"), mention_author=False); return

            final_w = content_final_width + TEXT_IMAGE_PADDING_COMMON * 2
            final_h = content_final_height + TEXT_IMAGE_PADDING_COMMON * 2
            final_canvas = Image.new("RGBA", (final_w, final_h), (0,0,0,0))
            
            y_offset_global = TEXT_IMAGE_VERTICAL_OFFSET_COMMON

            if cropped_outer_layer and outer_outline_color:
                final_canvas.paste(outer_outline_color, ((final_w-cropped_outer_layer.width)//2, (final_h-cropped_outer_layer.height)//2 + y_offset_global), cropped_outer_layer)
            
            if cropped_inner_layer:
                final_canvas.paste(inner_outline_color, ((final_w-cropped_inner_layer.width)//2, (final_h-cropped_inner_layer.height)//2 + y_offset_global), cropped_inner_layer)
            
            if cropped_text_layer_main:
                final_canvas.paste(text_color, ((final_w-cropped_text_layer_main.width)//2, (final_h-cropped_text_layer_main.height)//2 + y_offset_global), cropped_text_layer_main)

            output_image = final_canvas
            if make_square:
                alpha_ch = output_image.getchannel('A'); bbox_sq = alpha_ch.getbbox()
                if bbox_sq:
                    content_sq = output_image.crop(bbox_sq); dim_sq = max(content_sq.width, content_sq.height)
                    if dim_sq > 0:
                        sq_canvas = Image.new("RGBA",(dim_sq,dim_sq),(0,0,0,0)); stretched_sq = content_sq.resize((dim_sq,dim_sq),Image.Resampling.LANCZOS)
                        sq_canvas.paste(stretched_sq,(0,0)); output_image = sq_canvas
            
            img_byte_arr = io.BytesIO(); output_image.save(img_byte_arr, format='PNG'); img_byte_arr.seek(0)
            
            resized_output_io, resized_flag = await _resize_image_if_too_large(img_byte_arr, "PNG")
            if resized_output_io is None: 
                await ctx.reply(embed=create_embed("エラー", "画像のリサイズに失敗しました。", discord.Color.red(), "danger"), mention_author=False)
                img_byte_arr.close(); return
            resized_output_io.seek(0)

            file = discord.File(fp=resized_output_io, filename="text_image.png")
            description_for_embed = f"{STATUS_EMOJIS['info']} 改行はコンマ`,`区切りで スタンプ化は `square` をつけてください"
            embed = create_embed(
                title=embed_title, 
                description=description_for_embed, 
                color=embed_color, 
                status="success"
            )
            embed.set_image(url="attachment://text_image.png")
            
            await ctx.reply(content=None, embed=embed, file=file, mention_author=False)

            img_byte_arr.close()
            if resized_output_io != img_byte_arr and not resized_output_io.closed : 
                resized_output_io.close()

    except Exception as e:
        await send_error_embed(ctx, e)

# # TEXT COMMANDS
@bot.command(name="text")
@commands.cooldown(1, 10, commands.BucketType.user)
async def text_command(ctx: commands.Context, *, args: str):
    await _generate_text_image_styled(ctx, args,
        font_path=TEXT_IMAGE_FONT_PATH_DEFAULT,
        text_color=TEXT_IMAGE_TEXT_COLOR_DEFAULT,
        inner_outline_color=TEXT_IMAGE_OUTLINE_COLOR_BLACK_DEFAULT, 
        inner_outline_thickness=TEXT_IMAGE_OUTLINE_THICKNESS_BLACK_DEFAULT,
        outer_outline_color=TEXT_IMAGE_OUTLINE_COLOR_WHITE_DEFAULT,
        outer_outline_thickness=TEXT_IMAGE_OUTLINE_THICKNESS_WHITE_DEFAULT,
        embed_title="やまかわサムネ風テキスト", 
        embed_color=discord.Color.yellow()
    )

@bot.command(name="text2")
@commands.cooldown(1, 10, commands.BucketType.user)
async def text2_command(ctx: commands.Context, *, args: str):
    await _generate_text_image_styled(ctx, args,
        font_path=TEXT_IMAGE_FONT_PATH_DEFAULT,
        text_color=TEXT_IMAGE_TEXT_COLOR_BLUE,
        inner_outline_color=TEXT_IMAGE_OUTLINE_COLOR_BLACK_DEFAULT, 
        inner_outline_thickness=TEXT_IMAGE_OUTLINE_THICKNESS_BLACK_DEFAULT,
        outer_outline_color=TEXT_IMAGE_OUTLINE_COLOR_WHITE_DEFAULT,
        outer_outline_thickness=TEXT_IMAGE_OUTLINE_THICKNESS_WHITE_DEFAULT,
        embed_title="やまかわ青文字テキスト", 
        embed_color=discord.Color.blue()
    )

@bot.command(name="text3")
@commands.cooldown(1, 10, commands.BucketType.user)
async def text3_command(ctx: commands.Context, *, args: str):
    await _generate_text_image_styled(ctx, args,
        font_path=TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD,
        text_color=TEXT_IMAGE_TEXT_COLOR_RED_NOTO,
        inner_outline_color=TEXT_IMAGE_OUTLINE_COLOR_WHITE_NOTO, 
        inner_outline_thickness=TEXT_IMAGE_OUTLINE_THICKNESS_WHITE_NOTO,
        outer_outline_color=None, # Single outline
        outer_outline_thickness=0,
        embed_title="やまかわ赤文字テキスト", 
        embed_color=discord.Color.from_rgb(0xC3, 0x02, 0x03)
    )

async def text_common_error_handler(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed("引数不足", "画像にするテキストを指定してください。", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else: await send_error_embed(ctx, error)

text_command.error = text_common_error_handler
text2_command.error = text_common_error_handler
text3_command.error = text_common_error_handler


# # TENKI COMMAND (Tsukumijima API with Gemini assist)
@bot.command(name="tenki", aliases=["weather"])
@commands.cooldown(1, 10, commands.BucketType.user)
async def weather_command_tsukumijima(ctx: commands.Context, *, city_name_query: str):
    async with ctx.typing():
        city_id = None
        if not weather_city_id_map: await load_weather_city_codes()
        
        query_lower = city_name_query.lower()
        for name, id_val in weather_city_id_map.items():
            if query_lower == name.lower(): city_id = id_val; break
        
        if not city_id and not GEMINI_API_UNAVAILABLE:
            city_list_excerpt = "\n".join([f"- {name} (ID: {cid})" for name, cid in list(weather_city_id_map.items())[:150]])
            prompt_gemini = (
                f"日本の地名「{city_name_query}」に最も近いと思われる都市のIDを、以下のリストから一つだけ選んで、そのID（数字6桁）のみを返してください。\n"
                f"日本の地名ではない、またはリストから適切なIDが見つからない場合は「不明」とだけ返してください。\n"
                f"リストは:\n{city_list_excerpt}\n\n"
                f"ユーザー入力地名: {city_name_query}\n最も近いID:"
            )
            id_response_gemini = await generate_gemini_text_response([prompt_gemini])

            if not id_response_gemini.startswith("Error:") and id_response_gemini.strip().isdigit():
                potential_id = id_response_gemini.strip()
                if any(cid_val == potential_id for cid_val in weather_city_id_map.values()):
                    city_id = potential_id
                    print(f"Weather: Gemini suggested City ID for '{city_name_query}': {city_id}")
            elif "不明" in id_response_gemini:
                print(f"Weather: Gemini could not determine a city ID for '{city_name_query}'.")
        
        if not city_id:
            embed = create_embed("エラー", f"都市「{city_name_query}」が見つかりませんでした。\nこのコマンドは日本国内の地名のみ利用可能です。", discord.Color.orange(), "warning")
            await ctx.reply(embed=embed, mention_author=False); return

        target_url = f"{WEATHER_API_BASE_URL}{city_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error"):
                            embed = create_embed("APIエラー", data.get("error"), discord.Color.red(), "danger", "つくもAPI")
                            await ctx.reply(embed=embed, mention_author=False); return
                        
                        if data.get("forecasts") and len(data["forecasts"]) > 0:
                            # ★★★ description を含めず、タイトルとフィールドのみで構成 ★★★
                            embed = create_embed(f"{data.get('location', {}).get('city', city_name_query)} の天気予報", "", discord.Color.blue(), "success")
                            embed.set_footer(text=f"杉山啓太Bot / 天気予報API 情報取得時間 : {data.get('publicTimeFormatted', '')}", icon_url=BOT_ICON_URL)
                            embed.timestamp = None
                            for forecast in data["forecasts"][:3]:
                                date = f"{forecast.get('dateLabel', '不明')} ({forecast.get('date')[-5:]})"
                                temp_max = forecast.get("temperature", {}).get("max", {}).get("celsius", "--")
                                temp_min = forecast.get("temperature", {}).get("min", {}).get("celsius", "--")
                                value_str = f"{forecast.get('telop', '情報なし')} (最高:{temp_max}°C / 最低:{temp_min}°C)"
                                embed.add_field(name=date, value=value_str, inline=False)
                            await ctx.reply(embed=embed, mention_author=False)
                        else:
                            embed = create_embed("エラー", f"「{city_name_query}」(ID:{city_id}) の天気予報データを取得できませんでした。", discord.Color.orange(), "warning", "つくもAPI")
                            await ctx.reply(embed=embed, mention_author=False)
                    else:
                        embed = create_embed("APIエラー", f"天気情報の取得に失敗しました。(HTTP: {response.status})", discord.Color.red(), "danger", "つくもAPI")
                        await ctx.reply(embed=embed, mention_author=False)
        except Exception as e: await send_error_embed(ctx, e)

@weather_command_tsukumijima.error
async def weather_command_tsukumijima_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed("引数不足", "都市名を指定してください。\n例: `tenki 東京`", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else: await send_error_embed(ctx, error)

# # INFO COMMAND
@bot.command(name="info")
@commands.cooldown(1, 5, commands.BucketType.user)
async def user_info_command(ctx: commands.Context, member: discord.Member = None):
    target_member = member or ctx.author
    
    embed = create_embed(f"{target_member.display_name} の情報", "", target_member.color or discord.Color.default(), "info")
    if target_member.avatar: embed.set_thumbnail(url=target_member.avatar.url)
    
    embed.add_field(name="ユーザー名", value=f"`{target_member.name}`", inline=True)
    embed.add_field(name="ユーザーID", value=f"`{target_member.id}`", inline=True)
    embed.add_field(name="Bot?", value="はい" if target_member.bot else "いいえ", inline=True)

    embed.add_field(name="アカウント作成日", value=f"<t:{int(target_member.created_at.timestamp())}:D>", inline=True)
    if isinstance(target_member, discord.Member) and target_member.joined_at:
        embed.add_field(name="サーバー参加日", value=f"<t:{int(target_member.joined_at.timestamp())}:R>", inline=True)
    else: embed.add_field(name="サーバー参加日", value="N/A", inline=True)
    if isinstance(target_member, discord.Member) and target_member.premium_since:
        embed.add_field(name="ブースト開始日", value=f"<t:{int(target_member.premium_since.timestamp())}:R>", inline=True)
    else: embed.add_field(name="ブースト開始日", value="なし", inline=True)
    
    badges = []
    flags = target_member.public_flags
    badge_map = {"staff": flags.staff, "partner": flags.partner, "hypesquad_bravery": flags.hypesquad_bravery, "hypesquad_brilliance": flags.hypesquad_brilliance, "hypesquad_balance": flags.hypesquad_balance, "bug_hunter": flags.bug_hunter, "bug_hunter_level_2": flags.bug_hunter_level_2, "early_supporter": flags.early_supporter, "verified_bot": (target_member.bot and flags.verified_bot), "early_verified_bot_developer": flags.early_verified_bot_developer, "discord_certified_moderator": flags.discord_certified_moderator, "active_developer": flags.active_developer, "nitro": (isinstance(target_member, discord.Member) and target_member.premium_since) }
    for badge_name, has_badge in badge_map.items():
        if has_badge:
            emoji = USER_BADGES_EMOJI.get(badge_name)
            if emoji: badges.append(emoji)
    if badges: embed.add_field(name="バッジ", value=" ".join(badges) or "なし", inline=False)
    
    if isinstance(target_member, discord.Member):
        roles = [role.mention for role in sorted(target_member.roles, key=lambda r: r.position, reverse=True) if role.name != "@everyone"]
        if roles:
            roles_str = " ".join(roles); 
            if len(roles_str) > 1000: roles_str = roles_str[:997] + "..."
            embed.add_field(name=f"ロール ({len(roles)})", value=roles_str or "なし", inline=False)
            
    await ctx.reply(embed=embed, mention_author=False)

# # RATE COMMAND
@bot.command(name="rate")
@commands.cooldown(1, 5, commands.BucketType.user)
async def rate_command(ctx: commands.Context, amount_str: str, currency_code: str):
    try: amount = float(amount_str)
    except ValueError:
        embed = create_embed("入力エラー", "金額は有効な数値で入力してください。", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False); return

    currency_code_input = currency_code.upper()
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(EXCHANGE_RATE_API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        target_rate_key = f"{currency_code_input}_JPY"
                        if target_rate_key in data and isinstance(data[target_rate_key], (int, float)):
                            rate_val = data[target_rate_key]; amount_in_jpy = amount * rate_val
                            api_time_utc_str = data.get('datetime', ''); time_str_jst = api_time_utc_str
                            try:
                                api_time_utc = datetime.datetime.fromisoformat(api_time_utc_str.replace("Z", "+00:00"))
                                time_str_jst = api_time_utc.astimezone(JST).strftime('%Y-%m-%d %H:%M') + " JST"
                            except: pass
                            desc = f"**{amount:,.2f} {currency_code_input}** は **{amount_in_jpy:,.2f} 円**です。\n(レート: 1 {currency_code_input} = {rate_val:,.3f} JPY | {time_str_jst}時点)"
                            embed = create_embed("為替レート変換", desc, discord.Color.gold(), "success", "exchange-rate-api.krnk.org")
                            await ctx.reply(embed=embed, mention_author=False)
                        else:
                            available = sorted([k.split('_')[0] for k,v in data.items() if k.endswith("_JPY") and isinstance(v,(int,float))])
                            embed = create_embed("エラー", f"通貨「{currency_code_input}」のレートが見つかりません。\n利用可能(対JPY): `{', '.join(available[:15])}...`", discord.Color.orange(), "warning", "exchange-rate-api.krnk.org")
                            await ctx.reply(embed=embed, mention_author=False)
                    else: await ctx.reply(embed=create_embed("APIエラー", f"為替レートAPIへのアクセスに失敗しました (HTTP: {response.status})", discord.Color.red(), "danger", "exchange-rate-api.krnk.org"), mention_author=False)
        except Exception as e: await send_error_embed(ctx, e)

@rate_command.error
async def rate_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed("引数不足", "金額と通貨コードを指定してください。\n例: `rate 100 USD`", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else: await send_error_embed(ctx, error)

# # SHORTURL COMMAND
@bot.command(name="shorturl", aliases=["short"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def shorturl_command(ctx: commands.Context, *, url_to_shorten: str):
    if not (url_to_shorten.startswith("http://") or url_to_shorten.startswith("https://")): url_to_shorten = "http://" + url_to_shorten
    params = {"url": url_to_shorten}
    if SHORTURL_API_KEY and SHORTURL_API_KEY != "YOUR_XGD_API_KEY_PLACEHOLDER": params["key"] = SHORTURL_API_KEY
    target_url_with_params = f"{SHORTURL_API_ENDPOINT}?{urllib.parse.urlencode(params)}"
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target_url_with_params) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        short_url = None
                        try:
                            data = json.loads(response_text)
                            if isinstance(data, dict) and data.get("status") == 200 and data.get("shorturl"): short_url = data['shorturl']
                        except json.JSONDecodeError:
                             if response_text.startswith("https://x.gd/") or response_text.startswith("http://x.gd/"): short_url = response_text
                        if short_url:
                            embed = create_embed("短縮URLを生成しました", f"```{short_url}```", discord.Color.teal(), "success", "x.gd")
                            await ctx.reply(embed=embed, mention_author=False)
                        else: await ctx.reply(embed=create_embed("エラー", f"URLの短縮に失敗しました。\nAPI応答: `{response_text[:200]}`", discord.Color.orange(), "warning", "x.gd"), mention_author=False)
                    else: await ctx.reply(embed=create_embed("APIエラー", f"URL短縮APIへのアクセスに失敗しました (HTTP: {response.status})。", discord.Color.red(), "danger", "x.gd"), mention_author=False)
        except Exception as e: await send_error_embed(ctx, e)

@shorturl_command.error
async def shorturl_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed("引数不足", "短縮したいURLを指定してください。\n例: `shorturl https://google.com`", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else: await send_error_embed(ctx, error)

# # TOTUSI COMMAND
@bot.command(name="totusi")
@commands.cooldown(1, 3, commands.BucketType.user)
async def totusi_command(ctx: commands.Context, *, text: str):
    text_clean = text.replace("　", " ")
    char_display_width = sum(2 if unicodedata.east_asian_width(c) in ('F', 'W', 'A') else 1 for c in text_clean)
    arrow_count = min(15, max(3, math.ceil(char_display_width / 1.5)))
    line1 = "＿" + "人" * arrow_count + "＿"
    line2 = f"＞　**{text_clean}**　＜"
    line3 = "￣" + ("Y^" * (arrow_count // 2)) + ("Y" if arrow_count % 2 != 0 else "") + ("^Y" * (arrow_count//2)) + "￣"
    embed = create_embed("突然の死", f"{line1}\n{line2}\n{line3}", discord.Color.light_grey(), "success")
    await ctx.reply(embed=embed, mention_author=False)

@totusi_command.error
async def totusi_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed("引数不足", "AAにする文字列を指定してください。\n例: `totusi すごい`", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else: await send_error_embed(ctx, error)

# # TIME COMMAND
class TimeHelpView(discord.ui.View):
    def __init__(self): super().__init__(timeout=60)
    @discord.ui.button(label="国コード一覧を表示", style=discord.ButtonStyle.secondary, emoji="🌍")
    async def show_timezones(self, interaction: discord.Interaction, button: discord.ui.Button):
        help_text_lines = ["利用可能な国/地域コード (一部):"]
        for code, tz_name in sorted(TIMEZONE_MAP.items()):
            help_text_lines.append(f"`{code}`: {tz_name.split('/')[-1].replace('_', ' ')}")
        embed = create_embed("Timeコマンド ヘルプ", "\n".join(help_text_lines), discord.Color.blue(), "info")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

@bot.command(name="time")
@commands.cooldown(1, 3, commands.BucketType.user)
async def time_command(ctx: commands.Context, country_code: str = None):
    if not country_code:
        desc = (f"現在の日本時間は **{datetime.datetime.now(JST).strftime('%H:%M:%S')}** です。\n\n"
                f"{STATUS_EMOJIS['info']} 国コードを指定すると、その国の時刻を表示できます。(例: `time US`)")
        embed = create_embed("現在時刻 (日本時間)", desc, discord.Color.blue(), "info")
        await ctx.reply(embed=embed, view=TimeHelpView(), mention_author=False); return
    
    target_tz_name = TIMEZONE_MAP.get(country_code.upper())
    if not target_tz_name:
        desc = "利用可能な国コードの一覧は下のボタンから確認できます。"
        embed = create_embed("無効な国コード", f"`{country_code}` は見つかりませんでした。\n{desc}", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, view=TimeHelpView(), mention_author=False); return
    
    try:
        target_timezone = pytz.timezone(target_tz_name)
        target_dt = datetime.datetime.now(datetime.timezone.utc).astimezone(target_timezone)
        offset = target_dt.utcoffset()
        offset_hours = offset.total_seconds() / 3600
        offset_str = f"UTC{offset_hours:+g}"
        desc = f"**{target_dt.strftime('%Y-%m-%d %H:%M:%S')}** ({offset_str})"
        embed = create_embed(f"{target_tz_name.split('/')[-1].replace('_', ' ')} の現在時刻", desc, discord.Color.blue(), "success")
        await ctx.reply(embed=embed, mention_author=False)
    except Exception as e: await send_error_embed(ctx, e)

@bot.command(name="amazon")
@commands.cooldown(1, 5, commands.BucketType.user)
async def amazon_shorturl_command(ctx: commands.Context, *, amazon_url: str):
    parsed_url = urllib.parse.urlparse(amazon_url)
    if not (parsed_url.scheme in ["http", "https"] and any(domain in parsed_url.netloc for domain in ["amazon.co.jp", "amzn.asia", "amazon.com"])):
        embed = create_embed("URLエラー", "有効なAmazonのURLを指定してください。", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False); return

    marketplace_id = "6" if "amazon.co.jp" in parsed_url.netloc else "1"
    params = { "longUrl": urllib.parse.quote_plus(amazon_url), "marketplaceId": marketplace_id }
    target_url = f"{AMAZON_SHORTURL_ENDPOINT}?{urllib.parse.urlencode(params, safe='/:')}"
    
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" }
                async with session.get(target_url, headers=headers) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                            if data.get("isOk") and data.get("shortUrl"):
                                embed = create_embed("Amazon短縮URLを生成しました", f"```{data['shortUrl']}```", discord.Color.from_rgb(255, 153, 0), "success", "Amazon Associates")
                                await ctx.reply(embed=embed, mention_author=False)
                            else:
                                embed = create_embed("エラー", f"URLの短縮に失敗しました。\nAPI応答: `{data.get('error', {}).get('message', '不明なエラー')}`", discord.Color.orange(), "warning", "Amazon Associates")
                                await ctx.reply(embed=embed, mention_author=False)
                        except json.JSONDecodeError:
                            embed = create_embed("APIエラー", f"予期しない応答形式でした。\n応答: `{response_text[:200]}`", discord.Color.red(), "danger", "Amazon Associates")
                            await ctx.reply(embed=embed, mention_author=False)
                    else:
                        embed = create_embed("APIエラー", f"APIへのアクセスに失敗しました (HTTP: {response.status})。", discord.Color.red(), "danger", "Amazon Associates")
                        await ctx.reply(embed=embed, mention_author=False)
        except Exception as e: await send_error_embed(ctx, e)

@bot.command(name="bet")
@commands.cooldown(1, 3, commands.BucketType.user)
async def bet_command(ctx: commands.Context, amount_str: str):
    try: amount = int(amount_str)
    except ValueError: await ctx.reply(embed=create_embed("エラー", "賭け金は整数で指定してください。", discord.Color.orange(), "warning"), mention_author=False); return

    player_id = ctx.author.id
    current_points = get_player_points(player_id)

    if amount <= 0: await ctx.reply(embed=create_embed("エラー", "賭け金は1ポイント以上で指定してください。", discord.Color.orange(), "warning"), mention_author=False); return
    if current_points < amount: await ctx.reply(embed=create_embed("ポイント不足", f"ポイントが不足しています。\nあなたのポイント: `{current_points}pt`", discord.Color.orange(), "warning"), mention_author=False); return
    
    async with ctx.typing():
        await asyncio.sleep(random.uniform(0.5, 1.0)) 
        dice_roll = random.randint(1, 6)
        message, payout_multiplier = BET_DICE_PAYOUTS[dice_roll]
        points_change = int(amount * payout_multiplier)
        update_player_points(player_id, points_change)
        
        embed = create_embed(f"ダイスベット結果: {dice_roll}", f"{ctx.author.mention} が `{amount}pt` をベット！", discord.Color.purple(), "info")
        embed.add_field(name="結果", value=message, inline=False)
        embed.add_field(name="ポイント変動", value=f"`{'+' if points_change >=0 else ''}{points_change}pt`", inline=True)
        embed.add_field(name="現在のポイント", value=f"`{get_player_points(player_id)}pt`", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

@bet_command.error
async def bet_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed("引数不足", "賭け金を指定してください。\n例: `bet 10`", discord.Color.orange(), "warning")
        await ctx.reply(embed=embed, mention_author=False)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("クールダウン中", f"このコマンドはあと {error.retry_after:.1f}秒 後に利用できます。", discord.Color.orange(), "pending")
        await ctx.reply(embed=embed, mention_author=False, delete_after=5)
    else: await send_error_embed(ctx, error)


# ========================== BOT EXECUTION ==========================
if __name__ == "__main__":
    print("Starting Bot...")
    if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_PLACEHOLDER": print("CRITICAL ERROR: DISCORD_BOT_TOKEN not set."); exit(1)
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_PLACEHOLDER": print("WARNING: GEMINI_API_KEY not set.")
    if not VOICEVOX_API_KEY or VOICEVOX_API_KEY == "YOUR_VOICEVOX_API_KEY_PLACEHOLDER": print("WARNING: VOICEVOX_API_KEY not set.")
    
    if not os.path.exists(TEXT_IMAGE_FONT_PATH_DEFAULT): print(f"CRITICAL WARNING: Default text font not found: {TEXT_IMAGE_FONT_PATH_DEFAULT}")
    if not os.path.exists(TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD): print(f"WARNING: Noto Serif font not found: {TEXT_IMAGE_FONT_PATH_NOTO_SERIF_BOLD}. 'text3' may fail.")
    
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure: print("CRITICAL ERROR: Invalid Discord Bot Token.")
    except Exception as e: print(f"CRITICAL ERROR during bot execution: {e}"); traceback.print_exc()
