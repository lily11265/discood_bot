import discord
from discord import app_commands
from discord.ext import commands
import logging
from utils.settings import load_settings
from utils.config import ADMIN_IDS
from cogs.admin.views import ControlPanelView

logger = logging.getLogger(__name__)

class ControlPanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) in ADMIN_IDS

    @app_commands.command(name="제어판", description="[Admin] 봇 설정을 변경합니다.")
    async def control_panel(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("이 명령어를 사용할 권한이 없습니다.", ephemeral=True)
            return

        embed = self.create_status_embed()
        view = ControlPanelView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def create_status_embed(self):
        settings = load_settings()
        embed = discord.Embed(title="🎛️ 봇 제어판", color=discord.Color.dark_grey())
        
        f_cooldown = settings.get("fishing_cooldown_hours", 1)
        price_mode = "변동 가격 (길이 비례)" if settings.get("price_multiplier_mode", False) else "고정 가격"
        g_cooldown = settings.get("gacha_cooldown_hours", 1)
        g_cost = settings.get("gacha_cost", 100)
        b_max = settings.get("bribe_max_coin", 100)
        b_fail = settings.get("bribe_fail_rate", 1.5)
        shop_stat = "📖 개장" if settings.get("shop_open", True) else "📕 폐장"
        l_cooldown = settings.get("library_cooldown_hours", 1)
        lib_stat = "📖 개장" if settings.get("library_open", True) else "📕 폐장"
        
        embed.add_field(name="🎣 낚시 쿨타임", value=f"{f_cooldown}시간", inline=True)
        embed.add_field(name="💰 가격 계산 모드", value=price_mode, inline=True)
        embed.add_field(name="🎰 가챠 쿨타임", value=f"{g_cooldown}시간", inline=True)
        embed.add_field(name="💎 가챠 비용", value=f"{g_cost}코인", inline=True)
        embed.add_field(name="💸 뇌물 최대 코인", value=f"{b_max}코인", inline=True)
        embed.add_field(name="⚠️ 뇌물 실패 확률", value=f"{b_fail}%", inline=True)
        embed.add_field(name="🏪 상점 상태", value=shop_stat, inline=True)
        embed.add_field(name="📚 도서관 쿨타임", value=f"{l_cooldown}시간", inline=True)
        embed.add_field(name="🏫 도서관 상태", value=lib_stat, inline=True)
        
        embed.set_footer(text="아래 메뉴를 통해 설정을 변경하세요.")
        return embed

async def setup(bot):
    await bot.add_cog(ControlPanelCog(bot))
