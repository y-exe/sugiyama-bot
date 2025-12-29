# cogs/system.py
import discord
from discord.ext import commands, tasks
import datetime
from core.config import JST
from core.state import state
from services.ai.deepseek import generate_deepseek_text_response
from data.points_manager import points_manager
from data.settings_manager import settings_manager
from ui.embeds import create_embed

class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 富豪税タスクの開始
        if not self.wealth_tax.is_running():
            self.wealth_tax.start()

    def cog_unload(self):
        self.wealth_tax.cancel()

    @tasks.loop(hours=24)
    async def wealth_tax(self):
        """毎日朝5時に実行される富豪税ロジック"""
        now = datetime.datetime.now(JST)
        if now.hour != 5:
            return

        print("[System] 富豪税を徴収します...")
        for user_id_str, points in points_manager.game_points.items():
            try:
                uid = int(user_id_str)
                if uid == self.bot.user.id:
                    continue
                
                tax = 0
                if points >= 3000: tax = -50
                elif points >= 500: tax = -10
                elif points >= 100: tax = -5
                
                if tax != 0:
                    points_manager.update_points(uid, tax)
            except ValueError:
                continue
        print("[System] 徴収が完了しました。")

    @wealth_tax.before_loop
    async def before_wealth_tax(self):
        await self.bot.wait_until_ready()

    @commands.command(name="setchannel")
    @commands.has_permissions(administrator=True)
    async def setchannel(self, ctx):
        """コマンドの使用を許可/禁止するチャンネルを切り替える"""
        cid = ctx.channel.id
        if cid in state.allowed_channels:
            state.allowed_channels.remove(cid)
            settings_manager.save_settings() # JSONに即時保存
            embed = create_embed("設定変更", f"このチャンネル <#{cid}> でのコマンド利用を**禁止**しました。", discord.Color.red(), "danger")
        else:
            state.allowed_channels.add(cid)
            settings_manager.save_settings() # JSONに即時保存
            embed = create_embed("設定変更", f"このチャンネル <#{cid}> でのコマンド利用を**許可**しました。", discord.Color.green(), "success")
        
        await ctx.send(embed=embed)

    @discord.app_commands.command(name="imakita", description="過去30分のチャットを要約します。")
    async def imakita_slash(self, interaction: discord.Interaction):
        """スラッシュコマンド版 今北産業"""
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        after_time = discord.utils.utcnow() - datetime.timedelta(minutes=30)
        history = []
        async for m in interaction.channel.history(limit=200, after=after_time):
            if not m.author.bot and m.clean_content:
                history.append(f"{m.author.name}: {m.clean_content}")
        
        if not history:
            return await interaction.followup.send("過去30分間に要約できるメッセージがありませんでした。", ephemeral=True)
            
        prompt = (
            "以下のDiscordのチャット履歴を、重要な点を3つの短い箇条書きで要約してください。\n"
            "「以下に要約します」等の前置きは不要です。日本語で答えてください。\n\n"
            + "\n".join(history)
        )
        
        summary = await generate_deepseek_text_response(prompt)
        embed = create_embed("今北産業 (過去30分)", summary, discord.Color.green(), "success", "DeepSeek")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """スラッシュコマンドを手動同期する(オーナー限定)"""
        synced = await self.bot.tree.sync()
        await ctx.send(f"{len(synced)} 個のコマンドを同期しました。")

async def setup(bot):
    await bot.add_cog(System(bot))