# ui/views_highlow.py
import discord
import random
from core.state import state
from data.points_manager import points_manager
from ui.embeds import create_embed
from engines.high_low import HighLowLogic

class HighLowRecruitmentView(discord.ui.View):
    """ハイロー対戦の募集画面"""
    def __init__(self, host, opponent, bet_amount):
        super().__init__(timeout=120.0)
        self.host = host
        self.opponent = opponent
        self.bet_amount = bet_amount
        self.message = None

    @discord.ui.button(label="承認する", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, i: discord.Interaction, b: discord.ui.Button):
        # 参加資格チェック
        if i.user.id != self.opponent.id:
            return await i.response.send_message("対戦相手に指名された人のみ承認できます。", ephemeral=True)
        
        # ポイントチェック
        if points_manager.get_points(self.opponent.id) < self.bet_amount:
            return await i.response.send_message(f"ポイントが不足しています。このゲームには`{self.bet_amount}pt`必要です。", ephemeral=True)
        
        await i.response.defer()
        
        # ポイント先払い（賭け金没収）
        points_manager.update_points(self.host.id, -self.bet_amount)
        points_manager.update_points(self.opponent.id, -self.bet_amount)
        
        # ゲーム開始処理
        game = HighLowLogic(self.host.id, self.opponent.id, self.bet_amount, i.message.id)
        state.active_highlow_games[i.message.id] = game
        
        view = HighLowChoiceView(i.message.id)
        desc = (f"ベット額: `{self.bet_amount}pt`\n"
                f"現在のカード: **{game.get_card_display()}**\n\n"
                f"<@{self.host.id}> と <@{self.opponent.id}> は、\n"
                f"次のカードが **High** か **Low** か選んでください。\n"
                f"（ボタンはあなたにしか見えません）")
        
        embed = create_embed(f"ハイアンドロー対戦！", desc, discord.Color.blue(), "pending")
        await i.message.edit(content=None, embed=embed, view=view)
        self.stop()

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user.id != self.host.id:
            return await i.response.send_message("募集者のみがキャンセルできます。", ephemeral=True)
        
        embed = create_embed("キャンセル", f"{self.host.mention}が募集を取り消しました。", discord.Color.red(), "danger")
        await i.response.edit_message(embed=embed, view=None)
        self.stop()
    
    async def on_timeout(self):
        if self.message:
            # ゲームが始まっていなければ削除または無効化
            if self.message.id not in state.active_highlow_games:
                try: await self.message.edit(embed=create_embed("タイムアウト", "募集は時間切れになりました。", discord.Color.orange(), "warning"), view=None)
                except: pass

class HighLowChoiceView(discord.ui.View):
    """ハイロー対戦中の選択画面"""
    def __init__(self, message_id: int):
        super().__init__(timeout=60.0)
        self.message_id = message_id

    async def handle_choice(self, i: discord.Interaction, choice: str):
        game = state.active_highlow_games.get(self.message_id)
        if not game:
            return await i.response.send_message("このゲームは終了しています。", ephemeral=True)
            
        if i.user.id not in game.players:
            return await i.response.send_message("このゲームのプレイヤーではありません。", ephemeral=True)
        
        if game.choices[i.user.id] is not None:
            return await i.response.send_message(f"既に **{game.choices[i.user.id].upper()}** を選択済みです。", ephemeral=True)

        game.choices[i.user.id] = choice
        await i.response.send_message(f"**{choice.upper()}** を選択しました！相手の選択を待ちます。", ephemeral=True)

        # 全員選び終わったら結果判定
        if all(c is not None for c in game.choices.values()):
            await self.resolve_game(i, game)

    async def resolve_game(self, i, game):
        # 次のカードを決定
        new_card = random.randint(1, 13)
        while new_card == game.current_card: # 同じ数字は引き直し（シンプルなHighLowにするため）
            new_card = random.randint(1, 13)
        
        result = "high" if new_card > game.current_card else "low"
        
        # 勝者判定
        winners = [pid for pid, choice in game.choices.items() if choice == result]
        
        desc = (f"前のカード: **{game.get_card_display(game.current_card)}**\n"
                f"次のカード: **{game.get_card_display(new_card)}**\n\n"
                f"正解は... **{result.upper()}** でした！\n\n")
        
        if len(winners) == 1:
            winner_id = winners[0]
            # 勝ちは総取り (bet * 2)
            points_manager.update_points(winner_id, game.bet * 2)
            desc += f"🏆 <@{winner_id}> の勝利！ `{game.bet * 2}pt` 獲得！"
        elif len(winners) == 2:
            # 引き分けは返金
            for pid in winners: points_manager.update_points(pid, game.bet)
            desc += "🤝 二人とも正解！ ベット分が払い戻されました。"
        else:
            desc += "💸 二人ともハズレ... ポイントは没収されました。"

        embed = create_embed("ハイアンドロー 結果", desc, discord.Color.purple(), "success")
        
        # メッセージ更新（元のメッセージに対して）
        try:
            # インタラクション元のメッセージを更新
            await i.message.edit(embed=embed, view=None)
        except:
            # 失敗した場合は新規投稿
            await i.channel.send(embed=embed)
            
        del state.active_highlow_games[self.message_id]

    @discord.ui.button(label="HIGH", style=discord.ButtonStyle.primary, emoji="⬆️")
    async def high(self, i, b): await self.handle_choice(i, "high")

    @discord.ui.button(label="LOW", style=discord.ButtonStyle.secondary, emoji="⬇️")
    async def low(self, i, b): await self.handle_choice(i, "low")