
import discord
from discord import app_commands
from discord.ext import commands
import logging
from utils.sheets import get_user_inventory, update_user_inventory, get_all_users_inventory, get_admin_id, get_cached_metadata

logger = logging.getLogger(__name__)

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="아이템", description="러너의 아이템과 코인을 확인합니다.")
    async def item_command(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await get_user_inventory(user_id)
        
        if not data:
            await interaction.response.send_message("러너 정보를 찾을 수 없습니다.", ephemeral=True)
            return

        coins = data.get("coins", 0)
        items = ", ".join(data.get("items", [])) if data.get("items") else "없음"
        
        await interaction.response.send_message(
            f"**{interaction.user.display_name}**님의 보유 상태:\n**코인**: {coins}\n**아이템**: {items}",
            ephemeral=True
        )

    @app_commands.command(name="거래", description="코인이나 아이템을 다른 유저와 거래합니다.")
    @app_commands.describe(유형="거래 유형(돈, 아이템)", 이름="거래할 이름 또는 금액", 대상="거래할 대상 멤버")
    @app_commands.choices(유형=[
        app_commands.Choice(name="돈", value="돈"),
        app_commands.Choice(name="아이템", value="아이템")
    ])
    async def trade_command(self, interaction: discord.Interaction, 유형: str, 이름: str, 대상: discord.Member):
        if 대상.id == interaction.user.id:
            await interaction.response.send_message("자신과는 거래할 수 없습니다.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        target_id = str(대상.id)
        
        await interaction.response.defer()
        
        giver = await get_user_inventory(user_id)
        receiver = await get_user_inventory(target_id)
        
        if not giver:
            await interaction.followup.send("당신의 정보를 찾을 수 없습니다.", ephemeral=True)
            return
            
        # Receiver might be Admin (who might not have inventory? Or is Admin just a user?)
        # Existing code checked if target is admin.
        admin_id = await get_admin_id()
        is_admin_transfer = target_id == str(admin_id)

        if not receiver and not is_admin_transfer:
            await interaction.followup.send(f"{대상.display_name}님의 정보를 찾을 수 없습니다.", ephemeral=True)
            return

        # Validate
        if 유형 == "돈":
            if not 이름.isdigit():
                await interaction.followup.send("금액은 숫자여야 합니다.", ephemeral=True)
                return
            amount = int(이름)
            if amount <= 0 or giver["coins"] < amount:
                await interaction.followup.send("코인이 부족하거나 잘못된 금액입니다.", ephemeral=True)
                return
            
            # Execute
            await update_user_inventory(user_id, coins=giver["coins"] - amount)
            if not is_admin_transfer:
                await update_user_inventory(target_id, coins=receiver["coins"] + amount)

        elif 유형 == "아이템":
            if 이름 not in giver["items"]:
                await interaction.followup.send("해당 아이템을 보유하고 있지 않습니다.", ephemeral=True)
                return
            
            new_items = giver["items"].copy()
            new_items.remove(이름)
            await update_user_inventory(user_id, items=new_items)
            
            if not is_admin_transfer:
                rec_items = receiver["items"] + [이름]
                await update_user_inventory(target_id, items=rec_items)

        await interaction.followup.send(f"{대상.mention}님에게 {유형} '{이름}' 거래 완료.")

    @app_commands.command(name="지급", description="[Admin] 아이템이나 코인을 지급합니다.")
    @app_commands.choices(유형=[
        app_commands.Choice(name="코인", value="코인"),
        app_commands.Choice(name="아이템", value="아이템")
    ])
    async def give_command(self, interaction: discord.Interaction, 유형: str, 아이템: str, 대상: discord.Member = None):
        # Admin check logic
        admin_id = await get_admin_id()
        if str(interaction.user.id) != str(admin_id): # Simplified check
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        await interaction.response.defer()
        
        targets = []
        if 대상:
            inv = await get_user_inventory(str(대상.id))
            if inv: targets = [inv]
        else:
            all_users = await get_all_users_inventory()
            targets = list(all_users.values())

        if not targets:
            await interaction.followup.send("대상 러너가 없습니다.", ephemeral=True)
            return

        for user in targets:
            if 유형 == "코인":
                if not 아이템.isdigit(): continue
                new_coins = user["coins"] + int(아이템)
                await update_user_inventory(user["user_id"], coins=new_coins)
            else:
                new_items = user["items"] + [아이템]
                await update_user_inventory(user["user_id"], items=new_items)

        target_name = 대상.display_name if 대상 else "모두"
        await interaction.followup.send(f"{target_name}에게 {유형} '{아이템}' 지급 완료.")

    # Autocompletes skipped to save space/time as they depend on fetching list of items which isn't fully defined. 
    # But for '거래', name autocomplete is useful. I'll add a simple one if needed.

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
