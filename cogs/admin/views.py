import discord
from utils.settings import load_settings, save_settings
from utils.shop_data import sync_shop_data, get_shop_open_status, set_shop_open_status
from utils.library_data import sync_library_data

class ControlPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.select(
        placeholder="변경할 설정을 선택하세요",
        options=[
            discord.SelectOption(label="낚시 쿨타임 변경", value="f_cooldown", description="낚시 쿨타임 조정"),
            discord.SelectOption(label="가격 계산 모드 변경", value="price_mode", description="낚시 가격 방식 변경"),
            discord.SelectOption(label="가챠 쿨타임 변경", value="g_cooldown", description="가챠 쿨타임 조정"),
            discord.SelectOption(label="가챠 비용 변경", value="g_cost", description="가챠 비용 조정"),
            discord.SelectOption(label="뇌물 최대 코인 변경", value="b_max", description="뇌물 최대치 조정"),
            discord.SelectOption(label="뇌물 실패 확률 변경", value="b_fail", description="뇌물 실패(거절) 확률 조정"),
            discord.SelectOption(label="상점 상태 토글", value="toggle_shop", description="상점을 열거나 닫습니다"),
            discord.SelectOption(label="상점 데이터 동기화", value="sync_shop", description="구글 시트에서 상점 데이터 동기화"),
            discord.SelectOption(label="도서관 쿨타임 변경", value="l_cooldown", description="도서찾기 쿨타임 조정"),
            discord.SelectOption(label="도서관 상태 토글", value="toggle_lib", description="도서관을 열거나 닫습니다"),
            discord.SelectOption(label="도서관 데이터 동기화", value="sync_lib", description="구글 시트에서 도서 데이터 동기화")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0]
        if val == "f_cooldown":
            await interaction.response.send_modal(inputModal(self.cog, "fishing_cooldown_hours", "낚시 쿨타임 (시간)", int))
        elif val == "g_cooldown":
            await interaction.response.send_modal(inputModal(self.cog, "gacha_cooldown_hours", "가챠 쿨타임 (시간)", int))
        elif val == "g_cost":
            await interaction.response.send_modal(inputModal(self.cog, "gacha_cost", "가챠 비용 (코인)", int))
        elif val == "b_max":
            await interaction.response.send_modal(inputModal(self.cog, "bribe_max_coin", "뇌물 최대 코인", int))
        elif val == "b_fail":
            await interaction.response.send_modal(inputModal(self.cog, "bribe_fail_rate", "뇌물 실패 확률 (%)", float))
        elif val == "l_cooldown":
            await interaction.response.send_modal(inputModal(self.cog, "library_cooldown_hours", "도서관 쿨타임 (시간)", int))
        elif val == "price_mode":
            await interaction.response.send_message(
                "가격 계산 모드를 선택하세요.", 
                view=PriceModeView(self.cog, self), 
                ephemeral=True
            )
        elif val == "toggle_shop":
            cur = get_shop_open_status()
            set_shop_open_status(not cur)
            embed = self.cog.create_status_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        elif val == "sync_shop":
            await interaction.response.defer(ephemeral=True)
            res = await sync_shop_data()
            msg = f"상점 데이터 {len(res)}개 동기화 완료." if res is not False else "동기화 실패."
            await interaction.followup.send(msg, ephemeral=True)
        elif val == "toggle_lib":
            s = load_settings()
            cur = s.get("library_open", True)
            s["library_open"] = not cur
            save_settings(s)
            embed = self.cog.create_status_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        elif val == "sync_lib":
            await interaction.response.defer(ephemeral=True)
            res = await sync_library_data()
            msg = f"도서관 데이터 {len(res)}권 동기화 완료." if res is not False else "동기화 실패."
            await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="새로고침", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.cog.create_status_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class inputModal(discord.ui.Modal):
    answer = discord.ui.TextInput(label="값 입력", placeholder="숫자(소수점 가능)만 입력하세요")

    def __init__(self, cog, setting_key, title_txt, value_type):
        super().__init__(title=title_txt)
        self.cog = cog
        self.setting_key = setting_key
        self.value_type = value_type

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = self.value_type(self.answer.value)
            if val < 0: raise ValueError
            
            settings = load_settings()
            settings[self.setting_key] = val
            save_settings(settings)
            
            embed = self.cog.create_status_embed()
            view = ControlPanelView(self.cog)
            await interaction.response.edit_message(content="✅ 설정이 변경되었습니다.", embed=embed, view=view)
            
        except ValueError:
            await interaction.response.send_message("올바른 형식이 아닙니다.", ephemeral=True)

class PriceModeView(discord.ui.View):
    def __init__(self, cog, parent_view):
        super().__init__()
        self.cog = cog
        self.parent_view = parent_view

    @discord.ui.button(label="고정 가격", style=discord.ButtonStyle.primary)
    async def fixed_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.update_setting(False)
        await interaction.response.edit_message(content="가격 모드가 '고정 가격'으로 변경되었습니다.", view=None)

    @discord.ui.button(label="변동 가격 (길이 비례)", style=discord.ButtonStyle.success)
    async def variable_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.update_setting(True)
        await interaction.response.edit_message(content="가격 모드가 '변동 가격'으로 변경되었습니다.", view=None)

    def update_setting(self, value):
        settings = load_settings()
        settings["price_multiplier_mode"] = value
        save_settings(settings)
