# Imports
import discord
from discord.ext import commands


# Example cog class
class Miscellaneous(commands.Cog, description="Miscellaneous commands."):
    def __init__(self, bot):
        self.bot = bot

    # Example listener
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')

    # Command: Info
    @commands.command(help="Provide a list of information regarding B.O.B.")
    async def info(self, ctx):
        info_embed = discord.Embed(title='B.O.B Info',
                                   description='test',
                                   color=discord.Color.from_rgb(1, 162, 186))
        info_embed.set_author(name='B.O.B', icon_url=self.bot.avatar)
        info_embed.add_field()

async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))

