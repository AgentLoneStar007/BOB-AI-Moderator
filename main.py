# Imports
# from bot.core import bot, botSetup
import discord
import pretty_help
from discord import app_commands
from discord.ext import commands
from pretty_help import PrettyHelp
import wavelink
from wavelink.ext import spotify
from dotenv import load_dotenv
import asyncio
import os
from utils.load_extensions import loadExtensions
from utils.logger import log, logsInit
from utils.intents import defIntents
from utils.bot_utils import errorOccurred

# Vars
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
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
                no_category='Miscellaneous Commands',
                thumbnail_url='https://cdn.discordapp.com/avatars/1154825794963640390/ff31b0d57ab76713dba89da69a16fe35.webp?size=4096&width=913&height=913',
                menu=pretty_help.AppMenu(ephemeral=True)

))

    # Define on_ready() message
    async def on_ready(self) -> None:
        print(f'''
------------------------------
{self.user.name} is online and ready.
Bot ID: {self.user.id}
Custom Status: "{custom_status}"
------------------------------
''')
        # Log ready event
        log('info', f'{self.user.name} online and ready.')

        # Change bot status
        await self.change_presence(status=discord.Status.online, activity=discord.CustomActivity(custom_status))

    # Create setup hook for Wavelink music player
    async def setup_hook(self) -> None:
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='YouShallNotPass')
        sc: spotify.SpotifyClient = spotify.SpotifyClient(
            client_id='...',
            client_secret='...'
        )
        await wavelink.NodePool.connect(client=self, nodes=[node], spotify=sc)

    # NOT WORKING!
    #async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
    #    if isinstance(error, app_commands.MissingPermissions):
    #        print('amogus')
    #        return await interaction.response.send_message('You don\'t have permission to use this command.', ephemeral=True)
    #    elif isinstance(error, app_commands.CommandNotFound):
    #        print('amogus')
    #        return await interaction.response.send_message('That command doesn\'t exist.', ephemeral=True)
    #    elif isinstance(error, app_commands.Argument):
    #        print('amogus')
    #        return await interaction.response.send_message('The provided arguments are invalid. Check your command arguments '
    #                                                'and its\' proper syntax in the help menu, and try again. '
    #                                                'Use "`/help [command]`" to see a help page regarding the command.',
    #                                                ephemeral=True)
    #    else:
    #        print('amogus')
    #        return await interaction.response.send_message('error testing', ephemeral=True)

    # Add a handler for missing command arguments.
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            # Handler for missing arguments
            await ctx.send('You failed to provide some required arguments. Please try again. '
                           'Use "`/help [command]`" to see a help page related to that command.',)
        elif isinstance(error, commands.MissingPermissions):
            # Handler for missing permissions
            await ctx.send('You don\'t have permission to use this command.')
        elif isinstance(error, commands.CommandNotFound):
            # Handler for a non-existent command
            await ctx.send('That command doesn\'t exist.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('The provided arguments are invalid. Check your command arguments '
                           'and its\' proper syntax in the help menu, and try again. '
                           'Use "`/help [command]`" to see a help page regarding the command.')
        else:
            await errorOccurred(ctx, error)


async def run() -> None:
    bot = Bot()

    async with bot:
        await loadExtensions(bot)
        await bot.start(BOT_TOKEN)

# Run the bot
if __name__ == "__main__":
    asyncio.run(run())
