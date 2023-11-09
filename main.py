# Imports
# from bot.core import bot, botSetup
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
from utils.logger import log, logsInit
from utils.bot_utils import defIntents

# Vars
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
WAVELINK_PASSWORD = os.getenv("WAVELINK_PASSWORD")
custom_status = 'Use "/help" for help.'


class Bot(commands.Bot):
    # Init log system
    logsInit()

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
                no_category='Not Categorized',
                thumbnail_url='https://cdn.discordapp.com/avatars/1154825794963640390/ff31b0d57ab76713dba89da69a16fe35.webp?size=4096&width=913&height=913',
                menu=pretty_help.AppMenu(ephemeral=True)

            ))

    # On bot ready...
    async def on_ready(self) -> None:
        # Print a message to the console
        print(f'''
------------------------------
{self.user.name} is online and ready.
Bot ID: {self.user.id}
Custom Status: "{custom_status}"
------------------------------
''')
        # Log ready event
        log('info', f'{self.user.name} online and ready.')

        # Change the bots' status
        await self.change_presence(status=discord.Status.online, activity=discord.CustomActivity(custom_status))

    # Create setup hook for Wavelink music player
    async def setup_hook(self) -> None:
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password=WAVELINK_PASSWORD)
        await wavelink.NodePool.connect(client=self, nodes=[node])

    # Add a handler for anyone trying to use old command system
    async def on_command_error(self, ctx, error):
        message = ('I no longer support regular bot commands. Instead, I use Discord\'s built-in app commands! Use '
                   '`/help` for a list of available commands.')
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(message, ephemeral=True)
        else:
            await ctx.send(message, ephemeral=True)


async def run() -> None:
    # Create the bot from the Bot class
    bot = Bot()

    # Add some error handling for slash commands. I'm putting this down here, and not in the Bot class, because I need
    #  to use the "bot" variable, but I'm not smart enough to access the bot variable inside the class.
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        # Handler for missing permissions
        if isinstance(error, app_commands.MissingPermissions):
            print(f'User {interaction.user.display_name} was unable to run command "{interaction.command.name}" due to insufficient permissions.')
            return await interaction.response.send_message('You don\'t have permission to use this command.', ephemeral=True)
        # So far no other handlers are required, because AppCommands automatically requires correct argument types
        #  and "CommandNotFound" errors are (to my knowledge) impossible with slash commands.

        # General error handler
        else:
            # Defining the error message as a variable for optimization
            error_message = f'An error occurred when the user {interaction.user.display_name} tried to run the command {interaction.command.name}: "{type(error)}: {error}"'
            print(error_message)
            await interaction.response.send_message(
                f'An error occurred when trying to run that command:\n```{error}```', ephemeral=True)
            return log('error', error_message)

    # Load extensions and start bot, all in time with the bot itself
    async with bot:
        await loadExtensions(bot)
        await bot.start(BOT_TOKEN)

# Run the bot
if __name__ == "__main__":
    asyncio.run(run())
