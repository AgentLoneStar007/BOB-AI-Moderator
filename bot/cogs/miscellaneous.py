# Imports
import discord
from discord import app_commands
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
        creation_date = self.bot.user.created_at.strftime("%A, %B %d, %Y")
        info_embed = discord.Embed(title='B.O.B Info',
                                   description='This bot was designed solely for moderation and utilities on the LoneStar Gaming Community Discord.',
                                   color=discord.Color.from_rgb(1, 162, 186))
        info_embed.add_field(name='Created On:', value=f'{creation_date}')
        info_embed.add_field(name='Author:', value='AgentLoneStar007')
        info_embed.add_field(name='Code:', value='[GitHub](https://github.com/AgentLoneStar007/BOB-AI-Moderator) (currently private)')

        await ctx.send(embed=info_embed)


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))

