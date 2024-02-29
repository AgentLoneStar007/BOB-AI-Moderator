# BOB-AI-Moderator
# A Discord bot made in Python using Discord.py, by AgentLoneStar007
# https://github.com/AgentLoneStar007

# Imports
import discord
import pretty_help
from discord import app_commands
from discord.ext import commands, tasks
from pretty_help import PrettyHelp
import wavelink
from dotenv import load_dotenv
import asyncio
import os
import aiohttp.client_exceptions
from transformers import AutoModelForImageClassification
from utils.logger import Log, LogAndPrint, initLoggingUtility
from utils.bot_utils import defIntents, sendMessage, loadExtensions

# Vars
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
BOT_OUTPUT_CHANNEL = os.getenv("BOT_OUTPUT_CHANNEL")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")
custom_status = 'Use "/help" for help.'

# TODO: Add interactive console for bot
# TODO(maybe): Put that console in a web dashboard
# TODO: Finish implementing updated log system
# TODO: Add an update system for BOB that pulls files from the GitHub repo
# TODO: Add a system to scan even text files for bad content
# TODO: Add a system that uses VirusTotal to scan URLs
# TODO: Check into using latest version of Wavelink
# TODO: Utilize the new cleanup() function in every place possible

# Init log system
initLoggingUtility()
log = Log()
logandprint = LogAndPrint()


# Bot class, in which most bot variables and such are declared
class Bot(commands.Bot):
    # Bot init stuff
    def __init__(self) -> None:
        # Set intents
        intents = discord.Intents.default()
        intents.message_content = True

        # Set some bot values and PrettyHelp values
        super().__init__(
            command_prefix='!', owner_id=OWNER_ID, intents=defIntents(), help_command=PrettyHelp(
                color=discord.Color.from_rgb(1, 162, 186),
                index_title='B.O.B Help Menu',

                thumbnail_url='https://cdn.discordapp.com/avatars/1154825794963640390/ff31b0d57ab76713dba89da69a16fe35.webp?size=4096&width=913&height=913',
                menu=pretty_help.AppMenu(ephemeral=True)

            ))

        # Set maintenance mode var
        self.maintenance_mode: bool = False
        self.already_sent_maintenance_mode_notify = False

    # On bot ready...
    async def on_ready(self) -> None:
        # Print a message to the console and log ready event
        print(f'''
\033[32m------------------------------
\033[36m\033[01m{self.user.name}\033[0m\033[32m is online and ready.
Bot ID: \033[37m\033[04m{self.user.id}\033[0m\033[32m
Custom Status: \033[37m\033[04m"{custom_status}"\033[0m\033[32m
------------------------------\033[0m
''')
        log.info(f'{self.user.name} is online and ready.')

        # Change the bots' status
        await self.change_presence(status=discord.Status.online, activity=discord.CustomActivity(custom_status))

        # Activate background task
        self.checkIfMaintenanceModeActive.start()
        return logandprint.info('Started background task "Check If Maintenance Mode is Active."')

    # Create setup hook for Wavelink music player
    async def setup_hook(self) -> None:
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password=LAVALINK_PASSWORD)
        await wavelink.NodePool.connect(client=self, nodes=[node])

    # Add a handler for anyone trying to use old command system
    async def on_command_error(self, ctx, error) -> None:
        message = ('I don\'t support regular bot commands. Instead, I use Discord\'s built-in app commands! Use '
                   '`/help` for a list of available commands.')
        return await ctx.send(message)

    # Task: Check if maintenance mode is active
    @tasks.loop(seconds=3)
    async def checkIfMaintenanceModeActive(self) -> None:
        # If maintenance mode is active,
        if self.maintenance_mode:
            # Disconnect from all voice channels
            for guild in self.guilds:
                voice_client = guild.voice_client
                if voice_client:
                    await voice_client.disconnect(force=True)

            # Update the bots' status
            await self.change_presence(status=discord.Status.do_not_disturb, activity=discord.CustomActivity(
                'MAINTENANCE MODE ACTIVE'))

            # Send a notifying message to staff
            if not self.already_sent_maintenance_mode_notify:
                logandprint.warning('MAINTENANCE MODE IS ACTIVE!')

                await sendMessage(self, BOT_OUTPUT_CHANNEL, 'MAINTENANCE MODE ACTIVATED! All moderation systems'
                                                            ' and utilities are offline!')
                # Update this variable to prevent sending the message multiple times
                self.already_sent_maintenance_mode_notify = True

            return

        # If maintenance mode is off,
        if not self.maintenance_mode:
            # Get the bot as a member of a guild object(the following wouldn't work if the bot were in multiple servers)
            bot_member = self.guilds[0].get_member(self.user.id)

            if bot_member:
                # If the status is not online,
                if str(bot_member.status) != 'online':
                    # Update it to online
                    await self.change_presence(status=discord.Status.online, activity=discord.CustomActivity(custom_status))

                    # Log that maintenance mode is no longer active
                    logandprint.info('Maintenance mode is no longer active.')

        return


# Main program function
async def run() -> None:
    # Create the bot from the Bot class
    bot = Bot()

    # Add some error handling for slash commands. I'm putting this down here, and not in the Bot class, because I need
    #  to use the "bot" variable, but I'm not smart enough to access the bot variable inside the class.
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        # Handler for missing permissions
        if isinstance(error, app_commands.MissingPermissions):
            logandprint.info(f'User {interaction.user.name} was unable to run command "{interaction.command.name}" due to insufficient permissions.', source='d')
            return await interaction.response.send_message('You don\'t have permission to use this command.', ephemeral=True)

        if isinstance(error, app_commands.CommandOnCooldown):
            logandprint.warning(f'User {interaction.user.name} was unable to run command "{interaction.command.name}" because it\'s'
                  ' on cooldown.', source='d')
            return await interaction.response.send_message(f'This command is on cooldown!', ephemeral=True)

        # TODO: Add a specific error message when the bot is unable to respond to an interaction because it timed out.
        # Handler for failing to respond to an interaction quickly enough
        if isinstance(error, discord.app_commands.CommandInvokeError):
            return logandprint.error(f"Failed to respond to command \"{interaction.command.name}\" run by"
                         f" {interaction.user.display_name} because the interaction either timed out or failed. Error: {error}", source='d')

        # So far no other handlers are required, because AppCommands automatically requires correct argument types
        # and "CommandNotFound" errors are (to my knowledge) impossible with slash commands.

        # General error handler
        else:
            # Defining the error message as a variable for optimization
            logandprint.error(f'An error occurred when the user {interaction.user.display_name} tried to run the command'
                              f' {interaction.command.name}: "{type(error)}: {error}"', source='d')
            return await interaction.response.send_message(
                f'An error occurred when trying to run that command:\n```{error}```', ephemeral=True)

    # Load extensions and start bot, all in time with the bot itself
    async with bot:
        await loadExtensions(bot)
        await bot.start(BOT_TOKEN)


def main() -> int:
    # Put bot in a try/except for error handling
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logandprint.info('Shutting down!')
        return 0
    except aiohttp.client_exceptions.ClientConnectorError:
        logandprint.fatal(f'B.O.B was unable to connect to either the Internet or Discord. Check your connection.')
        return 1
    except Exception as e:
        logandprint.fatal(f'B.O.B encountered a critical error and had to shut down! Error: {e}')
        return 1


# Start the bot
if __name__ == "__main__":
    main()

