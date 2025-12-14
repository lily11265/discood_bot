
import discord
import random
from utils.sheets import get_user_inventory, update_user_inventory

class OddEvenGameView(discord.ui.View):
    def __init__(self, user_id, bet_amount, app_invoke_interaction, multiplier=2, total_net_change=0):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.interaction = app_invoke_interaction
        self.multiplier = multiplier
        self.total_net_change = total_net_change
        self.game_active = True
        
        self.dice1 = random.randint(1, 6)
        self.dice2 = random.randint(1, 6)
        self.dice3 = 0 

    @discord.ui.button(label="홀수", style=discord.ButtonStyle.primary, custom_id="odd")
    async def odd_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice(interaction, "odd")

    @discord.ui.button(label="짝수", style=discord.ButtonStyle.secondary, custom_id="even")
    async def even_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice(interaction, "even")

    async def process_choice(self, interaction: discord.Interaction, choice: str):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("자신의 게임만 진행할 수 있습니다.", ephemeral=True)
            return
        
        self.dice3 = random.randint(1, 6)
        total = self.dice1 + self.dice2 + self.dice3
        is_odd = (total % 2) != 0
        result_str = "홀수" if is_odd else "짝수"
        user_won = (choice == "odd" and is_odd) or (choice == "even" and not is_odd)
        
        user_data = await get_user_inventory(self.user_id)
        current_coins = user_data["coins"]
        
        # Deduct bet for this round
        current_coins -= self.bet_amount
        
        net_round = 0
        if user_won:
            add_val = self.bet_amount * self.multiplier
            current_coins += add_val
            net_round = add_val - self.bet_amount
            msg_title = "승리!"
            color = discord.Color.green()
        else:
            deduct_val = self.bet_amount * (self.multiplier - 1)
            current_coins -= deduct_val
            net_round = -self.bet_amount - deduct_val
            msg_title = "패배..."
            color = discord.Color.red()

        self.total_net_change += net_round
        
        await update_user_inventory(self.user_id, coins=current_coins)
        
        embed = interaction.message.embeds[0]
        
        # Check for Bust
        if current_coins <= 0:
            embed.title = "게임 종료 (파산)"
            embed.color = discord.Color.dark_red()
            embed.description = (
                f"주사위: {self.dice1}, {self.dice2}, **{self.dice3}** (합: {total}, {result_str})\n"
                f"선택: {'홀수' if choice=='odd' else '짝수'}\n"
                f"결과: {net_round:+d} 코인\n\n"
                f"게임 끝. **{interaction.user.display_name}**님은 총 {self.total_net_change:+d}원 획득하셨습니다.\n"
                f"현재 잔고 {current_coins}원."
            )
            embed.set_footer(text="")
            self.clear_items()
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()
        else:
            embed.title = msg_title
            embed.color = color
            embed.description = (
                f"주사위: {self.dice1}, {self.dice2}, **{self.dice3}** (합: {total}, {result_str})\n"
                f"선택: {'홀수' if choice=='odd' else '짝수'}\n"
                f"결과: {net_round:+d} 코인\n"
                f"현재 잔고: {current_coins}"
            )
            
            self.clear_items()
            cont_btn = discord.ui.Button(label="계속 하기", style=discord.ButtonStyle.success, custom_id="continue")
            cont_btn.callback = self.continue_game
            
            quit_btn = discord.ui.Button(label="그만두기", style=discord.ButtonStyle.danger, custom_id="quit")
            quit_btn.callback = self.quit_game
            
            self.add_item(cont_btn)
            self.add_item(quit_btn)
            
            await interaction.response.edit_message(embed=embed, view=self)

    async def continue_game(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id: return
        
        # Disable current view first
        self.stop()
        await interaction.response.edit_message(view=None) # Disable old message interactions
        
        # Start new round with new View and Message
        new_multiplier = self.multiplier + 1
        
        new_view = OddEvenGameView(
            self.user_id, 
            self.bet_amount, 
            self.interaction, 
            multiplier=new_multiplier, 
            total_net_change=self.total_net_change
        )
        
        embed = discord.Embed(
            title="주사위는 던져졌다...",
            description=f"주사위: {new_view.dice1}, {new_view.dice2}, ?\n배팅 금액: {self.bet_amount} (배수: {new_multiplier}배)",
            color=discord.Color.blue()
        )
        
        # Changed to ephemeral=False
        await interaction.followup.send(embed=embed, view=new_view, ephemeral=False)

    async def quit_game(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id: return
        
        user_data = await get_user_inventory(self.user_id)
        current_coins = user_data["coins"]
        
        embed = interaction.message.embeds[0]
        embed.title = "게임 종료"
        embed.color = discord.Color.gold()
        embed.description = (
            f"게임 끝. **{interaction.user.display_name}**님은 총 {self.total_net_change:+d}원 획득하셨습니다.\n"
            f"현재 잔고 {current_coins}원. 축하합니다!!"
        )
        embed.set_footer(text="")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
