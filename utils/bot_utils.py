# Imports
import discord
from dotenv import load_dotenv
import os

# Load vars
load_dotenv()
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))


# Send message in channel function
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


# Custom owner check function for app commands
async def checkIfOwner(interaction: discord.Interaction):
    if not interaction.user.id == OWNER_ID:
        await interaction.response.send_message('Only the owner can use this command.', ephemeral=True)
        return False
    return True

