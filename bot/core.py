# Imports
import discord
from discord.ext import commands
from pretty_help import PrettyHelp, EmojiMenu
from utils.intents import defIntents


# NEED TO DO! Add config loader, add logging functionality

# Variables
#menu = EmojiMenu(active_time=60)  # PrettyHelp menu
bot = commands.Bot(command_prefix='!', owner_id='403735483961704450', intents=defIntents(), help_command=PrettyHelp(
    color=discord.Color.from_rgb(1, 162, 186),
    index_title='B.O.B Help Menu',
    #menu=menu,
    no_category='Miscellaneous Commands',
    thumbnail_url='https://cdn.discordapp.com/avatars/1154825794963640390/ff31b0d57ab76713dba89da69a16fe35.webp?size=4096&width=913&height=913'
))
custom_status = 'Use "!help" for help.'


async def botSetup(bot):
    # Print online message upon connection and set custom status
    @bot.event
    async def on_ready():
        print(f'''------------------------------
{bot.user.name} is online and ready.
Bot ID: {bot.user.id}
Custom Status: "{custom_status}"
------------------------------
''')
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(custom_status))

