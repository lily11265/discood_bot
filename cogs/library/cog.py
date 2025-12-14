import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta
from utils.config import LIBRARY_GUILD_ID, LIBRARY_CHANNEL_ID
from utils.settings import load_settings
from cogs.library.logic import roll_dice, select_random_book
from utils.library_data import load_library_data

logger = logging.getLogger(__name__)

class LibraryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {} # user_id: datetime

    def check_channel(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id != LIBRARY_GUILD_ID:
            return False
        if interaction.channel_id != LIBRARY_CHANNEL_ID:
            return False
        return True

    @app_commands.command(name="도서찾기", description="도서실에서 책을 찾습니다.")
    async def find_book(self, interaction: discord.Interaction):
        # 1. 채널/서버 확인
        if not self.check_channel(interaction):
            await interaction.response.send_message("이 명령어는 지정된 도서실 채널에서만 사용할 수 있습니다.", ephemeral=True)
            return

        settings = load_settings()
        
        # 2. 개장 여부 확인
        if not settings.get("library_open", True):
            await interaction.response.send_message("도서관이 문닫았습니다.", ephemeral=True)
            return

        # 3. 쿨타임 확인
        user_id = interaction.user.id
        now = datetime.now()
        if user_id in self.cooldowns:
            last_used = self.cooldowns[user_id]
            cooldown_hours = settings.get("library_cooldown_hours", 1)
            diff = now - last_used
            if diff < timedelta(hours=cooldown_hours):
                remain = timedelta(hours=cooldown_hours) - diff
                # 분 단위 표시
                remain_min = int(remain.total_seconds() // 60)
                await interaction.response.send_message(f"아직 책을 찾을 수 없습니다. (남은 시간: {remain_min}분)", ephemeral=True)
                return

        # 4. 주사위 굴리기 (1d100)
        dice = roll_dice()
        
        if dice < 50:
            # 실패
            self.cooldowns[user_id] = now
            await interaction.response.send_message(f"🎲 주사위: {dice}\n책을 찾으려 했지만, 먼지만 날립니다... (실패)", ephemeral=True)
            return
            
        # 5. 성공: 책 선택
        book = select_random_book()
        if not book:
            await interaction.response.send_message(f"🎲 주사위: {dice}\n책을 찾았는데, 내용이 텅 비어있습니다. (데이터 없음)", ephemeral=True)
            return

        self.cooldowns[user_id] = now
        
        embed = discord.Embed(
            title=f"📖 발견! {book['title']}",
            description=book['content'],
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"🎲 주사위: {dice} (성공!)")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LibraryCog(bot))
