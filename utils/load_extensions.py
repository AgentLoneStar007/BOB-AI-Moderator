# Imports
import os


# TODO: Change extension loading system to app-command system
async def loadExtensions(bot):
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f'cogs.{filename[:-3]}')
