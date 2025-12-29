# core/logger.py
import discord
import traceback
import sys
from ui.embeds import create_embed

async def send_error_embed(ctx_or_interaction, error: Exception):
    """エラー内容を解析し、開発者への報告用Embedを送信する"""
    # チャンネルの特定
    channel = None
    if isinstance(ctx_or_interaction, discord.Interaction):
        channel = ctx_or_interaction.channel
    else:
        channel = ctx_or_interaction.channel

    if channel:
        error_traceback = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        description = f"開発者の(*'▽')またはオペレーターのはんちゃーいかにご報告ください。\n```{error_traceback[:1800]}```"
        embed = create_embed("エラーが発生しました", description, discord.Color.red(), status="danger")
        
        try:
            if isinstance(ctx_or_interaction, discord.Interaction) and ctx_or_interaction.response.is_done():
                await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
            elif isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await channel.send(embed=embed)
        except Exception as e:
            print(f"CRITICAL: Failed to send error embed. Reason: {e}")

    # コンソール出力
    print(f"--- ERROR in command/event ---")
    traceback.print_exc()