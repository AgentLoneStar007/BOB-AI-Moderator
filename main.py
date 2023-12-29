## BOB-AI-Moderator
## A Discord bot made in Python using Discord.py, by AgentLoneStar007
## https://github.com/AgentLoneStar007


# Imports
import discord
import pretty_help
from discord import app_commands
from discord.ext import commands
from pretty_help import PrettyHelp
import wavelink
from dotenv import load_dotenv
import asyncio
import os
from utils.load_extensions import loadExtensions
from utils.logger import Log, LogAndPrint, initLoggingUtility
from utils.bot_utils import defIntents

# Vars
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
WAVELINK_PASSWORD = os.getenv("WAVELINK_PASSWORD")
custom_status = 'Use "/help" for help.'

# TODO: Add interactive console for bot
# TODO(maybe): Put that console in a web dashboard
# TODO: Finish implementing updated log system
# TODO: Add an update system for BOB that pulls files from the GitHub repo
# TODO: Add a system to scan even text files for bad content
# TODO: Add a system that uses VirusTotal to scan URLs
# TODO: Check into using latest version of Wavelink

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

    # On bot ready...
    async def on_ready(self) -> None:
        # Print a message to the console and log ready event
        logandprint.info(f'''
------------------------------
{self.user.name} is online and ready.
Bot ID: {self.user.id}
Custom Status: "{custom_status}"
------------------------------
''')

        # Change the bots' status
        await self.change_presence(status=discord.Status.online, activity=discord.CustomActivity(custom_status))

    # Create setup hook for Wavelink music player
    async def setup_hook(self) -> None:
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password=WAVELINK_PASSWORD)
        await wavelink.NodePool.connect(client=self, nodes=[node])

    # Add a handler for anyone trying to use old command system
    async def on_command_error(self, ctx, error) -> None:
        message = ('I don\'t support regular bot commands. Instead, I use Discord\'s built-in app commands! Use '
                   '`/help` for a list of available commands.')
        return await ctx.send(message)


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
            logandprint.info(f'User {interaction.user.name} was unable to run command "{interaction.command.name}" due to insufficient permissions.')
            return await interaction.response.send_message('You don\'t have permission to use this command.', ephemeral=True)

        if isinstance(error, app_commands.CommandOnCooldown):
            logandprint.info(f'User {interaction.user.name} was unable to run command "{interaction.command.name}" because it\'s'
                  ' on cooldown.')
            return await interaction.response.send_message('This command is on cooldown!', ephemeral=True)

        # Handler for failing to respond to an interaction quickly enough
        if isinstance(error, discord.app_commands.CommandInvokeError):
            return logandprint.warning(f'Failed to respond to command "{interaction.command.name}" run by'
                         f'{interaction.user.display_name} because the interaction timed out.')

        # So far no other handlers are required, because AppCommands automatically requires correct argument types
        #  and "CommandNotFound" errors are (to my knowledge) impossible with slash commands.

        # General error handler
        else:
            # Defining the error message as a variable for optimization
            logandprint.error(f'An error occurred when the user {interaction.user.display_name} tried to run the command'
                              f' {interaction.command.name}: "{type(error)}: {error}"')
            return await interaction.response.send_message(
                f'An error occurred when trying to run that command:\n```{error}```', ephemeral=True)

    # Load extensions and start bot, all in time with the bot itself
    async with bot:
        await loadExtensions(bot)
        await bot.start(BOT_TOKEN)

# Start the bot
if __name__ == "__main__":
    # Put bot in a try/except for error handling
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logandprint.info('Shutting down!')
    except Exception as e:
        logandprint.fatal(f'B.O.B encountered a critical error and had to shut down! Error: {e}')
