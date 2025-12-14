
import discord
from discord import app_commands
from discord.ext import commands
from utils.sheets import get_user_inventory
from .view import OddEvenGameView

class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="홀짝", description="홀짝 도박 게임을 시작합니다.")
    @app_commands.describe(배팅금액="배팅할 코인 금액")
    async def odd_even_game(self, interaction: discord.Interaction, 배팅금액: int):
        user_id = str(interaction.user.id)
        user_data = await get_user_inventory(user_id)
        
        if not user_data:
            await interaction.response.send_message("정보를 찾을 수 없습니다.", ephemeral=True)
            return

        current_coins = user_data["coins"]
        
        if 배팅금액 > current_coins:
            await interaction.response.send_message(f"보유 코인이 부족합니다. (보유: {current_coins})", ephemeral=True)
            return
        
        if 배팅금액 <= 0:
            await interaction.response.send_message("배팅 금액은 양수여야 합니다.", ephemeral=True)
            return

        view = OddEvenGameView(user_id, 배팅금액, interaction)
        
        embed = discord.Embed(
            title="주사위는 던져졌다...",
            description=f"주사위: {view.dice1}, {view.dice2}, ?\n배팅 금액: {배팅금액} (배수 : 2배)",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view)

    @odd_even_game.autocomplete("배팅금액")
    async def betting_autocomplete(self, interaction: discord.Interaction, current: int):
        user_id = str(interaction.user.id)
        try:
            user_data = await get_user_inventory(user_id)
            coins = user_data["coins"] if user_data else 0
            # Always return this choice regardless of input, as a suggestion
            return [app_commands.Choice(name=f"현재 보유 금액 {coins}원", value=coins)]
        except:
            return []
