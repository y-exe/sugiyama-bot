import os
import discord
from discord.ext import commands, tasks
import google.generativeai as genai
import datetime
import asyncio
import aiohttp
import urllib.parse
import psutil
import json
import io
import random
from PIL import Image, ImageOps # Pillowライブラリ
from collections import deque # ウォーターマーク履歴のため

# --- 環境変数など ---
from dotenv import load_dotenv
load_dotenv() 

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "XXX")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "XXX")
AI_COMMAND_GEMINI_API_KEY = os.getenv("AI_COMMAND_GEMINI_API_KEY", "AIzaSyBAAEKNuon4fYI_ef5L7qORxx0KuuMWr4A")
TEST_GUILD_ID = os.getenv("TEST_GUILD_ID")

if not DISCORD_BOT_TOKEN: print("エラー: DISCORD_BOT_TOKEN 未設定。"); exit()
if not GEMINI_API_KEY: print("警告: メイン GEMINI_API_KEY 未設定。")
if not AI_COMMAND_GEMINI_API_KEY: print("警告: AI_COMMAND_GEMINI_API_KEY 未設定。")

SETTINGS_FILE = "bot_settings.json"
time_announce_channels = set()
soudayo_enabled_channels = set()
JST = datetime.timezone(datetime.timedelta(hours=9), 'JST')
watermark_template_history = deque(maxlen=2)

TEMPLATES_BASE_PATH = os.path.join("assets", "watermark_templates")
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
for t_data in TEMPLATES_DATA:
    try:
        parts = t_data['user_ratio_str'].split('/')
        if len(parts) == 2 and float(parts[1]) != 0: t_data['match_ratio_wh'] = float(parts[0]) / float(parts[1])
        else: raise ValueError("比率形式エラー")
    except Exception as e: print(f"警告: テンプレート '{t_data['name']}' 比率解析エラー: {e}"); t_data['match_ratio_wh'] = 1.0

gemini_model = None; GEMINI_API_UNAVAILABLE = False
if GEMINI_API_KEY:
    try: genai.configure(api_key=GEMINI_API_KEY); gemini_model = genai.GenerativeModel('gemini-1.5-flash'); print(f"メインGemini APIモデル '{gemini_model.model_name}' をロード。")
    except Exception as e: print(f"メインGemini API初期化失敗: {e}"); GEMINI_API_UNAVAILABLE = True
else: GEMINI_API_UNAVAILABLE = True

ai_command_gemini_model = None; AI_COMMAND_GEMINI_API_UNAVAILABLE = False
if AI_COMMAND_GEMINI_API_KEY:
    try: ai_command_gemini_model = genai.GenerativeModel('gemini-1.5-flash'); print(f"/ai専用Gemini APIモデル '{ai_command_gemini_model.model_name}' インスタンス準備完了。")
    except Exception as e: print(f"/ai専用Geminiモデルインスタンス準備失敗: {e}"); AI_COMMAND_GEMINI_API_UNAVAILABLE = True
else: AI_COMMAND_GEMINI_API_UNAVAILABLE = True

ai_conversation_history = {}; CONVERSATION_HISTORY_TIMEOUT = datetime.timedelta(minutes=15); MAX_HISTORY_MESSAGES = 10

def load_settings():
    global time_announce_channels, soudayo_enabled_channels
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: settings_data = json.load(f)
            time_announce_channels = set(settings_data.get("time_announce_channels", [])); soudayo_enabled_channels = set(settings_data.get("soudayo_enabled_channels", []))
            print(f"設定を '{SETTINGS_FILE}' からロード。")
        else: print(f"'{SETTINGS_FILE}' 未発見。空設定で開始。"); time_announce_channels, soudayo_enabled_channels = set(), set(); save_settings()
    except Exception as e: print(f"設定ロードエラー: {e}。空設定で開始。"); time_announce_channels, soudayo_enabled_channels = set(), set()

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump({"time_announce_channels": list(time_announce_channels), "soudayo_enabled_channels": list(soudayo_enabled_channels)}, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"設定保存エラー: {e}")

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_guild_id_str = TEST_GUILD_ID; self.active_test_guild_id = None
        if self.test_guild_id_str:
            try: self.active_test_guild_id = int(self.test_guild_id_str)
            except ValueError: print(f"警告: TEST_GUILD_ID ('{self.test_guild_id_str}') 無効。グローバル同期。"); self.active_test_guild_id = None
    
    async def setup_hook(self):
        # 設定ファイルのロード
        load_settings() 

        # コマンドツリーの同期
        if self.active_test_guild_id:
            guild = discord.Object(id=self.active_test_guild_id); self.tree.copy_global_to(guild=guild); await self.tree.sync(guild=guild)
            print(f"スラッシュコマンドをテストギルド {self.active_test_guild_id} に同期。")
        else: 
            await self.tree.sync()
            print("スラッシュコマンドをグローバルに同期。")
        
        # WebSocketに依存しない初期化処理はここに残せる
        # 例: データベース接続など (今回はなし)

