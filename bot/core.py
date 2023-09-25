# Imports
import discord
from discord.ext import commands
from utils.intents import defIntents
import os


# Variables
bot = commands.Bot(command_prefix='!', owner_id='403735483961704450', intents=defIntents())
custom_status = 'Use "!help" for help.'


async def botSetup(bot):
    # Print online message upon connection and set custom status
    @bot.event
    async def on_ready():
        print(f'''------------------------------
{bot.user.name} is online and ready.
Bot ID: {bot.user.id}
Status: "{custom_status}"
------------------------------
''')
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(custom_status))

    # Command: Ping
    @bot.command()
    async def ping(ctx):
        await ctx.send('Pong!')

    # Command: Hello
    @bot.command()
    async def hello(ctx):
        await ctx.send(f'Hello, {ctx.author.mention}!')

