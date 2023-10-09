# Imports
import discord


# Define intents the bot needs
def defIntents():
    intents = discord.Intents.default()
    intents.typing = False
    intents.dm_messages = True
    intents.messages = True
    intents.message_content = True
    intents.members = True
    intents.presences = True
    return intents
