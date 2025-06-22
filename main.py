import asyncio
from bot.core import get_bot
import dst
import os

bot = get_bot()

async def main():
    for cog in [
        'bot.cogs.archivos',
        'bot.cogs.entregas',
        'bot.cogs.otros',
        'bot.cogs.moderacion',
    ]:
        await bot.load_extension(cog)
    await bot.start(dst.TOKEN)

if __name__ == "__main__":
    asyncio.run(main())