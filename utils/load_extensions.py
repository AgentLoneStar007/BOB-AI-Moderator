# Imports
import os


async def loadExtensions(bot):
    for filename in os.listdir("bot/cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"bot.cogs.{filename[:-3]}")
