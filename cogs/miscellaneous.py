# Imports
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import shutil
import subprocess
from utils.logger import Log, LogAndPrint
from utils.bot_utils import checkIfOwner, loggingMention

# TODO: Add cool-downs to commands to prevent spamming(which may or may not work)

# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()

# Vars
load_dotenv()
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")


class Miscellaneous(commands.Cog, description="Miscellaneous commands."):
    def __init__(self, bot) -> None:
        self.bot = bot
        return

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return logandprint.logCogLoad(self.__class__.__name__)

    # Command: Info
    @app_commands.command(name="info", description="Provide a list of information regarding B.O.B.")
    async def info(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        creation_timestamp = int(self.bot.user.created_at.timestamp())
        info_embed = discord.Embed(
            title="B.O.B Info",
            description="**B.O.B**: Basic Operations and Bouncer.\n\nThis bot was designed solely for moderation and "
                        "server management utilities on the LoneStar Gaming Community Discord.",
            color=discord.Color.from_rgb(1, 162, 186))
        info_embed.add_field(name="Created:", value=f"<t:{creation_timestamp}:R>", inline=False)
        info_embed.add_field(name="Author:", value="<@403735483961704450>", inline=False)
        info_embed.add_field(name="Code:", value="[GitHub](https://github.com/AgentLoneStar007/BOB-AI-Moderator)")
        info_embed.add_field(name="Made In:", value="Python")
        info_embed.add_field(name="Using:", value="[Discord.py](https://github.com/Rapptz/discord.py)")

        await interaction.response.send_message(embed=info_embed, ephemeral=True)
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: Load
    @app_commands.command(name="load", description="Load a cog. (Only usable by bot owner.)")
    @app_commands.describe(cog_name="The name of the cog to load.")
    async def load(self, interaction: discord.Interaction, cog_name: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Format the cog name
        cog_name = cog_name.lower().replace(' ', '_')

        # Check if the user is the owner
        if not await checkIfOwner(interaction):
            return

        # Try to load the cog
        try:
            await self.bot.load_extension(f"cogs.{cog_name}")
            await interaction.response.send_message(
                f"The cog \"{cog_name.title().replace('_', ' ')}\" was successfully loaded and started.",
                ephemeral=True)
            return logandprint.info(f"Loaded the cog \"{cog_name}\" successfully.")
        # Throw an error if failed
        except commands.ExtensionError as e:
            # Throw a specific error if the cog can't be found
            if isinstance(e, discord.ext.commands.ExtensionNotFound):
                return await interaction.response.send_message(
                    f"The cog \"{cog_name.title().replace('_', ' ')}\" could not be loaded. Are you sure"
                    f" you spelled the name correctly?", ephemeral=True)
            await interaction.response.send_message(
                f"An error occurred while loading cog \"{cog_name}\": ```{e}```", ephemeral=True)
            return logandprint.error(f"Failed to load cog \"{cog_name}\" with the following error: {e}")

    # Command: Unload
    @app_commands.command(name="unload", description="Unload a cog. (Only usable by bot owner.)")
    @app_commands.describe(cog_name="The name of the cog to unload.")
    async def unload(self, interaction: discord.Interaction, cog_name: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Format the cog name
        cog_name = cog_name.lower().replace(' ', '_')

        # Check if the user is the owner
        if not await checkIfOwner(interaction):
            return

        # Prevent unloading of miscellaneous cog (with stupid formatting because PyCharm yells at me)
        if cog_name == "miscellaneous":
            return await interaction.response.send_message("Cannot unload cog Miscellaneous, as because it contains cog"
                                                           " loading utility commands. Restart the bot to apply changes"
                                                           " to the Miscellaneous cog.", ephemeral=True)
        # Try to unload cog
        try:
            await self.bot.unload_extension(f"cogs.{cog_name}")
            await interaction.response.send_message(f"The cog \"{cog_name.title().replace('_', ' ')}\" was "
                                                    "successfully unloaded.", ephemeral=True)
            return logandprint.info(f"The cog \"{cog_name}\" was unloaded.")

        # Throw an error if unloading the cog fails
        except commands.ExtensionError as e:
            # Throw a specific error if the cog hasn't been loaded
            if isinstance(e, discord.ext.commands.ExtensionNotLoaded):
                return await interaction.response.send_message(f"The cog \"{cog_name}\" has not been loaded. Are you"
                                                               " sure you spelled the name correctly?",
                                                               ephemeral=True)
            await interaction.response.send_message(f"An error occurred while unloading the cog \"{cog_name}\": ```{e}```")
            return logandprint.error(f"An error occurred while unloading the cog \"{cog_name}\": {e}")

    # Command: Reload
    @app_commands.command(name="reload", description="Reload a cog. (Only usable by bot owner.)")
    @app_commands.describe(cog_name="The name of the cog to reload.")
    async def reload(self, interaction: discord.Interaction, cog_name: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Format the cog name
        cog_name = cog_name.lower().replace(' ', '_')

        # Check if the user is the owner
        if not await checkIfOwner(interaction):
            return

        # Try to reload cog
        try:
            await self.bot.reload_extension(f"cogs.{cog_name}")
            await interaction.response.send_message(f"The cog \"{cog_name.title().replace('_', ' ')}\" was "
                                                    "successfully reloaded.", ephemeral=True)
            return logandprint.info(f"Reloaded cog \"{cog_name}.\"")

        # Throw an error if failed
        except commands.ExtensionError as e:
            # Throw a specific error if the cog hasn't been loaded
            if isinstance(e, discord.ext.commands.ExtensionNotLoaded):
                return await interaction.response.send_message(f"The cog \"{cog_name.title().replace('_', ' ')}"
                                                               "\" has not been loaded. Are you sure you spelled the"
                                                               "name correctly?", ephemeral=True)
            await interaction.response.send_message("An error occurred while reloading cog"
                                                    f"\"{cog_name.title().replace('_', ' ')}\": ```{e}```",
                                                    ephemeral=True)
            return logandprint.error(f"An error occurred while reloading cog \"{cog_name}\": {e}")

    # Command: Sync Commands
    @app_commands.command(name="synccommands",
                          description="Sync all app commands with Discord. (Only usable by bot owner.)")
    async def syncCommands(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check if the user is the owner
        if not await checkIfOwner(interaction):
            return

        try:
            # Try and sync bot commands
            synced = await self.bot.tree.sync()
            # If zero commands were synced, format the message to notify that it's probably an error
            if not synced:
                await interaction.response.send_message("Synced no commands with Discord. If this is in error, check"
                                                        "that all modules are loaded properly.", ephemeral=True)
                return logandprint.warning("When syncing bot commands with Discord, no commands were synced. "
                                           "If this is in error, check that all modules are loaded.", source='d')
            # Make the message look good by correctly using an "s" after commands if there's more than one command
            elif len(synced) == 1:
                message: str = "Synced one command with Discord."
            else:
                message: str = f"Synced {len(synced)} commands with Discord."
            await interaction.response.send_message(message, ephemeral=True)
            return logandprint.info(message, source='d')
        except Exception as error:
            # More efficiency; log and print the error
            message = f"Failed to sync commands with the following error: {error}"
            await interaction.response.send_message(message, ephemeral=True)
            return logandprint.error(message, source='d')

    # Command: Update
    @app_commands.command(name="update",
                          description="Update BOB by pulling latest changes from his Git repository. (Only usable by bot owner.)")
    async def update(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check if the user is the owner
        if not await checkIfOwner(interaction):
            return

        return await interaction.response.send_message('This feature is a work-in-progress!', ephemeral=True)

        # Leaving the following code for now, even though it does nothing, because I found out it doesn't actually
        # work if I deploy BOB to a server, since .env files and changes to the venv are not synced to the Git
        # repository. I will revisit this later, once I have a better idea of how BOB will be hosted and how updates
        # can be served.
        already_sent_message: bool = False

        try:
            discord_log: str = 'Started a system update. Please wait...'

            # Send a notifying message
            await interaction.response.send_message('Started a system update. Please wait...', ephemeral=True)
            # This is here for error handling, as seen below in the Except
            already_sent_message = True

            # Log system update
            logandprint.info('Starting system update...')

            # Create folder to store update files
            os.mkdir('data/update_files/root')

            # Notify of download
            discord_log = discord_log + '\nDownloading update files...'
            await interaction.edit_original_response(content=discord_log)

            # Start download
            try:
                logandprint.debug('Started download of update files...')
                subprocess.run(['git', 'clone', GITHUB_REPO_URL, 'data/update_files/root'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except subprocess.CalledProcessError as e:
                logandprint.error(f'The following error occurred during the download of the update files: {e}')
                discord_log = discord_log + f'The following error occurred during the download of the update files: ```{e}```For safety reasons, the update will not continue. Please update manually.'
                await interaction.edit_original_response(content=discord_log)
                return

            # Zip update files into an archive
            shutil.make_archive('data/update_files/update', 'zip', 'data/update_files/root')

            # Update message to notify download is done
            logandprint.debug('Download complete. Starting upgrade...')

            # Activate maintenance mode
            self.bot.maintenance_mode = True

            # Wait three seconds to make sure the maintenance mode check background task runs before the bot is updated
            await asyncio.sleep(3)

            # Update Discord message
            discord_log = discord_log + '\nDownload complete. Starting system upgrade...'
            await interaction.edit_original_response(content=discord_log)

        except Exception as e:
            message: str = f'The following error occurred when attempting to update: {e}'
            if already_sent_message:
                # If a message has already been sent, update it
                await interaction.edit_original_response(content=message)
            else:
                # Otherwise, send a new message
                await interaction.response.send_message(message, ephemeral=True)

        finally:
            # Clean up temporary files
            shutil.rmtree('data/update_files/root', ignore_errors=True)
            logandprint.debug('Cleaned')

        return


# Cog setup hook
async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))
