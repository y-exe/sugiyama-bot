# cogs/economy.py
import discord
from discord.ext import commands
import random
import datetime
import math
import asyncio
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
            try: user = await self.bot.fetch_user(int(pid))
            except: user = None
            user_display = user.mention if user else f"ID:{pid}"
            rich_top5_text.append(f"{medal}{i + 1}位 {user_display} - **{pval}pt**")
        embed.add_field(name="🏆 富豪ランキング Top 5", value="\n".join(rich_top5_text) or "該当者なし", inline=False)
        poor_top3_text = []
        poor_players = [p for p in poor_sorted if p[1] < 0]
        for i, (pid, pval) in enumerate(poor_players[:3]):
            try: user = await self.bot.fetch_user(int(pid))
            except: user = None
            user_display = user.mention if user else f"ID:{pid}"
            poor_top3_text.append(f"{i + 1}位 {user_display} - **{pval}pt**")
        if poor_top3_text:
            embed.add_field(name="💸 貧乏ランキング Top 3", value="\n".join(poor_top3_text), inline=False)
        my_points = points_manager.get_points(ctx.author.id)
        footer_text = f"あなたのポイント: {my_points}pt"
        my_rich_rank = points_manager.get_rank(ctx.author.id, self.bot.user.id)
        if my_rich_rank != -1: footer_text += f" | 富豪ランク: {my_rich_rank}位"
        if my_points < 0:
            my_poor_rank = -1
            for i, (pid, pval) in enumerate(poor_players):
                if pid == author_id_str:
                    my_poor_rank = i + 1
                    break
            if my_poor_rank != -1: footer_text += f" | 貧乏ランク: {my_poor_rank}位"
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
        confirm_message = await ctx.reply(embed=create_embed("ギャンブルを実行しますか？", confirm_desc, discord.Color.yellow(), "warning"), view=view, mention_author=False)
        view.message = confirm_message
        await view.wait()
        if not view.confirmed: return
        if g_info["date"] != today_str: g_info = {"date": today_str, "count": 1}
        else: g_info["count"] += 1
        if user_id_str not in points_manager.login_bonus_data: points_manager.login_bonus_data[user_id_str] = {}
        points_manager.login_bonus_data[user_id_str]["gamble_info"] = g_info
        points_manager.save_all()
        is_whale = current_points >= 20000
        bet_amount = 0
        if is_whale: bet_amount = random.randint(current_points // 4, current_points // 2)
        elif current_points > 0: bet_amount = random.randint(max(1, current_points // 3), current_points)
        else: bet = 100 if -100 <= current_points <= 0 else random.randint(abs(current_points)//6, abs(current_points)//2)
        def get_multiplier():
            roll = random.random()
            if roll < 0.02: base = random.uniform(5.01, 10.0)
            elif roll < 0.15: base = random.uniform(3.01, 5.0)
            else: base = random.uniform(1.51, 3.0)
            return round(base * random.choice([-1, 1]), 2)
        multiplier = get_multiplier()
        if is_whale: multiplier = round(random.uniform(-1.8, -1.5), 2)
        elif -1.5 <= multiplier <= 1.5 and multiplier != 0: multiplier = get_multiplier()
        original_multiplier = multiplier
        profit_loss = int(bet_amount * multiplier)
        points_change = profit_loss - bet_amount
        points_manager.update_points(player_id, points_change)
        details_log = [f"**1. ベット額の決定**", f"▫️ ギャンブル前の所持ポイント: `{current_points}pt`"]
        if is_whale: details_log.append("▫️ **富豪調整が適用されました。**")
        details_log.append(f"▶️ **ベット額: `{bet_amount}pt`**")
        details_log.append("\n**2. 倍率の抽選**")
        if is_whale:
            details_log.append("▫️ 富豪調整により、特別な倍率が設定されました。")
            details_log.append(f"▶️ **抽選された倍率: `{original_multiplier:+.2f}` 倍**")
        else:
            details_log.append(f"▫️ 1回目の抽選結果: `{original_multiplier:+.2f}` 倍")
            if original_multiplier != multiplier:
                 details_log.append("▫️ ±1.5倍の範囲だったため再抽選！")
                 details_log.append(f"▶️ **最終的な倍率: `{multiplier:+.2f}` 倍**")
        if current_points <= 0 and (current_points + points_change) > 0:
            details_log.append("▫️ **奇跡の瞬間！借金からの帰還！**")
        details_log.extend(["\n**3. 最終的なポイント変動**", f"▫️ `({bet_amount}pt × {multiplier:+.2f}倍) - {bet_amount}pt`", f"▶️ **ポイント変動: `{points_change:+}pt`**"])
        result_text, color = "", discord.Color.default()
        if is_whale: result_text, color = "💸 **何か大きな力が働いたようだ...** 💸", discord.Color.dark_purple()
        elif multiplier > 5.0: result_text, color = "🎉🎉🎉 **超大当たり！！** 🎉🎉🎉", discord.Color.gold()
        elif multiplier > 3.0: result_text, color = "🎊 **大当たり！** 🎊", discord.Color.green()
        elif multiplier < -5.0: result_text, color = "💀💀💀 **世紀の大失敗！！** 💀💀💀", discord.Color.from_rgb(100, 0, 0)
        elif multiplier < -3.0: result_text, color = "💸 **大失敗...** 💸", discord.Color.red()
        else: result_text, color = ("ちょい勝ち！", discord.Color.light_grey()) if multiplier > 0 else ("ちょい負け...", discord.Color.dark_grey())
        desc = (f"{ctx.author.mention} が **`{bet_amount}pt`** をベット！\n\n結果は... **`{multiplier:+.2f}`** 倍！\n\n**{result_text}**")
        result_embed = create_embed("ハイリスクギャンブル", desc, color, "info")
        result_embed.add_field(name="ポイント変動", value=f"`{points_change:+}pt`", inline=True)
        result_embed.add_field(name="現在のポイント", value=f"`{points_manager.get_points(player_id)}pt`", inline=True)
        await confirm_message.edit(embed=result_embed, view=GambleResultView(create_embed("ギャンブルの仕組み", "\n".join(details_log), discord.Color.blurple(), "info")))

    @commands.command(name="bet", aliases=["賭け", "かけ", "ベッド", "べっど"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bet(self, ctx, amount_str: str):
        try: amount = int(amount_str)
        except ValueError: return await ctx.send(embed=create_embed("エラー", "賭け金は整数で指定してください。", discord.Color.orange(), "warning"))
        current_points = points_manager.get_points(ctx.author.id)
        if amount <= 0: return await ctx.send(embed=create_embed("エラー", "賭け金は1ポイント以上で指定してください。", discord.Color.orange(), "warning"))
        if current_points < amount: return await ctx.send(embed=create_embed("ポイント不足", f"ポイントが不足しています。\nあなたのポイント: `{current_points}pt`", discord.Color.orange(), "warning"))
        async with ctx.typing():
            await asyncio.sleep(0.8)
            dice_roll = random.randint(1, 6)
            message, payout_multiplier = BET_DICE_PAYOUTS[dice_roll]
            points_change = int(amount * payout_multiplier)
            points_manager.update_points(ctx.author.id, points_change)
            title = f"ダイスベット結果: {dice_roll}"
            description = f"{ctx.author.mention} が `{amount}pt` をベット！\n\n**結果**\n{message}"
            embed = create_embed(title, description, discord.Color.purple(), "info")
            embed.add_field(name="ポイント変動", value=f"`{'+' if points_change >=0 else ''}{points_change}pt`", inline=True)
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
        last_login_str = user_data.get("last_login", "2000-01-01")
        if last_login_str == today.strftime("%Y-%m-%d"):
            view = LoginBonusView(ctx.author.id)
            message = await ctx.send(embed=create_embed("ログイン済み", f"{STATUS_EMOJIS['warning']} 今日のログインボーナスは既に受け取っています。\n毎日0時にリセットされます。", discord.Color.orange(), "warning"), view=view)
            view.message = message
            return
        consecutive_days_val = user_data.get("consecutive_days", 0)
        last_login_date = datetime.datetime.strptime(last_login_str, "%Y-%m-%d").date()
        if last_login_date == today.date() - datetime.timedelta(days=1): consecutive_days = (consecutive_days_val % 10) + 1
        else: consecutive_days = 1
        current_rank = points_manager.get_rank(ctx.author.id, self.bot.user.id)
        base_points = 30
        rank_bonus = 0
        if current_rank == 1: rank_bonus = 30
        elif 2 <= current_rank <= 3: rank_bonus = 20
        elif 4 <= current_rank <= 10: rank_bonus = 10
        consecutive_bonus = (consecutive_days - 1) * 10
        points_to_add = max(30, base_points + rank_bonus + consecutive_bonus)
        points_manager.update_points(ctx.author.id, points_to_add)
        points_manager.login_bonus_data[user_id_str] = {"last_login": today.strftime("%Y-%m-%d"), "consecutive_days": consecutive_days}
        points_manager.save_all()
        desc = (f"{STATUS_EMOJIS['success']} **{consecutive_days}日目**のログインボーナスです！\n"
                f"{STATUS_EMOJIS['pending']} `+{points_to_add}pt` を獲得しました！\n\n"
                "**連続ログイン**や**ランキング順位**でポイントが増減します。")
        embed = create_embed("ログインボーナス", desc, discord.Color.gold(), "success")
        embed.add_field(name="現在のポイント", value=f"`{points_manager.get_points(ctx.author.id)}pt`", inline=True)
        embed.add_field(name="現在の順位", value=f"`{current_rank if current_rank > 0 else '圏外'}`", inline=True)
        view = LoginBonusView(ctx.author.id)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @commands.command(name="give", aliases=["pay", "送金"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def give_command(self, ctx, target: discord.Member, amount_str: str):
        if ctx.author == target or target.bot:
            return await ctx.send(embed=create_embed("エラー", "自分自身またはBotには送金できません。", discord.Color.orange(), "warning"))
        try:
            amount = int(amount_str)
            if amount <= 0: return await ctx.send(embed=create_embed("エラー", "1以上のポイントを送金してください。", discord.Color.orange(), "warning"))
        except ValueError:
            return await ctx.send(embed=create_embed("エラー", "金額は有効な整数で入力してください。", discord.Color.orange(), "warning"))
        fee = math.ceil(amount * 0.15)
        total_cost = amount + fee
        author_points = points_manager.get_points(ctx.author.id)
        if author_points < total_cost:
            return await ctx.send(embed=create_embed("ポイント不足", f"送金には手数料を含め `{total_cost}pt` 必要ですが、あなたは `{author_points}pt` しか持っていません。", discord.Color.orange(), "warning"))
        desc = (f"本当に <@{target.id}> に **`{amount}pt`** を送金しますか？\n\n"
                f"手数料として別途 **`{fee}pt`** (15%) がかかります。\n"
                f"合計で **`{total_cost}pt`** があなたの所持ポイントから引かれます。")
        view = ConfirmGiveView(ctx.author, target, amount, fee)
        confirmation_message = await ctx.send(embed=create_embed("送金確認", desc, discord.Color.yellow(), "warning"), view=view)
        view.message = confirmation_message
        await view.wait()
        if not view.is_done:
            embed = create_embed("タイムアウト", "送金がタイムアウトしました。", discord.Color.orange(), "warning")
            try: await confirmation_message.edit(embed=embed, view=None)
            except: pass

    @give_command.error
    async def give_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=create_embed("引数不足", "送金先と金額を指定してください。\n例: `give @ユーザー 100`", discord.Color.orange(), "warning"))

async def setup(bot):
    await bot.add_cog(Economy(bot))