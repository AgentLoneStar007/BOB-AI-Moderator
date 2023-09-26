# Imports
import discord
from discord.ext import commands


async def sendMessage(bot, ctx, channel_id: str, message: str):
    try:
        # Convert the channel ID to an int
        channel_id = int(channel_id)

        # Get the channel using the ID
        channel = bot.get_channel(channel_id)

        if channel is None:
            await ctx.send(f'Channel with ID {channel_id} not found.')
            return

        # Send the message to the target channel
        await channel.send(message)
    except ValueError:
        await ctx.send('Invalid channel ID.')


async def lacksPermissions(ctx):
    await ctx.send("You don't have permission to use this command.")


async def errorOccurred(ctx, error):
    print(f'The following error occurred when trying to run a command: "`{error}`"')
    await ctx.send(f'The following error occurred when trying to run that command: "`{error}`"')

