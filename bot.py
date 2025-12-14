
import discord
from discord.ext import commands
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from utils.config import BOT_TOKEN
from utils.sheets import increment_daily_values, get_cached_metadata
from utils.cache import cache_manager
from utils.fishing_data import sync_fishing_data, load_fishing_data
from utils.gacha_data import sync_gacha_data, load_gacha_data
from utils.shop_data import sync_shop_data, load_shop_items
from utils.library_data import sync_library_data, load_library_data

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log")]
)
logger = logging.getLogger(__name__)

# Bot Setup
intents = discord.Intents.default()
intents.presences = True
intents.members = True # Needed for Member converter often
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
    async def setup_hook(self):
        # Load Cogs
        await self.load_extension("cogs.inventory")
        await self.load_extension("cogs.games")
        await self.load_extension("cogs.fishing.core")
        await self.load_extension("cogs.admin.control")
        await self.load_extension("cogs.gacha.core")
        await self.load_extension("cogs.bribe.core")
        await self.load_extension("cogs.shop.cog")
        await self.load_extension("cogs.library.cog")
        await self.tree.sync()
        logger.info("Commands Synced.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Check fishing data
        if not load_fishing_data():
            logger.info("Local fishing data not found. Syncing...")
            await sync_fishing_data()

        # Check gacha data
        if not load_gacha_data():
            logger.info("Local gacha data not found. Syncing...")
            await sync_gacha_data()

        # Check shop data
        if not load_shop_items():
            logger.info("Local shop data not found. Syncing...")
            await sync_shop_data()

        # Check library data
        if not load_library_data():
            logger.info("Local library data not found. Syncing...")
            await sync_library_data()

        # Start Scheduler
        scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Seoul"))
        scheduler.add_job(self.refresh_metadata, 'cron', hour=5, minute=0)
        scheduler.add_job(sync_fishing_data, 'cron', hour=5, minute=0)
        scheduler.add_job(sync_gacha_data, 'cron', hour=5, minute=0)
        scheduler.add_job(sync_shop_data, 'cron', hour=5, minute=0)
        scheduler.add_job(sync_library_data, 'cron', hour=5, minute=0)
        scheduler.start()
        
        # Start Cache Cleanup
        await cache_manager.start_background_cleanup()

    async def refresh_metadata(self):
        await cache_manager.delete("user_metadata")
        await get_cached_metadata()
        logger.info("Metadata refreshed.")

bot = MyBot()

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        logger.error(f"Bot execution failed: {e}")
