import discord
from discord.ext import commands
from utils.intents import defIntents

bot = commands.Bot(command_prefix='`', owner_id='403735483961704450', intents=defIntents())


def botSetup(botData):
    @botData.event
    async def on_ready():
        print(f'''------------------------------
{bot.user.name} is online and ready.
Bot ID: {bot.user.id}
------------------------------
''')

    # Command: Ping
    @botData.command()
    async def ping(ctx):
        await ctx.send('Pong!')

    # Command: Hello
    @botData.command()
    async def hello(ctx):
        await ctx.send(f'Hello, {ctx.author.mention}!')

