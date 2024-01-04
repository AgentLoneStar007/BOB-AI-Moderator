# Imports
import discord
from utils.logger import Log
from dotenv import load_dotenv
import os
import sys

# Vars
load_dotenv()
OWNER_ID: int = int(os.getenv("BOT_OWNER_ID"))

# Create object of Log class
log = Log()


# Define intents the bot needs
def defIntents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.typing = False
    intents.dm_messages = True
    intents.messages = True
    intents.message_content = True
    intents.members = True
    intents.presences = True
    return intents


# Send message in channel function
async def sendMessage(bot, channel_id: str, message: str) -> None:
    try:
        # Convert the channel ID to an int
        channel_id: int = int(channel_id)

        # Get the channel using the ID
        channel = bot.get_channel(channel_id)

        if channel is None:
            return print(f'Failed to send message to channel ID "{channel_id}." Cannot find channel.')

        # Send the message to the target channel
        await channel.send(message)
    except ValueError:
        return print(f'Failed to send message to channel ID "{channel_id}." Invalid ID.')


# Custom owner check function for app commands
async def checkIfOwner(interaction: discord.Interaction) -> bool:
    if not interaction.user.id == OWNER_ID:
        await interaction.response.send_message('Only the owner can use this command.', ephemeral=True)
        return False
    return True

