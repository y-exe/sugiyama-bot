# ui/embeds.py
import discord
import datetime
from core.config import JST
from core.constants import STATUS_EMOJIS, BOT_ICON_URL

def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue(), status: str = "info", api_source: str = None) -> discord.Embed:
    emoji = STATUS_EMOJIS.get(status, '')
    embed = discord.Embed(title=f"{emoji} {title}", description=description, color=color)
    
    footer_text = "杉山啓太Bot"
    if api_source:
        footer_text += f" / {api_source}"
        
    embed.set_footer(text=footer_text, icon_url=BOT_ICON_URL)
    embed.timestamp = datetime.datetime.now(JST)
    return embed