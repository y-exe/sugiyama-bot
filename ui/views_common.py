# ui/views_common.py
import discord
from core.constants import EMPTY, BLACK, WHITE, CF_P1_TOKEN, CF_P2_TOKEN
from ui.embeds import create_embed

class ConfirmLeaveView(discord.ui.View):
    def __init__(self, author, game_session, message_id, game_type, game_obj):
        super().__init__(timeout=30.0)
        self.author = author
        self.game_session = game_session
        self.message_id = message_id
        self.game_type = game_type
        self.game_obj = game_obj
        self.message = None # view.message 用

    @discord.ui.button(label="はい、離脱します", style=discord.ButtonStyle.danger)
    async def confirm(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.defer()
        
        # 循環参照を防ぐため、ここでインポート
        from core.state import state
        # channel_id からチャンネルを取得
        channel = i.client.get_channel(self.game_obj.channel_id)
        if not channel: return

        try:
            board_message = await channel.fetch_message(self.message_id)
            
            if self.game_type == "othello":
                # オセロの終了処理
                self.game_obj.game_over = True
                setattr(self.game_obj, 'ended_by_action', 'leave')
                
                # 相手プレイヤーを勝者にする
                opponent_id = next((pid for pid in self.game_obj.players.values() if pid != self.author.id), None)
                if opponent_id:
                    self.game_obj.winner = next((color for color, pid in self.game_obj.players.items() if pid == opponent_id), EMPTY)
                
                # 結果表示 (cogs/games.py の関数を呼び出す必要があるが、Viewからは呼べないので
                # ここで直接 Embed を更新するか、簡易的なメッセージを送る)
                # ★本来は Cog の関数を呼びたいが、ここでは処理完結させる
                from cogs.games import send_othello_result_message_helper
                await send_othello_result_message_helper(channel, self.game_session, board_message, "leave")
                
                if self.message_id in state.active_games:
                    del state.active_games[self.message_id]

            elif self.game_type == "connectfour":
                # コネクトフォーの終了処理
                self.game_obj.game_over = True
                opponent_id = next((pid for pid in self.game_obj.players.values() if pid != self.author.id), None)
                if opponent_id:
                    self.game_obj.winner = next((token for token, pid in self.game_obj.players.items() if pid == opponent_id), None)
                
                from cogs.games import send_connectfour_result_message_helper
                await send_connectfour_result_message_helper(channel, self.game_obj, board_message, "leave")

                if self.message_id in state.active_connectfour_games:
                    del state.active_connectfour_games[self.message_id]

            await i.message.delete()
            
        except discord.NotFound:
            await i.followup.send(embed=create_embed("エラー", "元のゲームメッセージが見つかりませんでした。", discord.Color.red(), "danger"), ephemeral=True)
        
        self.stop()

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.secondary)
    async def cancel(self, i: discord.Interaction, b: discord.ui.Button):
        await i.message.delete()
        await i.response.send_message(embed=create_embed("キャンセル", "離脱をキャンセルしました。", discord.Color.blue(), "info"), ephemeral=True, delete_after=5)
        self.stop()
    
    async def on_timeout(self):
        if self.message:
            try: await self.message.delete()
            except: pass