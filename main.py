# Imports
from bot.core import bot, botSetup
from utils.load_extensions import loadExtensions
from dotenv import load_dotenv
import asyncio
import os

# Vars
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Run the bot
if __name__ == "__main__":
    async def runBot():
        await botSetup(bot)  # Call a setup function from core.py to initialize event handlers and commands
        await loadExtensions(bot)

    asyncio.run(runBot())
    bot.run(BOT_TOKEN)
