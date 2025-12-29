# ui/views_games.py
import discord
from core.constants import HAND_EMOJIS
from core.state import state
from ui.embeds import create_embed

class JankenChoiceView(discord.ui.View):
    def __init__(self, host_id: int):
        super().__init__(timeout=60.0)
        self.host_id = host_id

    async def handle_choice(self, i: discord.Interaction, hand: str):
        game_data = state.active_janken_games.get(i.message.id)
        if not game_data: return
        
        game_data["host_hand"] = hand
        game_data["game_status"] = "opponent_recruiting"
        
        embed = create_embed("じゃんけん 対戦相手募集", f"{i.user.mention} が手を選びました！\n参加者はリアクションを押してください。", discord.Color.green(), "info")
        await i.response.edit_message(embed=embed, view=None)
        
        # リアクション付与
        for emoji in HAND_EMOJIS.values():
            await i.message.add_reaction(emoji)

    @discord.ui.button(label="グー", emoji="✊")
    async def rock(self, i, b): await self.handle_choice(i, "rock")
    @discord.ui.button(label="チョキ", emoji="✌️")
    async def scissors(self, i, b): await self.handle_choice(i, "scissors")
    @discord.ui.button(label="パー", emoji="✋")
    async def paper(self, i, b): await self.handle_choice(i, "paper")