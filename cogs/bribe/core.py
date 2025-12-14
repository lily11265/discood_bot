import discord
from discord import app_commands
from discord.ext import commands
import random
import logging
from utils.settings import load_settings
from utils.sheets import get_user_inventory, update_user_inventory
from utils.gacha_data import load_gacha_data

logger = logging.getLogger(__name__)
FAIL_MENTION_ID = "1007172975222603798"

class BribeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="뇌물", description="뇌물로 가챠를 쉽게 해봅시다.")
    @app_commands.describe(코인="바칠 코인의 양")
    async def bribe_command(self, interaction: discord.Interaction, 코인: int):
        user_id = str(interaction.user.id)
        settings = load_settings()
        
        # 1. 입력값 검증
        if 코인 <= 0:
            await interaction.response.send_message("코인은 1 이상의 양수여야 합니다.", ephemeral=True)
            return

        await interaction.response.defer()

        # 2. 보유 코인 및 최대 한도 확인
        user_inv = await get_user_inventory(user_id)
        if not user_inv:
            await interaction.followup.send("유저 정보를 찾을 수 없습니다.", ephemeral=True)
            return

        if user_inv["coins"] < 코인:
            await interaction.followup.send(f"코인이 부족합니다. (보유: {user_inv['coins']}원)", ephemeral=True)
            return

        max_coin = settings.get("bribe_max_coin", 100)
        if 코인 > max_coin:
            await interaction.followup.send(f"뇌물은 최대 {max_coin}코인까지만 가능합니다.", ephemeral=True)
            return

        # 3. 확률 계산
        # 성공 확률 = (입력 코인 / 최대 코인) * 100
        # 실패 확률(절대 실패) = settings.get("bribe_fail_rate", 1.5)
        
        fail_rate = settings.get("bribe_fail_rate", 1.5)
        success_chance = (코인 / max_coin) * 100
        
        critical_roll = random.uniform(0, 100)
        is_critical_fail = False

        if critical_roll < fail_rate:
            is_critical_fail = True
            final_result = False
        else:
            # Normal success check based on amount
            success_roll = random.uniform(0, 100)
            final_result = success_roll < success_chance

        # 4. 코인 차감
        new_coins = user_inv["coins"] - 코인
        
        if not final_result:
            # 실패 처리
            await update_user_inventory(user_id, coins=new_coins)
            
            if is_critical_fail:
                msg = f"직원이 돈을 받고 미쳐서 들고 튀었습니다... ... 첨벙!"
            else:
                msg = f"직원 : 이 ㅆ발럼이?! <@{FAIL_MENTION_ID}>!!!!!!!!!!!!!!!!!!!!!!!\n- 당신은 뇌물 거래에 실패했습니다!"
                
            await interaction.followup.send(msg)
            return

        # 5. 성공 처리 (가챠 아이템 3개 지급)
        gacha_items = load_gacha_data()
        if not gacha_items:
            await update_user_inventory(user_id, coins=new_coins)
            await interaction.followup.send("가챠 데이터가 없어 보상을 줄 수 없습니다. (코인은 차감됨)", ephemeral=True)
            return

        rewards = random.choices(gacha_items, k=3)
        reward_names = [item["name"] for item in rewards]
        
        # 인벤토리 업데이트 (코인 차감 + 아이템 3개 추가)
        final_items = user_inv["items"] + reward_names
        await update_user_inventory(user_id, coins=new_coins, items=final_items)
        
        # 임베드 출력
        embed = discord.Embed(title="🎉 뇌물 성공!", color=discord.Color.gold())
        embed.description = f"{코인}코인을 바쳐 아이템 3개를 획득했습니다!"
        
        for item in rewards:
            embed.add_field(name=item["name"], value=item["description"], inline=False)
            
        await interaction.followup.send(embed=embed)

    @bribe_command.autocomplete("코인")
    async def bribe_autocomplete(self, interaction: discord.Interaction, current: int) -> list[app_commands.Choice[int]]:
        user_id = str(interaction.user.id)
        settings = load_settings()
        max_coin = settings.get("bribe_max_coin", 100)
        
        choices = []
        
        # 1. Max Coin Choice
        choices.append(app_commands.Choice(name=f"넣을 수 있는 최대 코인은 {max_coin}코인입니다.", value=max_coin))
        
        # 2. Current Balance Choice
        try:
            user_inv = await get_user_inventory(user_id)
            balance = user_inv["coins"] if user_inv else 0
            choices.append(app_commands.Choice(name=f"현재 잔고는 {balance}원 입니다.", value=balance))
        except:
            choices.append(app_commands.Choice(name="보유 코인 확인 불가", value=0))
            
        return choices

async def setup(bot):
    await bot.add_cog(BribeCog(bot))
