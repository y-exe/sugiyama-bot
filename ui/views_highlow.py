# ui/views_highlow.py
import discord
import random
from core.state import state
from data.points_manager import points_manager
from ui.embeds import create_embed

class HighLowChoiceView(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=60.0)
        self.message_id = message_id

    async def handle_choice(self, i: discord.Interaction, choice: str):
        game = state.active_highlow_games.get(self.message_id)
        if not game or i.user.id not in game.players:
            return await i.response.send_message("このゲームのプレイヤーではありません。", ephemeral=True)
        
        if game.choices[i.user.id] is not None:
            return await i.response.send_message("既に選択済みです。", ephemeral=True)

        game.choices[i.user.id] = choice
        await i.response.send_message(f"{choice.upper()} を選択しました。", ephemeral=True)

        if all(c is not None for c in game.choices.values()):
            await self.resolve_game(i, game)

    async def resolve_game(self, i, game):
        new_card = random.randint(1, 13)
        while new_card == game.current_card:
            new_card = random.randint(1, 13)
        
        result = "high" if new_card > game.current_card else "low"
        
        desc = f"前のカード: **{game.get_card_display()}**\n"
        desc += f"新しいカード: **{game.get_card_display(new_card)}**\n\n"
        
        winners = [pid for pid, choice in game.choices.items() if choice == result]
        
        if len(winners) == 1:
            winner_id = winners[0]
            points_manager.update_points(winner_id, game.bet * 2)
            desc += f"🏆 <@{winner_id}> の勝利！ `{game.bet * 2}pt` 獲得！"
        elif len(winners) == 2:
            for pid in winners: points_manager.update_points(pid, game.bet)
            desc += "🤝 二人とも正解！ ベット分が払い戻されました。"
        else:
            desc += "💸 二人ともハズレ... ポイントは没収されました。"

        embed = create_embed("ハイアンドロー 結果", desc, discord.Color.purple(), "success")
        await i.message.edit(embed=embed, view=None)
        del state.active_highlow_games[self.message_id]

    @discord.ui.button(label="HIGH", style=discord.ButtonStyle.primary)
    async def high(self, i, b): await self.handle_choice(i, "high")

    @discord.ui.button(label="LOW", style=discord.ButtonStyle.secondary)
    async def low(self, i, b): await self.handle_choice(i, "low")