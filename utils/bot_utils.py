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


# Cleanup function
def cleanup(*args) -> None:
    # Vars
    cleaned_memory_amount: float = 0.0

    # Mark every passed argument for garbage cleanup
    for var in args:
        try:
            # First get the size of the var in bytes
            cleaned_memory_amount += sys.getsizeof(var)

            # Then mark it for deletion
            del var
        # Handle errors as needed
        except Exception as e:
            log.debug(f'Failed to cleanup a variable with the following error: {e}')

    # Round the total amount of cleaned memory to two decimal places
    cleaned_memory_amount = round((cleaned_memory_amount / 1024), 2)

    # Send a message showing how much memory was cleaned.
    log.debug(f'Cleaned {cleaned_memory_amount} Kb of memory.')

    # Delete the cleaned_memory_amount var for even more efficiency
    del cleaned_memory_amount

    return
