
from .cog import GamesCog

async def setup(bot):
    await bot.add_cog(GamesCog(bot))
