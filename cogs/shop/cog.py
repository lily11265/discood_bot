import discord
from discord import app_commands
from discord.ext import commands
import logging
from collections import Counter
from utils.shop_data import load_shop_items, get_shop_open_status
from utils.fishing_data import load_fishing_data
from utils.sheets import get_user_inventory
from cogs.shop.logic import process_sell, process_buy

logger = logging.getLogger(__name__)

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="상점", description="물건을 구매하거나 판매합니다.")
    @app_commands.describe(action="구매 또는 판매", item="아이템 이름", amount="수량")
    async def shop(self, interaction: discord.Interaction, action: str, item: str, amount: str):
        if not get_shop_open_status():
            await interaction.response.send_message("상점이 문닫았습니다.", ephemeral=True)
            return

        inv = await get_user_inventory(str(interaction.user.id))
        if not inv:
            await interaction.response.send_message("인벤토리를 찾을 수 없습니다.", ephemeral=True)
            return

        if action == "판매":
            await process_sell(interaction, inv, item, amount)
        elif action == "구입":
            await process_buy(interaction, inv, item, amount)
        else:
            await interaction.response.send_message("잘못된 접근입니다.", ephemeral=True)

    @shop.autocomplete("action")
    async def action_autocomplete(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name="판매", value="판매"), app_commands.Choice(name="구입", value="구입")]

    @shop.autocomplete("item")
    async def item_autocomplete(self, interaction: discord.Interaction, current: str):
        action = interaction.namespace.action
        inv = await get_user_inventory(str(interaction.user.id))
        
        if action == "판매":
            if not inv: return []
            f_data = load_fishing_data()
            f_names = {f["name"]: f["price"] for f in f_data}
            
            user_items = [i for i in inv["items"] if i in f_names]
            cnt = Counter(user_items)
            
            choices = []
            for name, count in cnt.items():
                price = f_names[name]
                if name.startswith(current):
                    choices.append(app_commands.Choice(name=f"{name} (개당 {price}코인, 보유 {count}개)", value=name))
            
            choices.append(app_commands.Choice(name=f"전부 (모든 낚시 아이템 판매)", value="전부"))
            return choices[:25]
            
        elif action == "구입":
            s_items = load_shop_items()
            choices = []
            for item in s_items:
                if item["quantity"] > 0 and item["name"].startswith(current):
                    choices.append(app_commands.Choice(
                        name=f"{item['name']} - {item['price']}코인 ({item['description']})", 
                        value=item['name']
                    ))
            return choices[:25]
        return []

    @shop.autocomplete("amount")
    async def amount_autocomplete(self, interaction: discord.Interaction, current: str):
        action = interaction.namespace.action
        item_name = interaction.namespace.item
        
        if not action or not item_name: return []
        
        if action == "판매":
            if item_name == "전부":
                return [app_commands.Choice(name="선택불가 (전체 판매)", value="0")]
            
            inv = await get_user_inventory(str(interaction.user.id))
            if not inv: return []
            cnt = inv["items"].count(item_name)
            return [app_commands.Choice(name=f"{cnt}개 (보유량)", value=str(cnt))]
            
        elif action == "구입":
            s_items = load_shop_items()
            target = next((x for x in s_items if x["name"] == item_name), None)
            if target:
                return [app_commands.Choice(name=f"{target['quantity']}개 (재고)", value=str(target['quantity']))]
        
        return []

async def setup(bot):
    await bot.add_cog(ShopCog(bot))
