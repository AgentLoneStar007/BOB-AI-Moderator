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
