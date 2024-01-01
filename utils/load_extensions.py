# Imports
import os
from utils.logger import LogAndPrint

# Create object of Log and LogAndPrint class
logandprint = LogAndPrint()


# Load extension/cog function
async def loadExtensions(bot) -> None:
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            except Exception as e:
                logandprint.error(f'Failed to load cog "{filename[:-3]}" with the following error: {e}')
    return
