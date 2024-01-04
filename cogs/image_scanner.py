# Imports
import discord
from discord.ext import commands
from utils.logger import Log, LogAndPrint

# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()


class ImageScanner(commands.Cog, description="Example cog description."):
    def __init__(self, bot) -> None:
        self.bot = bot
        return

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return logandprint.logCogLoad(self.__class__.__name__)

    async def scanImage(self, message: discord.Message) -> bool:
        # Coming soon...

        # TODO: When image scanner is complete, this function will return True if media passed the test,
        #  and False otherwise. I'm leaving it statically as True until the system is complete.
        return True


async def setup(bot) -> None:
    return await bot.add_cog(ImageScanner(bot))
