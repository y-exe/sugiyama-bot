# ui/views_economy.py
import discord
from ui.embeds import create_embed

class RankingDetailView(discord.ui.View):
    def __init__(self, author_id, rich_ranking_text, poor_ranking_text):
        super().__init__(timeout=180.0)
        self.author_id = author_id
        self.rich_ranking_text = rich_ranking_text
        self.poor_ranking_text = poor_ranking_text
        self.message = None

    @discord.ui.button(label="さらに表示", style=discord.ButtonStyle.primary)
    async def show_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed("ゲームポイント 詳細ランキング", color=discord.Color.gold(), status="info")
        embed.add_field(name="🏆 富豪ランキング Top 10", value=self.rich_ranking_text or "該当者なし", inline=False)
        embed.add_field(name="💸 貧乏ランキング Top 10", value=self.poor_ranking_text or "該当者なし", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_timeout(self):
        if self.message:
            for item in self.children: item.disabled = True
            try: await self.message.edit(view=self)
            except: pass

class GambleConfirmView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.confirmed = False
        self.message = None

    @discord.ui.button(label="実行", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("コマンドを実行した本人のみが操作できます。", ephemeral=True)
        
        self.confirmed = True
        for item in self.children: item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("コマンドを実行した本人のみが操作できます。", ephemeral=True)
        
        self.confirmed = False
        embed = create_embed("キャンセル", "ギャンブルをキャンセルしました。", discord.Color.red(), "danger")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    async def on_timeout(self):
        if self.message and not self.confirmed:
             embed = create_embed("タイムアウト", "操作がなかったため、ギャンブルはキャンセルされました。", discord.Color.orange(), "warning")
             try: await self.message.edit(embed=embed, view=None)
             except: pass

class GambleResultView(discord.ui.View):
    def __init__(self, details_embed: discord.Embed):
        super().__init__(timeout=180.0)
        self.details_embed = details_embed
        self.message = None

    @discord.ui.button(label="仕組み", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def details_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=self.details_embed, ephemeral=True)

    async def on_timeout(self):
        if self.message:
            for item in self.children: item.disabled = True
            try: await self.message.edit(view=self)
            except: pass

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

    @discord.ui.button(label="今後のログボ", style=discord.ButtonStyle.secondary, emoji="ℹ️") # 絵文字は近似
    async def show_future_bonus(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user.id != self.user_id:
            await i.response.send_message(embed=create_embed("エラー", "コマンドを実行した本人のみ操作できます。", discord.Color.orange(), "warning"), ephemeral=True); return
        
        # 循環参照回避のためここでインポート
        from data.points_manager import points_manager
        from data.login_manager import login_manager
        
        await i.response.defer(ephemeral=True)
        
        current_rank = points_manager.get_rank(self.user_id, i.client.user.id)
        user_data = points_manager.login_bonus_data.get(str(self.user_id), {})
        
        # ロジックの完全再現
        from core.config import JST
        import datetime
        today_str = datetime.datetime.now(JST).strftime("%Y-%m-%d")
        last_login_str = user_data.get("last_login", "")
        consecutive_days = user_data.get("consecutive_days", 0)
        
        start_day = consecutive_days + 1 if last_login_str == today_str else consecutive_days
        
        embed = create_embed(f"今後のログインボーナス予測", f"現在の順位: `{current_rank if current_rank > 0 else '圏外'}`", discord.Color.teal(), "info")
        future_text = []
        
        for day_offset in range(1, 8):
            future_consecutive = (start_day + day_offset -1) % 10 or 10
            
            # ポイント計算 (login_managerのロジックと同じものを使用)
            base_points = 30
            rank_bonus = 0
            if current_rank == 1: rank_bonus = 30
            elif 2 <= current_rank <= 3: rank_bonus = 20
            elif 4 <= current_rank <= 10: rank_bonus = 10
            consecutive_bonus = (future_consecutive - 1) * 10
            points = max(30, base_points + rank_bonus + consecutive_bonus)
            
            day_text = "明日" if day_offset == 1 else f"{day_offset}日後"
            future_text.append(f"▫️ **{day_text} ({future_consecutive}日目)**: `+{points}pt`")
            
        embed.add_field(name="今後7日間の報酬", value="\n".join(future_text), inline=False)
        embed.set_footer(text="※順位は毎日変動するため、実際の報酬とは異なる場合があります。")
        await i.followup.send(embed=embed, ephemeral=True)

class ConfirmGiveView(discord.ui.View):
    def __init__(self, author, target, amount, fee):
        super().__init__(timeout=60.0)
        self.author = author
        self.target = target
        self.amount = amount
        self.fee = fee
        self.is_done = False
        self.message = None

    @discord.ui.button(label="はい、送金します", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("コマンドを実行した本人のみが操作できます。", ephemeral=True)
        
        from data.points_manager import points_manager
        total_cost = self.amount + self.fee
        if points_manager.get_points(self.author.id) < total_cost:
            embed = create_embed("送金失敗", "ポイントが不足しています。", discord.Color.red(), "danger")
            await interaction.response.edit_message(embed=embed, view=None)
            self.is_done = True; self.stop()
            return

        points_manager.update_points(self.author.id, -total_cost)
        points_manager.update_points(self.target.id, self.amount)
        
        desc = (f"<@{self.author.id}> から <@{self.target.id}> に **`{self.amount}pt`** が送金されました。\n"
                f"手数料として `{self.fee}pt` が引かれました。")
        embed = create_embed("送金完了", desc, discord.Color.green(), "success")
        await interaction.response.edit_message(embed=embed, view=None)
        self.is_done = True; self.stop()

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("コマンドを実行した本人のみが操作できます。", ephemeral=True)
        
        embed = create_embed("キャンセル", "送金をキャンセルしました。", discord.Color.red(), "danger")
        await interaction.response.edit_message(embed=embed, view=None)
        self.is_done = True; self.stop()
    
    async def on_timeout(self):
        if self.message and not self.is_done:
            embed = create_embed("タイムアウト", "送金がタイムアウトしました。", discord.Color.orange(), "warning")
            try: await self.message.edit(embed=embed, view=None)
            except: pass