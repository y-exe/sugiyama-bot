# ui/views_othello.py
import discord
import asyncio
import random
import datetime
from core.config import JST
from core.constants import BLACK, WHITE, EMPTY, BLACK_STONE, WHITE_STONE, GREEN_SQUARE, STATUS_EMOJIS
from core.state import state
from engines.othello import OthelloEngine
from data.points_manager import points_manager
from ui.embeds import create_embed

def build_othello_embed(game_session: dict) -> discord.Embed:
    game = game_session["game"]
    p_black_id = game.players.get(BLACK)
    p_white_id = game.players.get(WHITE)
    
    # ポイント表示の復元
    def get_p_str(uid):
        # Bot判定 (IDがbot.user.idと一致するかどうかはここでは不明なので簡易判定)
        # points_managerから取得して0ならBotまたは新規とみなす
        pt = points_manager.get_points(uid)
        return f"<@{uid}> (Pt: {pt})"

    current_player_id = game.get_current_player_id()
    
    title = f"オセロゲーム #{game.game_id} ({game.board_size}x{game.board_size})"
    color = discord.Color.green() if not game.game_over else discord.Color.dark_grey()
    embed = discord.Embed(title=title, color=color)
    
    board_lines = []
    if not game.game_over:
        game.calculate_valid_moves(game.current_player)
    
    for r in range(game.board_size):
        row_str = ""
        for c in range(game.board_size):
            # マーカーがある場合はそれを表示、なければ石か空きマス
            marker = game.valid_moves_with_markers.get((r, c))
            if marker:
                row_str += marker
            else:
                stone_val = game.board[r][c]
                if stone_val == BLACK: row_str += BLACK_STONE
                elif stone_val == WHITE: row_str += WHITE_STONE
                else: row_str += GREEN_SQUARE
        board_lines.append(row_str)
    
    desc = f"{BLACK_STONE} {get_p_str(p_black_id)} vs {WHITE_STONE} {get_p_str(p_white_id)}\n\n"
    desc += "\n".join(board_lines)
    embed.description = desc
    
    b_score = sum(r.count(BLACK) for r in game.board)
    w_score = sum(r.count(WHITE) for r in game.board)
    embed.add_field(name="スコア", value=f"{BLACK_STONE} {b_score} - {WHITE_STONE} {w_score}", inline=True)
    
    if not game.game_over:
        embed.add_field(name="手番", value=f"<@{current_player_id}>", inline=True)
        embed.set_footer(text="石を置きたい場所のリアクションを押してください。")
    else:
        embed.add_field(name="状態", value="**ゲーム終了**", inline=True)
    
    embed.timestamp = datetime.datetime.now(JST)
    return embed

class OthelloSizeSelectView(discord.ui.View):
    def __init__(self, host, opponent):
        super().__init__(timeout=180.0)
        self.host = host
        self.opponent = opponent
        self.selected_size = None
        self.message = None

    async def start_recruitment(self, i: discord.Interaction, size: int):
        if self.selected_size: return
        self.selected_size = size
        
        host_pt = points_manager.get_points(self.host.id)
        if self.opponent:
            desc = (f"{STATUS_EMOJIS['pending']} {self.host.mention} が {self.opponent.mention} に **{size}x{size}** の対戦を申し込みました。\n\n"
                    f"▫️ {self.opponent.mention} さんが参加する場合は **承認** ボタンを押してください。\n"
                    f"▫️ {self.host.mention} さんが取り消す場合は **キャンセル** ボタンを押してください。")
        else:
            desc = (f"{STATUS_EMOJIS['pending']} {self.host.mention} (Pt: `{host_pt}`) さんが **{size}x{size}** の対戦相手を募集しています。\n\n"
                    f"▫️ 参加したい方は **承認** ボタンを押してください。\n"
                    f"▫️ Botと対戦したい場合は **Botと対戦** ボタンを押してください。\n"
                    f"▫️ {self.host.mention} さんが取り消す場合は **キャンセル** ボタンを押してください。")
        
        embed = create_embed("オセロ対戦者募集", desc, discord.Color.blue(), "info")
        view = OthelloRecruitmentView(self.host, self.opponent, size)
        
        await i.response.edit_message(content=self.opponent.mention if self.opponent else None, embed=embed, view=view)
        view.message = await i.original_response()
        self.stop()

    @discord.ui.button(label="6x6", style=discord.ButtonStyle.secondary)
    async def s6(self, i, b): await self.start_recruitment(i, 6)
    @discord.ui.button(label="8x8", style=discord.ButtonStyle.primary)
    async def s8(self, i, b): await self.start_recruitment(i, 8)
    @discord.ui.button(label="10x10", style=discord.ButtonStyle.secondary)
    async def s10(self, i, b): await self.start_recruitment(i, 10)
    
    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user.id != self.host.id:
            await i.response.send_message("募集者のみが選択できます。", ephemeral=True)
            return False
        return True

class OthelloRecruitmentView(discord.ui.View):
    def __init__(self, host, opponent, board_size):
        super().__init__(timeout=300.0)
        self.host = host
        self.opponent = opponent
        self.board_size = board_size
        self.message = None
        if opponent: self.bot_btn.disabled = True

    async def start_game(self, i: discord.Interaction, opponent):
        for item in self.children: item.disabled = True
        await i.message.edit(view=self)
        
        # ゲーム初期化
        players = [self.host.id, opponent.id]
        random.shuffle(players)
        game = OthelloEngine(self.board_size)
        game.players = {BLACK: players[0], WHITE: players[1]}
        game.channel_id = i.channel_id
        game.message_id = i.message.id
        
        session = {"game": game, "players": game.players, "host_id": self.host.id}
        state.active_games[i.message.id] = session
        
        # 盤面表示
        embed = build_othello_embed(session)
        await i.message.edit(content=None, embed=embed, view=None)
        
        # 初回Bot判定などはCog側で行うが、ここでは「ゲーム開始した」事実だけ作る
        # Cog側の start_game_logic を呼ぶのが理想
        from cogs.games import start_othello_logic
        await start_othello_logic(i.message, session, i.client)
        
        self.stop()

    @discord.ui.button(label="承認する", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, i, b):
        if (self.opponent and i.user.id != self.opponent.id) or (not self.opponent and i.user.id == self.host.id):
            return await i.response.send_message("許可されていません。", ephemeral=True)
        await i.response.defer()
        await self.start_game(i, i.user)

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel(self, i, b):
        if i.user.id != self.host.id: return await i.response.send_message("募集者のみがキャンセルできます。", ephemeral=True)
        embed = create_embed("キャンセル", f"{self.host.mention}が募集を取り消しました。", discord.Color.red(), "danger")
        await i.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="Botと対戦", style=discord.ButtonStyle.secondary, custom_id="bot_btn")
    async def bot_btn(self, i, b):
        if i.user.id != self.host.id: return await i.response.send_message("募集者のみが開始できます。", ephemeral=True)
        await i.response.defer()
        await self.start_game(i, i.client.user)