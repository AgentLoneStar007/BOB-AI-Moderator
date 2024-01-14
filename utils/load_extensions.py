# Imports
import os
from utils.logger import LogAndPrint

# Create object of Log and LogAndPrint class
logandprint = LogAndPrint()


# Load extension/cog function
async def loadExtensions(bot) -> None:
    # For all files in the cogs directory,
    for filename in os.listdir('cogs'):
        # If the file ends with .py,
        if filename.endswith('.py'):
            # Try to load it as a cog
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            # And log it if it fails
            except Exception as e:
                logandprint.error(f'Failed to load cog "{filename[:-3]}" with the following error: {e}')
    return
