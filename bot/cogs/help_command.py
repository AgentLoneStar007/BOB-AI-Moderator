# Imports
from discord.ext import commands


# Cog class
class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')

    @commands.command()
    async def test(self, ctx):
        await ctx.send("Hello, world!")


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))