intents = discord.Intents.default(); intents.message_content = True; intents.messages = True; intents.guilds = True
bot = MyBot(command_prefix='!', intents=intents)

async def generate_gemini_text(prompt: str, model_instance=None, api_key_to_use=None) -> str:
    global GEMINI_API_UNAVAILABLE, AI_COMMAND_GEMINI_API_UNAVAILABLE
    current_model = model_instance or gemini_model
    is_ai_cmd = (current_model == ai_command_gemini_model and api_key_to_use == AI_COMMAND_GEMINI_API_KEY)
    if not current_model: return "エラー: Geminiモデルインスタンス未準備。"
    if is_ai_cmd and (AI_COMMAND_GEMINI_API_UNAVAILABLE or not AI_COMMAND_GEMINI_API_KEY): return f"エラー: /ai専用Gemini API利用不可(キー:{not AI_COMMAND_GEMINI_API_KEY}, 初期化:{AI_COMMAND_GEMINI_API_UNAVAILABLE})。"
    if not is_ai_cmd and (GEMINI_API_UNAVAILABLE or not GEMINI_API_KEY): return f"エラー: メインGemini API利用不可(キー:{not GEMINI_API_KEY}, 初期化:{GEMINI_API_UNAVAILABLE})。"
    key_switched = False; main_key_was_set = GEMINI_API_KEY is not None
    try:
        if api_key_to_use: genai.configure(api_key=api_key_to_use); key_switched = True
        response = await asyncio.to_thread(current_model.generate_content, prompt)
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts: return response.candidates[0].content.parts[0].text
        fb = response.prompt_feedback; return f"応答生成不可。プロンプトブロックの可能性 (理由: {fb.block_reason},詳細: {fb.block_reason_message})."
    except genai.types.generation_types.BlockedPromptException as e: return f"応答生成不可。プロンプトブロック: {e}"
    except genai.types.generation_types.StopCandidateException as e: return f"応答生成が途中で停止: {e}"
    except genai.types.ResourceExhausted as e: 
        if is_ai_cmd: AI_COMMAND_GEMINI_API_UNAVAILABLE = True
        else: GEMINI_API_UNAVAILABLE = True
        return f"APIリソース制限: {e}。"
    except Exception as e: return f"Gemini API予期せぬエラー: {e}"
    finally:
        if key_switched and main_key_was_set:
            try: genai.configure(api_key=GEMINI_API_KEY)
            except Exception as e_reconf: print(f"メインAPIキー再設定失敗: {e_reconf}"); GEMINI_API_UNAVAILABLE = True
        elif key_switched and not main_key_was_set: print("警告: APIキー切り替え後、戻すべきメインAPIキーなし。")

async def generate_summary(text: str, num_points: int = 3) -> str:
    prompt = f"以下の内容を{num_points}つの短い箇条書きで要約してください。\n\n{text}"
    return await generate_gemini_text(prompt, model_instance=gemini_model, api_key_to_use=GEMINI_API_KEY)

