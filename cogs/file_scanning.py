# Imports
import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import logCommand, log
import vt
from dotenv import load_dotenv
import os

# Vars
load_dotenv()
VIRUS_TOTAL_API_KEY = os.getenv("VIRUS_TOTAL_API_KEY")


class FileScanning(commands.Cog, description="Example cog description."):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.client = vt.Client(VIRUS_TOTAL_API_KEY)
        return

    # Vars
    ingnorable_file_extensions: list = ['.jpg', '.png', '.jpeg', '.mp4', '.mp3', '.webm', '.txt', '.gif', '.ico', '.bmp', '.tiff', '.ttf', '.otf', '.csv', '.xml', '.json', '.docx', '.xlsx', '.pptx']
    uploaded_files: int
    time_since_last_upload: int

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return print(f'Extension loaded: {self.__class__.__name__}')

    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # If the message contains any attachments,
        if message.attachments:
            # There might be a better way to do the following, because this is a loop within a loop, which is probably
            # more performance-intensive than necessary.

            # Run through each attachment,
            for attachment in message.attachments:
                # And check its extension type. If it's in the ignore list, ignore the file
                for x in self.ingnorable_file_extensions:
                    if attachment.filename.endswith(x):
                        continue



        return

    # Example command
    @app_commands.command(name='scan', description='Temp description')
    async def scan(self, interaction: discord.Interaction) -> None:
        return await interaction.response.send_message("This is an example cog!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(FileScanning(bot))
