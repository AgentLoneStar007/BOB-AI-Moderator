import discord


def defIntents():
    intents = discord.Intents.default()
    intents.typing = False  # Disable the typing event
    intents.dm_messages = True
    intents.messages = True
    intents.message_content = True

    return intents