@bot.event
async def on_ready():
    print(f'ログイン: {bot.user.name} ({bot.user.id})'); print('------')
    m_stat = "可" if not (GEMINI_API_UNAVAILABLE or not GEMINI_API_KEY or not gemini_model) else "不可"
    ai_stat = "可" if not (AI_COMMAND_GEMINI_API_UNAVAILABLE or not AI_COMMAND_GEMINI_API_KEY or not ai_command_gemini_model) else "不可"
    print(f"メインGemini: {m_stat} | /ai専用Gemini: {ai_stat}")

    # ステータスメッセージの設定 (on_readyに移動)
    try:
        await bot.change_presence(activity=discord.Game(name="杉山啓太Bot βVer"))
        print("ステータスメッセージ設定。")
    except Exception as e_presence:
        print(f"ステータスメッセージ設定失敗: {e_presence}")

    # 時報タスクの開始 (on_readyに移動)
    if not time_announcement_task.is_running(): 
        try:
            time_announcement_task.start()
            # print("時報タスクを開始しました。") # before_loopでログが出るので通常は不要
        except RuntimeError as e_task_start: # 既に開始しようとしている場合など
            print(f"時報タスクの開始に失敗: {e_task_start}")
            if time_announcement_task.is_running():
                 print("時報タスクは既に実行中です。")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user: return
    if message.channel.id in soudayo_enabled_channels and message.content == "そうだよ":
        try: await message.channel.send("そうだよ(便乗)")
        except Exception as e: print(f"そうだよ便乗エラー: {e}")
    await bot.process_commands(message)

def _process_and_composite_image(uploaded_bytes: bytes, template: dict) -> io.BytesIO:
    try:
        base = Image.open(io.BytesIO(uploaded_bytes)); target_w, target_h = template['target_size']
        processed_base = ImageOps.fit(base, (target_w, target_h), Image.Resampling.LANCZOS, centering=(0.5,0.5))
        overlay_path = os.path.join(TEMPLATES_BASE_PATH, template['name'])
        if not os.path.exists(overlay_path): raise FileNotFoundError(f"テンプレート未発見: {overlay_path}")
        overlay = Image.open(overlay_path).convert("RGBA").resize((target_w, target_h), Image.Resampling.LANCZOS)
        if processed_base.mode != 'RGBA': processed_base = processed_base.convert('RGBA')
        final_img = Image.alpha_composite(processed_base, overlay)
        buf = io.BytesIO(); final_img.save(buf, format="PNG"); buf.seek(0); return buf
    except Exception as e: print(f"画像処理エラー: {e}"); raise RuntimeError(f"画像処理中エラー: {e}") from e

# --- コマンドリスト ---
@bot.tree.command(name="help", description="コマンド一覧と説明を表示します。")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="杉山啓太Bot βVer コマンド一覧", color=discord.Color.blue())
    embed.add_field(name="/imakita", value="過去30分のチャットを3行で要約。(実行者のみ)", inline=False)
    embed.add_field(name="!ggrks (返信で実行)", value="返信先メッセージを要約しGoogle検索を促す。", inline=False)
    embed.add_field(name="/ggr [検索語]", value="指定語を3行で簡潔に説明。(実行者のみ)", inline=False)
    embed.add_field(name="/5000choyen [上文字列] [下文字列] ...", value="5000兆円欲しいジェネレーター画像作成。", inline=False)
    embed.add_field(name="/ai [メッセージ]", value="AIと会話。過去15分程度の会話履歴を記憶。(実行者のみ)", inline=False)
    embed.add_field(name="/watermark [画像]", value="アップロード画像にフレームを合成。", inline=False)
    embed.add_field(name="/cat", value="ランダムな猫画像を表示。", inline=False)
    embed.add_field(name="/settimeannounce (管理者)", value="このチャンネルの時報を有効/無効化。", inline=False)
    embed.add_field(name="/setsoudayo (管理者)", value="このチャンネルの「そうだよ(便乗)」を有効/無効化。", inline=False)
    embed.add_field(name="/resetgemini (管理者)", value="メインGemini APIの利用不可フラグをリセット。", inline=False)
    embed.add_field(name="/performance", value="Botのパフォーマンス情報を表示。(実行者のみ)", inline=False)
    embed.add_field(name="/help", value="このヘルプを表示。(実行者のみ)", inline=False)
    m_stat = "可" if not (GEMINI_API_UNAVAILABLE or not GEMINI_API_KEY or not gemini_model) else "不可"
    ai_stat = "可" if not (AI_COMMAND_GEMINI_API_UNAVAILABLE or not AI_COMMAND_GEMINI_API_KEY or not ai_command_gemini_model) else "不可"
    embed.set_footer(text=f"メインLLM({m_stat}) | /ai専用LLM({ai_stat})")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="performance", description="Botの現在のパフォーマンス情報を表示します。")
