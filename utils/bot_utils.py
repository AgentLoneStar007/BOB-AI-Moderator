# Imports
import discord
from discord.ext import commands


async def sendMessage(bot, channel_id: str, message: str):
    try:
        # Convert the channel ID to an int
        channel_id = int(channel_id)

        # Get the channel using the ID
        channel = bot.get_channel(channel_id)

        if channel is None:
            print(f'Failed to send message to channel ID "{channel_id}." Cannot find channel.')
            return

        # Send the message to the target channel
        await channel.send(message)
    except ValueError:
        print(f'Failed to send message to channel ID "{channel_id}." Invalid ID.')


async def errorOccurred(ctx, error):
    print(f'The following error occurred when trying to run a command: "{error}"')
    await ctx.send(f'The following error occurred when trying to run that command: "`{error}`"')

