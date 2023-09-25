import discord
from discord.ext import commands
from bot.core import bot, botSetup
from dotenv import load_dotenv
import os

# Load vars
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Create an instance of the bot

# Run the bot
if __name__ == "__main__":
    botSetup(bot)  # Call a setup function from core.py to initialize event handlers and commands
    bot.run(BOT_TOKEN)
