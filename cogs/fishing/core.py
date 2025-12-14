import discord
from discord import app_commands
from discord.ext import commands
import random
import logging
from datetime import datetime, timedelta
from utils.fishing_data import load_fishing_data
from utils.settings import load_settings
from cogs.fishing.view import FishingView

logger = logging.getLogger(__name__)

class FishingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {} # user_id: datetime

    def get_price(self, base_price, length, mode):
        """가격 계산 로직"""
        if not mode: # 고정 가격
            return base_price
        
        # 변동 가격: 기존 가격 + (길이 / 20 * 기존 가격) -> 반올림
        # 예: 100원, 10m -> 100 + (10/20 * 100) = 150원
        added_value = (length / 20) * base_price
        return int(base_price + added_value + 0.5) # 반올림 로직

    @app_commands.command(name="낚시", description="낚시를 하여 아이템을 획득합니다.")
    async def fishing_command(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        settings = load_settings()
        
        # 쿨타임 체크
        cooldown_hours = settings.get("fishing_cooldown_hours", 1)
        if user_id in self.cooldowns:
            last_used = self.cooldowns[user_id]
            diff = datetime.now() - last_used
            if diff < timedelta(hours=cooldown_hours):
                remaining = timedelta(hours=cooldown_hours) - diff
                minutes = int(remaining.total_seconds() // 60)
                await interaction.response.send_message(f"낚시는 {cooldown_hours}시간마다 가능합니다. {minutes}분 남았습니다.", ephemeral=True)
                return

        items = load_fishing_data()
        if not items:
            await interaction.response.send_message("낚시 데이터가 없습니다. 관리자에게 문의하세요.", ephemeral=True)
            return

        # 아이템 추첨 및 변수 생성
        selected_item = random.choice(items)
        length = random.randint(1, 20)
        
        price_mode = settings.get("price_multiplier_mode", False)
        final_price = self.get_price(selected_item['price'], length, price_mode)
        
        # 임베드 생성
        # 제목: {아이템 이름, 가격: 아이템 가격원}
        title = f"{selected_item['name']}, 가격: {final_price}원"
        
        embed = discord.Embed(title=title, color=discord.Color.blue())
        
        # 항목: 설명 / 값: {아이템 설명 (줄바꿈) 길이는 아이템 길이m 입니다}
        field_value = f"{selected_item['description']}\n길이는 {length}m 입니다"
        embed.add_field(name="설명", value=field_value, inline=False)
        
        # 쿨타임 등록
        self.cooldowns[user_id] = datetime.now()
        
        view = FishingView(item=selected_item, price=final_price, user_id=user_id)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(FishingCog(bot))
