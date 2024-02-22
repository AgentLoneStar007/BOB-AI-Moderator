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
    """
    Defines the needed intents for the bot, then returns the object.
    :returns: discord.Intents
    """

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
async def sendMessage(bot, channel_id: str, message: str) -> discord.Message:
    """
    Sends a message in a specified channel.

    :param bot: The bot object to use.
    :param channel_id: The ID, in a string data type, of the channel to send a message to.
    :param message: The message to send.
    :returns: discord.Message
    :raises ValueError: Raises ValueError if the channel ID cannot be found or the message cannot be sent.
    """

    try:
        # Convert the channel ID to an integer
        channel_id: int = int(channel_id)

        # Get the channel using the ID
        channel: discord.TextChannel = bot.get_channel(channel_id)

        if channel is None:
            logandprint.error(f"Failed to send message to channel ID \"{channel_id}.\" Cannot find channel.", source='d')
            raise ValueError(f"Failed to send message to channel ID \"{channel_id}.\" Cannot find channel.")

        # Send the message to the target channel
        message_object: discord.Message = await channel.send(message)

        # Return the message object if needed for editing
        return message_object
    except ValueError:
        # The following is mildly redundant code; I'll fix it later
        logandprint.error(f"Failed to send message to channel ID \"{channel_id}.\"", source='d')
        raise ValueError("Failed to send message to channel ID \"{channel_id}.\"")


# Custom owner check function for app commands
async def checkIfOwner(interaction: discord.Interaction) -> bool:
    """
    A custom check function to see if the user of an application command
    is the bots' owner.

    :param interaction: The interaction object for responding to application commands.
    :returns: True(if user is owner); False otherwise
    """

    if not interaction.user.id == OWNER_ID:
        await interaction.response.send_message('Only the owner can use this command.', ephemeral=True)
        return False
    return True


# A function that checks if the user of an app command is an administrator
def checkIfAdmin(interaction: discord.Interaction) -> bool:
    """
    A simple function that checks if a user is an admin.
    Returns True if the user is and admin, and False otherwise.

    :param interaction: The interaction object.
    :returns: True, False
    :raises ValueError: If the target role of "Admin" cannot be found.
    """

    # Get the guild object and target role object
    guild = interaction.user.guild
    target_role = discord.utils.get(guild.roles, name="Admin")

    # Raise an error if the Admin role isn't found.
    if not target_role:
        raise ValueError(f"The \"Admin\" role was not found in the server.")

    # Create a set of all the user's roles
    user_roles = set(interaction.user.roles)

    # Return True if the user has the Admin role or higher; False otherwise
    return any(target_role >= role for role in user_roles)


# Quick function to print a user's username and ID in console
def loggingMention(member: discord.Member) -> str:
    """
    A simple function that returns a pretty-printed string of a
    user's name and ID.

    :param member: The Discord member object.
    :returns: str - A string of the user's name and ID.
    """
    return f"@{member.display_name}(ID:{member.id})"


# Load extension/cog function
async def loadExtensions(bot) -> None:
    """
    A function that loads all extensions in the cogs folder into the bot.

    :param bot: The bot object to load extensions into.
    :return: None
    """

    # For all files in the cogs directory,
    for filename in os.listdir('cogs'):
        # If the file ends with .py,
        if filename.endswith('.py'):
            # Try to load it as a cog
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            # And log it if it fails
            except Exception as e:
                logandprint.error(f'Failed to load cog "{filename[:-3]}" with the following error: {e}')
    return


def prettyPrintInt(integer: int) -> str:
    """
    Formats a given integer to correctly have commas and such.
    Example: input of "1000" outputs "1,000". This function
    can handle negative integers.

    :param integer: The integer to format.
    :returns: str - A formatted string.
    :raises None:
    """

    # If the input is less than 1000 and more than -1,000, just return it as a string
    if 999 >= integer >= -999:
        return str(integer)

    # Format the integer with commas
    formatted_number = '{:,}'.format(integer)

    # Return the formatted number string
    return formatted_number


