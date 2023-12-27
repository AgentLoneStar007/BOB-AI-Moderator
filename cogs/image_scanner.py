# Imports
import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import Log, logCogLoad
from utils.bot_utils import checkIfOwner

# Create object of Log class
log = Log()


class ImageScanner(commands.Cog, description="Example cog description."):
    def __init__(self, bot) -> None:
        self.bot = bot
        return

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logCogLoad(self.__class__.__name__)
        return print(f'Extension loaded: {self.__class__.__name__}')

    async def scanImage(self, message: discord.Message) -> None:
        # Coming soon...
        return


async def setup(bot) -> None:
    return await bot.add_cog(ImageScanner(bot))
