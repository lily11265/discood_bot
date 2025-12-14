import discord
from discord import app_commands
from discord.ext import commands
import random
import logging
from datetime import datetime, timedelta
from utils.gacha_data import load_gacha_data
from utils.settings import load_settings
from utils.sheets import get_user_inventory, update_user_inventory

logger = logging.getLogger(__name__)

class GachaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {} # user_id: datetime

    @app_commands.command(name="가챠", description="랜덤 아이템을 뽑습니다.")
    async def gacha_command(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        settings = load_settings()
        
        # 1. 쿨타임 체크
        cooldown_hours = settings.get("gacha_cooldown_hours", 1)
        if user_id in self.cooldowns:
            last_used = self.cooldowns[user_id]
            diff = datetime.now() - last_used
            if diff < timedelta(hours=cooldown_hours):
                remaining = timedelta(hours=cooldown_hours) - diff
                minutes = int(remaining.total_seconds() // 60)
                await interaction.response.send_message(f"가챠는 {cooldown_hours}시간마다 가능합니다. {minutes}분 남았습니다.", ephemeral=True)
                return

        await interaction.response.defer()

        # 2. 코인 확인 및 차감
        cost = settings.get("gacha_cost", 100)
        user_inv = await get_user_inventory(user_id)
        
        if not user_inv:
            await interaction.followup.send("유저 정보를 찾을 수 없습니다.", ephemeral=True)
            return
            
        if user_inv["coins"] < cost:
            await interaction.followup.send(f"코인이 부족합니다. (필요: {cost}원, 보유: {user_inv['coins']}원)", ephemeral=True)
            return
            
        # 3. 데이터 로드 및 추첨
        items = load_gacha_data()
        if not items:
            await interaction.followup.send("가챠 데이터가 없습니다.", ephemeral=True)
            return
            
        picked_item = random.choice(items)
        name = picked_item["name"]
        desc = picked_item["description"]
        
        # 4. 결과 처리 (코인 차감 + 아이템 지급)
        new_coins = user_inv["coins"] - cost
        current_items = user_inv["items"]
        new_items_list = current_items + [name]
        
        try:
            # 배치 업데이트처럼 보이지만 각각 호출 (sheets.py 구조상)
            # 코인 차감과 아이템 지급을 동시에 update_user_inventory 하나로 처리 가능하면 좋겠지만,
            # 현재 함수는 coins=None, items=None 인자를 받으므로 한 번에 호출 가능.
            await update_user_inventory(user_id, coins=new_coins, items=new_items_list)
            
            # 쿨타임 등록
            self.cooldowns[user_id] = datetime.now()
            
            # 5. 메시지 전송 (일반 메시지)
            # "축하합니다! "아이템 이름"을 뽑았습니다!(줄바꿈)"아이템 이름" : "아이템 설명"
            msg = f"축하합니다! \"{name}\"을 뽑았습니다!\n\"{name}\" : \"{desc}\""
            await interaction.followup.send(msg)
            
        except Exception as e:
            logger.error(f"가챠 트랜잭션 실패: {e}")
            await interaction.followup.send("가챠 처리 중 오류가 발생했습니다.")

async def setup(bot):
    await bot.add_cog(GachaCog(bot))
