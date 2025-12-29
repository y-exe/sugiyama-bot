# cogs/economy.py
import discord
from discord.ext import commands
import random
import datetime
import math
from core.config import JST
from core.constants import BET_DICE_PAYOUTS, STATUS_EMOJIS
from data.points_manager import points_manager
from data.login_manager import login_manager
from ui.embeds import create_embed
from ui.views_economy import RankingDetailView, GambleConfirmView, LoginBonusView, GambleResultView, ConfirmGiveView

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="point", aliases=["othello point", "ポイント"])
    async def point(self, ctx):
        author_id_str = str(ctx.author.id)
        human_players_points = {pid: p for pid, p in points_manager.game_points.items() if int(pid) != self.bot.user.id}
        
        if not human_players_points:
            return await ctx.reply(embed=create_embed("ランキング", "まだポイントを持っているプレイヤーがいません。", status="info"), mention_author=False)
            
        rich_sorted = sorted(human_players_points.items(), key=lambda item: item[1], reverse=True)
        poor_sorted = sorted(human_players_points.items(), key=lambda item: item[1])

        embed = create_embed("ゲームポイントランキング", color=discord.Color.gold(), status="success")

        rich_top5_text = []
        for i, (pid, pval) in enumerate(rich_sorted[:5]):
            medal = "🥇 " if i == 0 else "🥈 " if i == 1 else "🥉 " if i == 2 else ""
            rich_top5_text.append(f"{medal}{i + 1}位 <@{pid}> - **{pval}pt**")
        embed.add_field(name="🏆 富豪ランキング Top 5", value="\n".join(rich_top5_text) or "該当者なし", inline=False)

        poor_top3_text = []
        poor_players = [p for p in poor_sorted if p[1] < 0]
        for i, (pid, pval) in enumerate(poor_players[:3]):
            poor_top3_text.append(f"{i + 1}位 <@{pid}> - **{pval}pt**")
        if poor_top3_text:
            embed.add_field(name="💸 貧乏ランキング Top 3", value="\n".join(poor_top3_text), inline=False)
            
        my_points = points_manager.get_points(ctx.author.id)
        footer_text = f"あなたのポイント: {my_points}pt | 富豪ランク: {points_manager.get_rank(ctx.author.id, self.bot.user.id)}位"
        embed.set_footer(text=footer_text, icon_url=ctx.author.display_avatar.url)
        
        rich_10 = "\n".join([f"{i+1}位 <@{p[0]}>: {p[1]}pt" for i, p in enumerate(rich_sorted[:10])])
        poor_10 = "\n".join([f"{i+1}位 <@{p[0]}>: {p[1]}pt" for i, p in enumerate(poor_sorted[:10]) if p[1] < 0])
        await ctx.reply(embed=embed, view=RankingDetailView(ctx.author.id, rich_10, poor_10), mention_author=False)

    @commands.command(name="gamble", aliases=["ギャンブル"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def gamble(self, ctx):
        player_id = ctx.author.id
        user_id_str = str(player_id)
        today_str = datetime.datetime.now(JST).strftime("%Y-%m-%d")
        current_points = points_manager.get_points(player_id)

        GAMBLE_LIMIT = 5
        user_data = points_manager.login_bonus_data.get(user_id_str, {})
        g_info = user_data.get("gamble_info", {"date": "2000-01-01", "count": 0})
        play_count = g_info["count"] if g_info["date"] == today_str else 0
        
        if current_points > 0 and play_count >= GAMBLE_LIMIT:
            msg = f"今日のギャンブルは上限の **{GAMBLE_LIMIT}回** に達しました。\n`bet` コマンドの使用を推奨します。"
            return await ctx.reply(embed=create_embed("回数上限", msg, discord.Color.red(), "danger"), mention_author=False)

        rem = max(0, GAMBLE_LIMIT - play_count) if current_points > 0 else "無制限"
        confirm_desc = f"ベット額は手持ちからランダム（1/3以上）で決まります。\n一日 **{GAMBLE_LIMIT}回** まで。本日残り: **{rem}**"
        if current_points <= 0: confirm_desc += "\n\n**※救済措置発動中！回数制限なくギャンブルが可能です。**"

        view = GambleConfirmView(player_id)
        confirm_msg = await ctx.reply(embed=create_embed("ギャンブルを実行しますか？", confirm_desc, discord.Color.yellow(), "warning"), view=view, mention_author=False)
        
        await view.wait()
        if not view.confirmed: return

        if g_info["date"] != today_str: g_info = {"date": today_str, "count": 1}
        else: g_info["count"] += 1
        points_manager.login_bonus_data[user_id_str]["gamble_info"] = g_info
        points_manager.save_all()
        
        is_whale = current_points >= 20000
        if is_whale: bet = random.randint(current_points // 4, current_points // 2)
        elif current_points > 0: bet = random.randint(max(1, current_points // 3), current_points)
        else: bet = 100 if -100 <= current_points <= 0 else random.randint(abs(current_points)//6, abs(current_points)//2)

        def get_mult():
            r = random.random()
            if r < 0.02: return round(random.uniform(5.01, 10.0) * random.choice([-1, 1]), 2)
            if r < 0.15: return round(random.uniform(3.01, 5.0) * random.choice([-1, 1]), 2)
            return round(random.uniform(1.51, 3.0) * random.choice([-1, 1]), 2)
        
        mult = get_mult()
        if is_whale: mult = round(random.uniform(-1.8, -1.5), 2)
        elif -1.5 <= mult <= 1.5 and mult != 0: mult = get_mult()

        diff = int(bet * mult) - bet
        points_manager.update_points(player_id, diff)
        
        logs = [f"**1. ベット額**: `{bet}pt`", f"**2. 倍率**: `{mult:+.2f}倍`"]
        if is_whale: logs.append("▫️ **富豪調整が適用されました。**")
        logs.append(f"**3. 変動**: `{diff:+}pt`")

        res_txt, col = "勝ち！", discord.Color.green()
        if is_whale: res_txt, col = "💸 **大きな力が働いた...**", discord.Color.dark_purple()
        elif mult > 5.0: res_txt, col = "🎉🎉🎉 **超大当たり！！**", discord.Color.gold()
        elif mult < -5.0: res_txt, col = "💀💀💀 **世紀の大失敗！！**", discord.Color.from_rgb(100, 0, 0)
        elif diff < 0: res_txt, col = "負け...", discord.Color.red()

        embed = create_embed("ハイリスクギャンブル", f"{ctx.author.mention} Result: **{mult:+.2f}倍**\n\n**{res_txt}**", col, "info")
        embed.add_field(name="ポイント変動", value=f"`{diff:+}pt`", inline=True)
        embed.add_field(name="現在のポイント", value=f"`{points_manager.get_points(player_id)}pt`", inline=True)

        await confirm_msg.edit(embed=embed, view=GambleResultView(create_embed("仕組み", "\n".join(logs))))

    @commands.command(name="bet", aliases=["賭け", "かけ", "ベッド", "べっど"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bet(self, ctx, amount_str: str):
        try:
            amount = int(amount_str)
        except ValueError:
            return await ctx.send(embed=create_embed("エラー", "賭け金は整数で指定してください。", discord.Color.orange(), "warning"))

        current = points_manager.get_points(ctx.author.id)
        if amount <= 0:
            return await ctx.send(embed=create_embed("エラー", "1ポイント以上で指定してください。", discord.Color.orange(), "warning"))
        if current < amount:
            return await ctx.send(embed=create_embed("ポイント不足", f"所持ポイント: `{current}pt`", discord.Color.orange(), "warning"))
        
        async with ctx.typing():
            await asyncio.sleep(0.8)
            roll = random.randint(1, 6)
            msg, mult = BET_DICE_PAYOUTS[roll]
            diff = int(amount * mult)
            points_manager.update_points(ctx.author.id, diff)
            
            embed = create_embed(f"ダイスベット結果: {roll}", f"{ctx.author.mention} ベット: `{amount}pt`\n\n**結果**\n{msg}", discord.Color.purple(), "info")
            embed.add_field(name="ポイント変動", value=f"`{diff:+}pt`", inline=True)
            embed.add_field(name="現在のポイント", value=f"`{points_manager.get_points(ctx.author.id)}pt`", inline=True)
            await ctx.send(embed=embed)

    @bet.error
    async def bet_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed("引数不足", "賭け金を指定してください。\n例: `bet 10`", discord.Color.orange(), "warning"))

    @commands.command(name="login", aliases=["bonus", "daily", "ログイン", "ログボ"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def login_bonus_command(self, ctx):
        user_id_str = str(ctx.author.id)
        today = datetime.datetime.now(JST)
        user_data = points_manager.login_bonus_data.get(user_id_str, {})
        
        if user_data.get("last_login") == today.strftime("%Y-%m-%d"):
            view = LoginBonusView(ctx.author.id)
            return await ctx.send(embed=create_embed("ログイン済み", f"{STATUS_EMOJIS['warning']} 今日のボーナスは受取済みです。", discord.Color.orange(), "warning"), view=view)

        consecutive_days = user_data.get("consecutive_days", 0)
        last_date = datetime.datetime.strptime(user_data.get("last_login", "2000-01-01"), "%Y-%m-%d").date()
        if last_date == today.date() - datetime.timedelta(days=1):
            consecutive_days = (consecutive_days % 10) + 1
        else:
            consecutive_days = 1
        
        current_rank = points_manager.get_rank(ctx.author.id, self.bot.user.id)
        
        base_points = 30 
        rank_bonus = 30 if current_rank == 1 else 20 if 2 <= current_rank <= 3 else 10 if 4 <= current_rank <= 10 else 0
        con_bonus = (consecutive_days - 1) * 10  
        points_to_add = max(30, base_points + rank_bonus + con_bonus)

        points_manager.update_points(ctx.author.id, points_to_add)
        points_manager.login_bonus_data[user_id_str] = {"last_login": today.strftime("%Y-%m-%d"), "consecutive_days": consecutive_days}
        points_manager.save_all()

        desc = (f"{STATUS_EMOJIS['success']} **{consecutive_days}日目**のログインボーナスです！\n"
                f"{STATUS_EMOJIS['pending']} `+{points_to_add}pt` を獲得しました！")
        embed = create_embed("ログインボーナス", desc, discord.Color.gold(), "success")
        embed.add_field(name="現在のポイント", value=f"`{points_manager.get_points(ctx.author.id)}pt`", inline=True)
        embed.add_field(name="現在の順位", value=f"`{current_rank if current_rank > 0 else '圏外'}`", inline=True)
        
        view = LoginBonusView(ctx.author.id)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="give", aliases=["pay", "送金"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def give_command(self, ctx, target: discord.Member, amount_str: str):
        if ctx.author == target or target.bot:
            return await ctx.send(embed=create_embed("エラー", "自分自身またはBotには送金できません。", discord.Color.orange(), "warning"))

        try:
            amount = int(amount_str)
            if amount <= 0: raise ValueError
        except ValueError:
            return await ctx.send(embed=create_embed("エラー", "1以上の整数を指定してください。", discord.Color.orange(), "warning"))

        fee = math.ceil(amount * 0.15)
        total = amount + fee
        if points_manager.get_points(ctx.author.id) < total:
            return await ctx.send(embed=create_embed("ポイント不足", f"手数料込みで `{total}pt` 必要です。", discord.Color.orange(), "warning"))

        desc = (f"本当に <@{target.id}> に **`{amount}pt`** を送金しますか？\n\n"
                f"手数料: `{fee}pt` (15%)\n合計: `{total}pt` 消費します。")
        
        view = ConfirmGiveView(ctx.author, target, amount, fee)
        await ctx.send(embed=create_embed("送金確認", desc, discord.Color.yellow(), "warning"), view=view)

    @give_command.error
    async def give_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed("引数不足", "送金先と金額を指定してください。\n例: `give @ユーザー 100`", discord.Color.orange(), "warning"))

async def setup(bot):
    await bot.add_cog(Economy(bot))