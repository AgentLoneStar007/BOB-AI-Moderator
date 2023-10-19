# Imports
import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import logCommand, log


# TODO: Either figure out hybrid commands, or use app commands everywhere


class Miscellaneous(commands.Cog, description="Miscellaneous commands."):
    def __init__(self, bot):
        self.bot = bot

    # Custom owner check function for app commands
    async def checkIfOwner(self, interaction: discord.Interaction):
        if not interaction.user.id == self.bot.owner_id:
            await interaction.response.send_message('Only the owner can use this command.', ephemeral=True)
            return False
        return True

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')

    # Command: Info
    @app_commands.command(name='info', description='Provide a list of information regarding B.O.B.')
    async def info(self, interaction: discord.Interaction):
        creation_date = self.bot.user.created_at.strftime("%A, %B %d, %Y")
        info_embed = discord.Embed(
            title='B.O.B Info',
            description='This bot was designed solely for moderation and utilities on the LoneStar Gaming Community Discord.',
            color=discord.Color.from_rgb(1, 162, 186))
        info_embed.add_field(name='Created On:', value=f'{creation_date}')
        info_embed.add_field(name='Author:', value='AgentLoneStar007')
        info_embed.add_field(name='Code:', value='[GitHub](https://github.com/AgentLoneStar007/BOB-AI-Moderator)')
        info_embed.add_field(name='Made In:', value='Python')
        info_embed.add_field(name='Using:', value='[Discord.py](https://github.com/Rapptz/discord.py)')

        await interaction.response.send_message(embed=info_embed, ephemeral=True)
        logCommand(interaction.user, 'info', interaction.channel)

    @app_commands.command(name='load', description='Load a cog. (Only usable by bot owner.)')
    async def load(self, interaction: discord.Interaction, cog_name: str):
        # Format the cog name
        cog_name = cog_name.lower()

        # Check if the user is the owner
        if not await self.checkIfOwner(interaction):
            return

        # Try to load the cog
        try:
            await self.bot.load_extension(f'cogs.{cog_name}')
            await interaction.response.send_message(
                f'The cog "{cog_name}" was successfully mounted and started.', ephemeral=True)
            log('info', f'Loaded the cog "{cog_name}" successfully.')
        # Throw an error if failed
        except commands.ExtensionError as e:
            await interaction.response.send_message(
                f'An error occurred while unloading cog "{cog_name}": {e}', ephemeral=True)
            log('err', f'Failed to load cog "{cog_name}" with the following error: {e}')

    @app_commands.command(name='unload', description='Unload a cog. (Only usable by bot owner.)')
    async def unload(self, interaction: discord.Interaction, cog_name: str):
        cog_name = cog_name.lower()

        # Check if the user is the owner
        if not await self.checkIfOwner(interaction):
            return

        # Prevent unloading of miscellaneous cog (with stupid formatting because PyCharm yells at me)
        if cog_name == 'miscellaneous':
            return await interaction.response.send_message('Cannot unload cog Miscellaneous, as because it contains cog'
                                                           ' loading utility commands. Restart the bot to apply changes'
                                                           ' to cog Miscellaneous.', ephemeral=True)

        # Try to unload cog
        try:
            await self.bot.unload_extension(f'cogs.{cog_name}')
            return await interaction.response.send_message(f'The cog "{cog_name}" was successfully unloaded.', ephemeral=True)
        # Handle any errors that may occur
        except commands.ExtensionError as e:
            return await interaction.response.send_message(f'An error occurred while unloading cog "{cog_name}": {e}')

    @app_commands.command(name='reload', description='Reload a cog. (Only usable by bot owner.)')
    async def reload(self, interaction: discord.Interaction, cog_name: str):
        cog_name = cog_name.lower()

        # Check if the user is the owner
        if not await self.checkIfOwner(interaction):
            return

        # Try to reload cog
        try:
            await self.bot.reload_extension(f'cogs.{cog_name}')
            return await interaction.response.send_message(f'The cog "{cog_name.title()}" was successfully reloaded.',
                                                           ephemeral=True)
        # Handle unload errors
        except commands.ExtensionError as e:
            return await interaction.response.send_message(f'An error occurred while reloading cog "{cog_name}": {e}',
                                                           ephemeral=True)

    @app_commands.command(name='synccommands', description='Sync all app commands with Discord. (Only usable by bot owner.)')
    async def synccommands(self, interaction: discord.Interaction):
        # Check if the user is the owner
        if not await self.checkIfOwner(interaction):
            return

        try:
            # Try and sync bot commands
            synced = await self.bot.tree.sync()
            # Assign message to variable for efficiency
            message = f'Synced {len(synced)} command(s) with Discord.'
            print(message)
            await interaction.response.send_message(message, ephemeral=True)
            log('info', message)
        except Exception as e:
            # More efficiency; log and print the error
            message = f'Failed to sync commands with the following error: {e}'
            print(message)
            await interaction.response.send_message(message, ephemeral=True)
            log('err', message)


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))
