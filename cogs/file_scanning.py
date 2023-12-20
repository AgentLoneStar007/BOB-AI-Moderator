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

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return print(f'Extension loaded: {self.__class__.__name__}')

    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Check if message was sent by the bot
        if message.author.id == self.bot.user.id:
            return

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
                # Set the download directory, which is the download directory, plus the
                download_directory = f'./downloads/{str(message.id)}'
                os.mkdir(download_directory)
                filename = f'{download_directory}/{attachment.filename}'
                # Get the file's data
                file_stream: io.BytesIO = io.BytesIO(file_content)
                # Get the file's total size, in bytes
                total_size = len(file_content)

                # Download the file, showing a progress bar
                with tqdm(total=total_size, desc=f"Downloading {attachment.filename}", unit_scale=True) as progress_bar:
                    # Save the file content to the specified file
                    with open(filename, "wb") as file:
                        for chunk in iter(lambda: file_stream.read(4096), b""):
                            file.write(chunk)
                            progress_bar.update(len(chunk))

            # Announce downloaded files in console and log it to file
            log_message = f'Downloaded {len(message_attachments)} files for scanning from message by user "{message.author.name}" in channel {message.channel.name}.'
            print(log_message)
            log('info', log_message)

            # Get the text content of the message. If there's no text, set message_text to equal None
            message_text: str = message.content if message.content else None

            # And notify the sender of file scanning
            notify_message: str = (f'{message.author.mention}, your files have been downloaded and are now being '
                                   f'scanned for viruses. I will re-upload them upon completion of the scan and '
                                   f'verification from VirusTotal that they are safe.')

            # If there was text attached to the original message, attach it to the notifying message
            if message_text:
                # If the message was greater than 1,800 characters, cut off the last 200 characters(giving wiggle room
                # for the @mention in the notifying message, because the length of the name can't be determined),
                # and put triple-dots at the end. (It probably can be determined; I just don't care.)
                if len(message_text) > 1800:
                    message_text = message_text[:-200] + '...'

                # Update the notify message accordingly
                notify_message = notify_message + f'\n\nOriginal Message:\n{message_text}'

            # Delete the original message
            await message.delete()

            # Send the notifying message in the channel
            await message.channel.send(notify_message)

            # TODO: Build the actual file scanner

        return


async def setup(bot):
    await bot.add_cog(FileScanning(bot))