async def performance_slash(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True); ping = round(bot.latency * 1000)
    mem = psutil.Process(os.getpid()).memory_info(); ram_mb, sys_ram_pct = mem.rss / (1024*1024), psutil.virtual_memory().percent
    embed = discord.Embed(title="Botパフォーマンス", color=discord.Color.purple())
    embed.add_field(name="Ping", value=f"{ping} ms"); embed.add_field(name="Bot RAM", value=f"{ram_mb:.2f} MB"); embed.add_field(name="Sys RAM %", value=f"{sys_ram_pct:.1f}%")
    m_stat = "可" if not (GEMINI_API_UNAVAILABLE or not GEMINI_API_KEY or not gemini_model) else "不可"
    ai_stat = "可" if not (AI_COMMAND_GEMINI_API_UNAVAILABLE or not AI_COMMAND_GEMINI_API_KEY or not ai_command_gemini_model) else "不可"
    embed.add_field(name="LLMステータス", value=f"メイン({m_stat}), /ai専用({ai_stat})", inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="imakita", description="今北産業機能＝過去30分のチャット内容を3行で要約します。")
async def imakita_slash(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not isinstance(interaction.channel, discord.TextChannel): await interaction.followup.send("テキストチャンネル専用。", ephemeral=True); return
    history = [f"{m.author.display_name}: {m.content}" async for m in interaction.channel.history(limit=200, after=discord.utils.utcnow() - datetime.timedelta(minutes=30)) if m.author != bot.user and m.content]
    if not history: await interaction.followup.send("過去30分メッセージなし。", ephemeral=True); return
    summary = await generate_summary("\n".join(reversed(history)), 3)
    if summary.startswith("エラー:") or summary.startswith("応答生成不可"): await interaction.followup.send(f"要約失敗:\n{summary}", ephemeral=True)
    else: await interaction.followup.send(f"**今北産業(過去30分):**\n{summary}", ephemeral=True)

@bot.command(name="ggrks", help="返信先メッセージを要約しGoogle検索を促す。")
async def ggrks_prefix(ctx: commands.Context):
    async with ctx.typing():
        if not ctx.message.reference or not (msg := await ctx.fetch_message(ctx.message.reference.message_id)): await ctx.send("質問メッセージに返信して実行。"); return
        if not msg.content: await ctx.send("返信先内容なし。"); return
        summary = await generate_summary(msg.content, 3); s_url = f"https://www.google.com/search?q={urllib.parse.quote(msg.content[:150])}"
        if summary.startswith("エラー:") or summary.startswith("応答生成不可"): await ctx.send(f"要約失敗:\n{summary}\n[Google検索]({s_url})")
        else: await ctx.send(embed=discord.Embed(title="ggrks", description=f"**質問要点:**\n{summary}\n[Google検索]({s_url})", color=discord.Color.green()))

@bot.tree.command(name="ggrks", description="!ggrks コマンドの使い方を説明します。")
async def ggrks_slash_info(interaction: discord.Interaction):
    await interaction.response.send_message(embed=discord.Embed(title="`!ggrks`コマンド", description="メッセージに返信し`!ggrks`で内容要約とGoogle検索を促します。", color=discord.Color.blue()), ephemeral=True)

@bot.tree.command(name="ggr", description="Google検索を行い、3行でまとめてくれます。")
@discord.app_commands.describe(search_term="検索語")
async def ggr_slash(interaction: discord.Interaction, search_term: str):
    await interaction.response.defer(ephemeral=True)
    summary = await generate_gemini_text(f"「{search_term}」を3行箇条書きで簡潔に説明。", model_instance=gemini_model, api_key_to_use=GEMINI_API_KEY)
    if summary.startswith("エラー:") or summary.startswith("応答生成不可"): await interaction.followup.send(f"説明取得失敗:\n{summary}", ephemeral=True)
    else: await interaction.followup.send(embed=discord.Embed(title=f"「{search_term}」の簡単説明", description=summary, color=discord.Color.blue()), ephemeral=True)

@bot.tree.command(name="5000choyen", description="「5000兆円欲しい！」画像を作成。")
@discord.app_commands.describe(top_text="上文字列", bottom_text="下文字列", hoshii="「欲しい！」代わりの文字(true/false)", rainbow="虹色(true/false)")
async def five_thousand_choyen_slash(interaction: discord.Interaction, top_text: str, bottom_text: str, hoshii: bool = False, rainbow: bool = False):
    await interaction.response.defer()
    params = {"top": top_text, "bottom": bottom_text, "hoshii": str(hoshii).lower(), "rainbow": str(rainbow).lower()}
    url = f"https://gsapi.cbrx.io/image?{urllib.parse.urlencode(params)}"
    try:
        async with aiohttp.ClientSession() as s, s.get(url) as r:
            if r.status == 200: await interaction.followup.send(embed=discord.Embed(title="5000兆円欲しい！", color=discord.Color.gold()).set_image(url=url))
            else: await interaction.followup.send(f"画像生成失敗 (API状態: {r.status})", ephemeral=True)
    except Exception as e: await interaction.followup.send(f"画像生成中エラー: {e}", ephemeral=True)

@bot.tree.command(name="ai", description="AIと会話(過去15分程度の会話履歴を記憶＆個人ごとに保存)。")
@discord.app_commands.describe(text="メッセージ")
async def ai_slash(interaction: discord.Interaction, text: str):
    await interaction.response.defer(ephemeral=True); user_id = interaction.user.id
    if not AI_COMMAND_GEMINI_API_KEY or not ai_command_gemini_model or AI_COMMAND_GEMINI_API_UNAVAILABLE:
        msg = "エラー: /ai専用Gemini APIが"; msg += "キー未設定。" if not AI_COMMAND_GEMINI_API_KEY else "モデル準備失敗。" if not ai_command_gemini_model else "一時利用不可。"
        await interaction.followup.send(msg, ephemeral=True); return
    now = discord.utils.utcnow(); history = ai_conversation_history.setdefault(user_id, deque(maxlen=MAX_HISTORY_MESSAGES))
    while history and (now - history[0][0]) > CONVERSATION_HISTORY_TIMEOUT: history.popleft()
    prompt_parts = ["以前の会話:"] if history else ["これは新しい会話です。"]
    for _, role, msg_text in history: prompt_parts.append(f"{'あなた' if role == 'user' else 'AI'}: {msg_text}")
    prompt_parts.extend([f"あなたの質問: {text}", "\nAIの応答 (日本語で):"]); final_prompt = "\n".join(prompt_parts)
    response = await generate_gemini_text(final_prompt, model_instance=ai_command_gemini_model, api_key_to_use=AI_COMMAND_GEMINI_API_KEY)
    if not response.startswith("エラー:") and not response.startswith("応答生成不可"): history.append((now, "user", text)); history.append((now, "bot", response))
    if len(response) > 1950:
        parts = [response[i:i+1950] for i in range(0, len(response), 1950)]; await interaction.followup.send(parts[0], ephemeral=True)
        for part in parts[1:]:
            try: await interaction.user.send(f"AI応答(続き):\n{part}")
            except discord.Forbidden: await interaction.channel.send(f"{interaction.user.mention} AI応答(続き):\n{part}", allowed_mentions=discord.AllowedMentions.none())
            except Exception as e: print(f"/ai続きDM送信エラー: {e}")
    else: await interaction.followup.send(response, ephemeral=True)

@bot.tree.command(name="settimeannounce", description="このチャンネルの時報を有効/無効化。(管理者)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def set_time_announce_slash(interaction: discord.Interaction):
    act = "有効" if interaction.channel_id not in time_announce_channels else "無効"
    if act == "有効": time_announce_channels.add(interaction.channel_id)
    else: time_announce_channels.remove(interaction.channel_id)
    await interaction.response.send_message(f"時報を{act}化しました。", ephemeral=True); save_settings()
@set_time_announce_slash.error
async def set_time_announce_error(i: discord.Interaction, e): await i.response.send_message("管理者権限が必要です。" if isinstance(e, discord.app_commands.MissingPermissions) else f"コマンドエラー: {e}", ephemeral=True)

@bot.tree.command(name="cat", description="ランダムな猫画像を表示。")
async def cat_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        async with aiohttp.ClientSession() as s, s.get(f"https://cataas.com/cat?timestamp={discord.utils.utcnow().timestamp()}") as r:
            if r.status == 200: await interaction.followup.send(embed=discord.Embed(title="にゃーん！", color=discord.Color.random()).set_image(url=str(r.url)))
            else: await interaction.followup.send(f"猫画像取得失敗 (API状態: {r.status})。", ephemeral=True)
    except Exception as e: await interaction.followup.send(f"猫画像取得中エラー: {e}", ephemeral=True)

@bot.tree.command(name="setsoudayo", description="このチャンネルの「そうだよ(便乗)」を有効/無効化。(管理者)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def set_soudayo_slash(interaction: discord.Interaction):
    act = "有効" if interaction.channel_id not in soudayo_enabled_channels else "無効"
    if act == "有効": soudayo_enabled_channels.add(interaction.channel_id)
    else: soudayo_enabled_channels.remove(interaction.channel_id)
    await interaction.response.send_message(f"「そうだよ(便乗)」を{act}化。", ephemeral=True); save_settings()
@set_soudayo_slash.error
async def set_soudayo_error(i: discord.Interaction, e): await i.response.send_message("管理者権限が必要です。" if isinstance(e, discord.app_commands.MissingPermissions) else f"コマンドエラー: {e}", ephemeral=True)

@bot.tree.command(name="resetgemini", description="メインGemini API利用不可フラグをリセット。(管理者)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def reset_gemini_slash(interaction: discord.Interaction):
    global GEMINI_API_UNAVAILABLE, gemini_model; msg = []
    if not GEMINI_API_KEY: msg.append("メインGemini APIキー未設定。")
    elif GEMINI_API_UNAVAILABLE or not gemini_model:
        msg.append("メインGemini API再初期化試行..."); 
        try: genai.configure(api_key=GEMINI_API_KEY); gemini_model = genai.GenerativeModel('gemini-1.5-flash'); GEMINI_API_UNAVAILABLE = False; msg.append(f"メインGemini API({gemini_model.model_name})再初期化成功。")
        except Exception as e: GEMINI_API_UNAVAILABLE = True; msg.append(f"メインGemini API再初期化失敗: {e}")
    else: msg.append("メインGemini APIは利用可能です。")
    await interaction.response.send_message("\n".join(msg), ephemeral=True)
@reset_gemini_slash.error
async def reset_gemini_error(i: discord.Interaction, e): await i.response.send_message("管理者権限が必要です。" if isinstance(e, discord.app_commands.MissingPermissions) else f"コマンドエラー: {e}", ephemeral=True)

@bot.tree.command(name="watermark", description="アップロード画像にフレームを合成。")
@discord.app_commands.describe(image="加工する画像")
async def watermark_slash(interaction: discord.Interaction, image: discord.Attachment):
    global watermark_template_history
    await interaction.response.defer(ephemeral=False)
    if not image.content_type or not image.content_type.startswith("image/"): await interaction.followup.send("画像ファイルをアップロード下さい。", ephemeral=True); return
    if not TEMPLATES_DATA or not os.path.exists(TEMPLATES_BASE_PATH) or not os.listdir(TEMPLATES_BASE_PATH): await interaction.followup.send("エラー: テンプレート設定/フォルダ不備。", ephemeral=True); return
    try:
        img_bytes = await image.read()
        try: pil_img = Image.open(io.BytesIO(img_bytes)); up_w, up_h = pil_img.size; pil_img.close()
        except Exception as e_pil: print(f"Pillow画像オープンエラー: {e_pil}"); await interaction.followup.send("アップロード画像を解析できませんでした。", ephemeral=True); return
        if up_w == 0 or up_h == 0: await interaction.followup.send("画像サイズ無効。", ephemeral=True); return
        up_ratio = up_w / up_h
        min_diff, candidates = float('inf'), []; valid_templates = [t for t in TEMPLATES_DATA if 'match_ratio_wh' in t and os.path.exists(os.path.join(TEMPLATES_BASE_PATH, t['name']))]
        if not valid_templates: await interaction.followup.send("エラー: 利用可能な有効なテンプレートがありません。",ephemeral=True); return
        for t in valid_templates:
            diff = abs(t['match_ratio_wh'] - up_ratio)
            if diff < min_diff: min_diff, candidates = diff, [t]
            elif diff == min_diff: candidates.append(t)
        if not candidates: await interaction.followup.send("エラー: 適合テンプレートが見つかりませんでした。", ephemeral=True); return
        history_list = list(watermark_template_history); last_used = history_list[-1] if len(history_list) >= 1 else None; selected_template = None
        preferred = [t for t in candidates if t['name'] != last_used]
        if preferred:
            second_last_used = history_list[-2] if len(history_list) >= 2 else None; final_choices = [t for t in preferred if t['name'] != second_last_used]
            selected_template = random.choice(final_choices if final_choices else preferred)
        else:
            if candidates and last_used and all(t['name'] == last_used for t in candidates): await interaction.followup.send(f"今回は適切なフレームが見つかりませんでした (連続使用を避けるため「{last_used}」以外を探しましたが他になし)。別の画像を試すか後ほど再試行ください。", ephemeral=True); return
            elif candidates: selected_template = random.choice(candidates)
            else: await interaction.followup.send("エラー: 適合テンプレートなし。", ephemeral=True); return
        if not selected_template:
            if candidates: selected_template = random.choice(candidates); print("警告: ウォーターマーク選択フォールバック作動")
            else: await interaction.followup.send("致命的エラー: テンプレート選択失敗。", ephemeral=True); return
        print(f"選択されたテンプレート: {selected_template['name']}")
        final_buf = await asyncio.to_thread(_process_and_composite_image, img_bytes, selected_template)
        d_file = discord.File(fp=final_buf, filename=f"watermarked_{image.filename}.png"); watermark_template_history.append(selected_template['name'])
        await interaction.followup.send(f"画像加工完了！(使用: {selected_template['name']})", file=d_file)
    except FileNotFoundError as e: await interaction.followup.send(f"エラー: 必要なファイルが見つかりませんでした ({e})。", ephemeral=True)
    except RuntimeError as e: await interaction.followup.send(f"{e}", ephemeral=True)
    except Exception as e: print(f"Watermarkコマンドで予期せぬエラー: {e}"); import traceback; traceback.print_exc(); await interaction.followup.send(f"画像処理中に予期せぬエラー。", ephemeral=True)

@tasks.loop(hours=1)
async def time_announcement_task():
    now_jst = discord.utils.utcnow().astimezone(JST)
    embed = discord.Embed(title="時報", description=f"ただ今の時刻は **{now_jst.hour}時** です。", color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
    embed.set_footer(text=f"{bot.user.name} ")
    for channel_id in list(time_announce_channels):
        channel = bot.get_channel(channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            try: await channel.send(embed=embed)
            except discord.Forbidden: print(f"ChID {channel_id} 時報送信権限なし。"); time_announce_channels.discard(channel_id); save_settings()
            except Exception as e_task: print(f"ChID {channel_id} 時報送信中エラー: {e_task}")
        elif not channel: print(f"時報ChID {channel_id} 未発見。"); time_announce_channels.discard(channel_id); save_settings()

@time_announcement_task.before_loop
async def before_time_announcement_task():
    await bot.wait_until_ready()
    now_jst = discord.utils.utcnow().astimezone(JST)
    next_run_target_jst = (now_jst + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    wait_seconds = (next_run_target_jst - now_jst).total_seconds(); 
    if wait_seconds <= 0: wait_seconds += 3600
    print(f"時報タスク: 次回実行 {next_run_target_jst.strftime('%H:%M:%S')} ({wait_seconds:.0f}秒後)。")
    if wait_seconds > 0: await asyncio.sleep(wait_seconds)

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN: print("エラー: DISCORD_BOT_TOKENが設定されていません。")
    else:
        try: bot.run(DISCORD_BOT_TOKEN)
        except discord.LoginFailure: print("エラー: 不正なDiscord Botトークンです。")
        except KeyboardInterrupt: print("Botを手動で終了します...")
        except Exception as e: print(f"Bot実行中予期せぬエラー: {e}"); import traceback; traceback.print_exc()
        finally: print("Botを終了しました。")
