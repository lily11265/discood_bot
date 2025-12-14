import discord
import logging
from utils.sheets import update_user_inventory, get_user_inventory

logger = logging.getLogger(__name__)

class FishingView(discord.ui.View):
    def __init__(self, item, price, user_id):
        super().__init__(timeout=60)
        self.item = item
        self.price = price
        self.user_id = str(user_id)
        self.processed = False

    async def disable_all_buttons(self, interaction):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="판매한다", style=discord.ButtonStyle.danger)
    async def sell_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("자신의 낚시 결과만 선택할 수 있습니다.", ephemeral=True)
            return
            
        if self.processed:
            return

        self.processed = True
        await interaction.response.defer()
        
        try:
            user_data = await get_user_inventory(self.user_id)
            if not user_data:
                await interaction.followup.send("유저 정보를 찾을 수 없습니다.", ephemeral=True)
                return

            current_coins = user_data["coins"]
            new_coins = current_coins + self.price
            
            await update_user_inventory(self.user_id, coins=new_coins)
            
            await self.disable_all_buttons(interaction)
            await interaction.followup.send(f"🐟 **{self.item['name']}**을(를) {self.price}원에 판매했습니다! (현재 코인: {new_coins})")
            
        except Exception as e:
            logger.error(f"판매 처리 중 오류: {e}")
            await interaction.followup.send("판매 처리 중 오류가 발생했습니다.", ephemeral=True)

    @discord.ui.button(label="챙긴다", style=discord.ButtonStyle.success)
    async def keep_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("자신의 낚시 결과만 선택할 수 있습니다.", ephemeral=True)
            return

        if self.processed:
            return

        self.processed = True
        await interaction.response.defer()

        try:
            user_data = await get_user_inventory(self.user_id)
            if not user_data:
                await interaction.followup.send("유저 정보를 찾을 수 없습니다.", ephemeral=True)
                return

            current_items = user_data["items"]
            new_items = current_items + [self.item['name']]
            
            await update_user_inventory(self.user_id, items=new_items)
            
            await self.disable_all_buttons(interaction)
            await interaction.followup.send(f"🐟 **{self.item['name']}**을(를) 가방에 챙겼습니다!")

        except Exception as e:
            logger.error(f"아이템 획득 처리 중 오류: {e}")
            await interaction.followup.send("아이템 획득 처리 중 오류가 발생했습니다.", ephemeral=True)
