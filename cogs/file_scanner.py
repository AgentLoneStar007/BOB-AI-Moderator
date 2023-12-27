# Imports
import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import Log, logCogLoad
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

# Create object of Log class to use
log = Log()


class FileScanner(commands.Cog, description="Example cog description."):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.client = vt.Client(VIRUS_TOTAL_API_KEY)
        return

    # Vars
    ingnorable_file_extensions: list = ['.jpg', '.png', '.jpeg', '.mp4', '.mp3', '.avi', '.mkv', '.webm', '.gif', '.ico', '.bmp', '.tiff', '.ttf', '.otf', '.csv', '.xml', '.log', '.json', '.docx', '.xlsx', '.pptx']
    unscannable_file_extensions: list = ['.iso', '.zip', '.tar', '.gz', '.bz2', '.xz', '.rar', '.7z', '.tgz', '.tbz2', '.cab', '.zipx', '.img', '.gz']
    uploaded_files: int
    time_since_last_upload: int

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logCogLoad(self.__class__.__name__)
        return print(f'Extension loaded: {self.__class__.__name__}')

    # File scanner function
    async def scanAttachedFiles(self, message: discord.Message) -> None:
        # Check if message was sent by the bot
        if message.author.id == self.bot.user.id:
            return

        # If the message contains any attachments,
        if message.attachments:
            # Create a list of all files that will need to be downloaded
            message_attachments: list = []
            # And create a list of all files that cannot be scanned
            unscannable_message_attachments: list = []

            # There might be a better way to do the following, because these are loops within a loop, which is probably
            # more performance-intensive than necessary.

            # Run through each attachment,
            for attachment in message.attachments:
                # Since running "continue" in one of the sub for-loops doesn't work, I have to do this
                should_continue: bool = False

                # And check its extension type. If it's in the ignore list, ignore the file
                for x in self.ingnorable_file_extensions:
                    if attachment.filename.endswith(x):
                        should_continue = True

                # Also check for any files with an un-scan-able extension type, and add the filenames to a list
                for x in self.unscannable_file_extensions:
                    if attachment.filename.endswith(x):
                        unscannable_message_attachments.append(attachment.filename)
                        should_continue = True

                # If the should_continue var is True, continue
                if should_continue:
                    continue

                # Add the file to the message_attachments list for later
                message_attachments.append(attachment)

            # If both lists are empty, all attachments are ignored file extensions
            if not message_attachments and not unscannable_message_attachments:
                return

            # If there are no scan-able message attachments, notify users that the files cannot be verified
            if not message_attachments:
                await message.reply(content='I cannot scan some or all of the attached files, so I cannot verify if'
                                            ' they are safe or not. Download at your own risk.')
                return

            # Log the download of the files to console and logfile
            download_log_message: str = f'Downloading {len(message_attachments)} files for scanning...'
            print(download_log_message)
            log.info(download_log_message)

            # For every attachment in the list
            for attachment in message_attachments:
                # Get the file's contents
                file_content: bytes = await attachment.read()
                # Set the download directory, which is the download directory, then the message ID as the directory name
                download_directory = f'./downloads/{str(message.id)}'
                os.mkdir(download_directory)
                filename = f'{download_directory}/{attachment.filename}'
                # Get the file's data
                file_stream: io.BytesIO = io.BytesIO(file_content)
                # Get the file's total size, in bytes
                total_size = len(file_content)

                # Download the file, showing a progress bar(which may or may not work)
                with tqdm(total=total_size, desc=f"Downloading {attachment.filename}", unit_scale=True) as progress_bar:
                    # Save the file content to the specified file
                    with open(filename, "wb") as file:
                        for chunk in iter(lambda: file_stream.read(4096), b""):
                            file.write(chunk)
                            progress_bar.update(len(chunk))

            # Announce downloaded files in console and log it to file
            log_message = f'Downloaded {len(message_attachments)} files for scanning from message by user "{message.author.name}" in channel {message.channel.name}.'
            print(log_message)
            log.info(log_message)

            # Get the text content of the message. If there's no text, set message_text to equal None
            message_text: str = message.content if message.content else None

            # And notify the sender of file scanning
            notify_message: str = (f'{message.author.mention}, your files have been downloaded and are now being '
                                   f'scanned for viruses. I will re-upload them upon completion of the scan and '
                                   f'verification from VirusTotal that they are safe.')

            # If there's any items in the unscannable files list, append them and a message to the notifying message
            if len(unscannable_message_attachments) > 0:
                # Apparently Python 3.11 doesn't allow backslash characters inside f-strings, so I have to do this
                newline_char: str = '\n'
                # Add to the notifying message, and use join() to print every item in the unscannable files list
                notify_message = notify_message + (f'\n\nThe following files are unscannable and will be skipped. I '
                                                   f'cannot verify if they are safe.\n```{f"{newline_char}".join(unscannable_message_attachments)}```')
                del newline_char

            # If there was text attached to the original message, attach it to the notifying message
            if message_text:
                # If the message was greater than 1,800 characters, cut off the last 200 characters(giving wiggle room
                # for the @mention in the notifying message, because the length of the name can't be determined),
                # and put triple-dots at the end. (It probably can be determined; I just don't care.)
                if len(message_text) > 1700:
                    message_text = message_text[:-300] + '...'

                # Update the notify message accordingly
                notify_message = notify_message + f'\n\n**Original Message:**\n{message_text}'

            # Delete the original message
            await message.delete()

            # Send the notifying message in the channel
            await message.channel.send(notify_message)

            # TODO: Build the actual file scanner

        return


async def setup(bot) -> None:
    return await bot.add_cog(FileScanner(bot))
