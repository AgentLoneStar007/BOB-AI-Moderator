# Imports
import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import logCommand, log
import vt
from dotenv import load_dotenv
import os
from tqdm import tqdm
import io

# TODO: Instead of setting a hard limit on file sizes or message attachments, I'll instead pull a Google Drive
#  and just warn that the files have not been scanned if they're too large
# TODO: Don't forget to add a system that cleans the download folder after the files are deemed safe and re-uploaded
# TODO: See if I need to download differing files from different messages to different sub-directories of the download
#  folder in order to prevent naming conflicts

# Vars
load_dotenv()
VIRUS_TOTAL_API_KEY = os.getenv("VIRUS_TOTAL_API_KEY")


class FileScanning(commands.Cog, description="Example cog description."):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.client = vt.Client(VIRUS_TOTAL_API_KEY)
        return

    # Vars
    # TODO: RE-ADD .TXT TO THIS LIST (I removed it for testing purposes)
    ingnorable_file_extensions: list = ['.jpg', '.png', '.jpeg', '.mp4', '.mp3', '.webm', '.gif', '.ico', '.bmp', '.tiff', '.ttf', '.otf', '.csv', '.xml', '.json', '.docx', '.xlsx', '.pptx']
    uploaded_files: int
    time_since_last_upload: int
    download_directory: str = './downloads/'

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return print(f'Extension loaded: {self.__class__.__name__}')

    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # If the message contains any attachments,
        if message.attachments:
            # Create a list of all files that will need to be downloaded
            message_attachments: list = []

            # There might be a better way to do the following, because this is a loop within a loop, which is probably
            # more performance-intensive than necessary.

            # Run through each attachment,
            for attachment in message.attachments:
                # And check its extension type. If it's in the ignore list, ignore the file
                for x in self.ingnorable_file_extensions:
                    if attachment.filename.endswith(x):
                        continue

                # Add every risky file to a list
                message_attachments.append(attachment)

            # Log the download of the files to console and logfile
            download_log_message: str = f'Downloading {len(message_attachments)} files for scanning...'
            print(download_log_message)
            log('info', download_log_message)

            # For every attachment in the list
            for attachment in message_attachments:
                # Get the file's contents
                file_content: bytes = await attachment.read()
                # Set the download directory
                filename = f'{self.download_directory}{attachment.filename}'
                # Get the file's data
                file_stream: io.BytesIO = io.BytesIO(file_content)
                # Get the file's total size, in bytes
                total_size = len(file_content)

                # Download the file, showing a progress bar
                with tqdm(total=total_size, desc=f"Downloading {attachment.filename}", unit_scale=True) as pbar:
                    # Save the file content to the specified file
                    with open(filename, "wb") as file:
                        for chunk in iter(lambda: file_stream.read(4096), b""):
                            file.write(chunk)
                            pbar.update(len(chunk))

            # Announce downloaded files in console and log it to file
            log_message = f'Downloaded {len(message_attachments)} files for scanning from message by user "{message.author.name}" in channel {message.channel.name}.'
            print(log_message)
            log('info', log_message)

            # Delete the message
            await message.delete()

            # And notify the sender of file scanning
            await message.channel.send(f'{message.author.mention}, your files have been downloaded and are now being '
                                       f'scanned for viruses. I will re-upload them upon completion of the scan and '
                                       f'verification from VirusTotal that they are safe.')

            # TODO: Build the actual file scanner

        return


async def setup(bot):
    await bot.add_cog(FileScanning(bot))
