# Imports
import discord
from utils.logger import Log, LogAndPrint
from dotenv import load_dotenv
import os
import sys

# Vars
load_dotenv()
OWNER_ID: int = int(os.getenv("BOT_OWNER_ID"))

# Create object of Log class
log = Log()
logandprint = LogAndPrint()


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


# Send message in channel function (not defining a return type for this function, because it needs to return either a
# message or NoneType. Specifying a return type, then attempting to return None, is illegal and will raise an
# exception.) I need to stop relying on stuff like this, or I'll struggle with non-dynamic languages like C or Rust.
async def sendMessage(bot, channel_id: str, message: str):
    try:
        # Convert the channel ID to an integer
        channel_id: int = int(channel_id)

        # Get the channel using the ID
        channel: discord.TextChannel = bot.get_channel(channel_id)

        if channel is None:
            return logandprint.error(f'Failed to send message to channel ID "{channel_id}." Cannot find channel.', source='d')

        # Send the message to the target channel
        await channel.send(message)

        # Return the message object
        return message
    except ValueError:
        logandprint.error(f'Failed to send message to channel ID "{channel_id}." Invalid ID.', source='d')

        # Return None if there was an error.
        return None


# Custom owner check function for app commands
async def checkIfOwner(interaction: discord.Interaction) -> bool:
    if not interaction.user.id == OWNER_ID:
        await interaction.response.send_message('Only the owner can use this command.', ephemeral=True)
        return False
    return True


# Quick function to print a user's username and ID in console
def loggingMention(member: discord.Member) -> str:
    return f"@{member.display_name}(ID:{member.id})"

