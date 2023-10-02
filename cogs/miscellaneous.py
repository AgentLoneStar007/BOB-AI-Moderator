# Imports
import discord
from discord.ext import commands
from utils.logger import logCommand


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
        info_embed = discord.Embed(
            title='B.O.B Info',
            description='This bot was designed solely for moderation and utilities on the LoneStar Gaming Community Discord.',
            color=discord.Color.from_rgb(1, 162, 186))
        info_embed.add_field(name='Created On:', value=f'{creation_date}')
        info_embed.add_field(name='Author:', value='AgentLoneStar007')
        info_embed.add_field(name='Code:', value='[GitHub](https://github.com/AgentLoneStar007/BOB-AI-Moderator) (currently private)')
        info_embed.add_field(name='Made In:', value='Python')

        await ctx.send(embed=info_embed)
        logCommand(ctx.author, 'info', ctx.channel)

    @commands.command(help='Load a cog. (Only usable by bot owner.)')
    @commands.is_owner()
    async def load(self, ctx, cog_name: str):
        try:
            self.bot.load_extension(cog_name)
            await ctx.send(f'The cog "{cog_name}" was successfully mounted and started.')
        except commands.ExtensionError as e:
            await ctx.send(f'An error occurred while unloading cog "{cog_name}": {e}')

    @commands.command(help='Unload a cog. (Only usable by bot owner.)')
    @commands.is_owner()
    async def unload(self, ctx, cog_name: str):
        # TODO: WORK HERE!!
        if cog_name == 'Miscellaneous':
            return await ctx.send('amogus')
        try:
            self.bot.unload_extension(cog_name)
            await ctx.send(f'The cog "{cog_name}" was successfully unloaded.')
        except commands.ExtensionError as e:
            await ctx.send(f'An error occurred while unloading cog "{cog_name}": {e}')

    @commands.command(help='Reload a cog. (Only usable by bot owner.)')
    @commands.is_owner()
    async def reload(self, ctx, cog_name: str):
        try:
            self.bot.reload_extension(cog_name)
            await ctx.send(f'The cog "{cog_name}" was successfully reloaded.')
        except commands.ExtensionError as e:
            await ctx.send(f'An error occurred while unloading cog "{cog_name}": {e}')


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))

