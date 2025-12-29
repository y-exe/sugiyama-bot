# ui/views_connect4.py
import discord
import datetime
from core.config import JST
from core.constants import CF_EMPTY, CF_P1_TOKEN, CF_P2_TOKEN, CONNECTFOUR_MARKERS, COLS
from core.state import state
from engines.connect_four import ConnectFourEngine
from ui.embeds import create_embed

def create_cf_board_embed(game: ConnectFourEngine):
    p1_id = game.players.get(CF_P1_TOKEN)
    p2_id = game.players.get(CF_P2_TOKEN)
    
    board_str = "\n".join("".join(row) for row in game.board)
    nums_str = "".join(CONNECTFOUR_MARKERS)
    
    desc = (f"{CF_P1_TOKEN} <@{p1_id}> vs {CF_P2_TOKEN} <@{p2_id}>\n\n"
            f"{board_str}\n{nums_str}\n\n"
            f"ルール: 列のリアクションを押してコマを落としてください。")
    
    embed = discord.Embed(title=f"四目並べ #{game.game_id}", description=desc, color=discord.Color.blue())
    
    if not game.game_over:
        current_id = game.get_current_player_id()
        embed.add_field(name="手番", value=f"<@{current_id}> ({game.current_player_token})")
    else:
        if game.winner:
            embed.description += f"\n\n**🏆 <@{game.players[game.winner]}> の勝利！**"
            embed.color = discord.Color.gold()
        else:
            embed.description += f"\n\n**🤝 引き分け！**"
            embed.color = discord.Color.light_grey()
            
    embed.timestamp = datetime.datetime.now(JST)
    return embed

class ConnectFourRecruitmentView(discord.ui.View):
    def __init__(self, host: discord.Member, opponent: discord.Member | None):
        super().__init__(timeout=300.0)
        self.host = host
        self.opponent = opponent

    @discord.ui.button(label="承認する", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, i: discord.Interaction, b: discord.ui.Button):
        if self.opponent and i.user.id != self.opponent.id:
            return await i.response.send_message("指名された方のみ参加できます。", ephemeral=True)
        if i.user.id == self.host.id:
            return await i.response.send_message("自分の募集には参加できません。", ephemeral=True)
        
        await self.start_game(i, i.user)

    @discord.ui.button(label="Botと対戦", style=discord.ButtonStyle.secondary)
    async def bot_match(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user.id != self.host.id:
            return await i.response.send_message("募集者のみがBot対戦を開始できます。", ephemeral=True)
        await self.start_game(i, i.client.user)

    async def start_game(self, i: discord.Interaction, p2):
        game = ConnectFourEngine(self.host.id, p2.id)
        game.channel_id = i.channel_id
        game.message_id = i.message.id
        state.active_connectfour_games[game.message_id] = game
        
        embed = create_cf_board_embed(game)
        msg = await i.response.edit_message(content=None, embed=embed, view=None)
        
        # リアクション付与
        for m in CONNECTFOUR_MARKERS:
            await i.message.add_reaction(m)
        
        # 【修正】Botが先行なら思考開始
        if game.get_current_player_id() == i.client.user.id:
             # 循環参照回避のローカルインポート
             from cogs.games import run_connectfour_bot_turn
             import asyncio
             asyncio.create_task(run_connectfour_bot_turn(i.message, game))
        
        self.stop()