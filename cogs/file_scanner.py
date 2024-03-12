# Imports
import discord
from discord.ext import commands, tasks
from utils.logger import Log, LogAndPrint
from utils.bot_utils import loggingMention
import vt
from dotenv import load_dotenv
import os
import hashlib

# TODO: Instead of setting a hard limit on file sizes or message attachments, I'll instead pull a Google Drive
#  and just warn that the files have not been scanned if they're too large
# TODO: Don't forget to add a system that cleans the download folder after the files are deemed safe and re-uploaded
# TODO: Add a system that stores the totals of how many files have been scanned per minute, day, month, etc. in order
#  to prevent exceeding the free API limits. Also make that system reset those counts when needed.

# Vars
load_dotenv()
VIRUS_TOTAL_API_KEY: str = os.getenv("VIRUS_TOTAL_API_KEY")

# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()


# Function to compute the SHA-256 of a file
def computeSHA256(file_path) -> str:
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        # Read the file in chunks to handle large files
        for chunk in iter(lambda: file.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


class FileScanner(commands.Cog, description="Everything relating to the file scanner."):
    def __init__(self, bot) -> None:
        self.bot = bot

        # TODO: Make sure the ignorable_file_extensions list lines up with the list that will be in the image scanner to
        #  prevent duplicate scans or skipped files being scanned

        # Vars
        # TODO: Re-add .txt to this list
        self.total_request: int = 0
        self.requests_this_minute: int = 0
        self.ingnorable_file_extensions: list = [".svg", ".ico", ".jpg", ".webp", ".jpeg", ".hdr", ".bmp", ".dds",
                                                 ".gif", ".cur", ".psd", ".tiff", ".tga", ".avif", ".rgb", ".xpim",
                                                 ".heic", ".ppm", ".rgba", ".exr", ".jfif", ".wbmp", ".pgm", ".xbm",
                                                 ".jp2", ".pcx", ".jbg", ".heif", ".map", ".pdb", ".picon", ".pnm",
                                                 ".jpe", ".jif", ".jps", ".pbm", ".g3", ".yuv", ".pict", ".ras", ".pal",
                                                 ".g4", ".pcd", ".sixel", ".rgf", ".sgi", ".six", ".mng", ".jbig",
                                                 ".xv", ".xwd", ".fts", ".vips", ".ipl", ".pct", ".hrz", ".pfm", ".pam",
                                                 ".uyvy", ".otb", ".mtv", ".viff", ".fax", ".pgx", ".sun", ".palm",
                                                 ".rgbo", ".jfi", ".png", ".ttf", ".otf", ".csv", ".xml", ".log",
                                                 ".json", ".docx", ".xlsx", ".pptx"]
        self.unscannable_file_extensions: list = [".iso", ".zip", ".tar", ".gz", ".bz2", ".xz", ".rar", ".7z", ".tgz",
                                                  ".tbz2", ".cab", ".zipx", ".img"]

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return logandprint.logCogLoad(self.__class__.__name__)

    # Task: Reset Requests
    @tasks.loop(hours=24.0)
    async def resetDailyRequests(self) -> None:
        # TODO: Build reset function
        return

    # Task: Reset Requests
    @tasks.loop(minutes=1.0)
    async def resetMinutelyRequest(self) -> None:
        # TODO: Build reset function
        return

    # Task: Clean Download Folder
    @tasks.loop(minutes=5.0)
    async def cleanDownloadFolder(self) -> None:
        # TODO: Build downloads cleaner function
        return

    # File scanner function
    async def scanAttachedFiles(self, message: discord.Message) -> bool:
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
                    break

            # Also check for any files with an un-scan-able extension type, and add the filenames to a list
            for x in self.unscannable_file_extensions:
                if attachment.filename.endswith(x):
                    unscannable_message_attachments.append(attachment.filename)
                    should_continue = True
                    break

            # If the should_continue var is True, continue
            if should_continue:
                continue

            # Add the file to the message_attachments list for later
            message_attachments.append(attachment)

        # If both lists are empty, all attachments are ignored file extensions
        if not message_attachments and not unscannable_message_attachments:
            return False

        # If there are no scan-able message attachments, notify users that the files cannot be verified
        if not message_attachments:
            await message.reply(content="I cannot scan some or all of the attached files, so I cannot verify if"
                                        " they are safe or not. Download at your own risk.")
            return False

        # Log the download of the files to console and logfile
        logandprint.info(f"Downloading {len(message_attachments)} files for scanning...", source='d')

        # Create a count variable
        current_file_index: int = 0

        # Create download directory variable, to prevent issues
        download_directory: str = ""

        # For every attachment in the list,
        for attachment in message_attachments:
            # Get the file's contents
            file_content: bytes = await attachment.read()
            # Set the download directory, which is the download directory, then the message ID as the subdirectory name
            download_directory = f"downloads/{str(message.id)}"
            os.mkdir(download_directory)
            file_path = f"{download_directory}/{attachment.filename}"

            # Download the file
            with open(file_path, "wb") as file:
                file.write(file_content)

            # Increment the count by one
            current_file_index += 1

            logandprint.debug(f"Finished download of file {current_file_index} of {len(message_attachments)}.")

        # Announce downloaded files in console and log it to file
        logandprint.info(f"Finished downloading {len(message_attachments)} files for scanning from a message "
                         f"sent by the user \"{loggingMention(message.author)}\" in channel #{message.channel.name}.",
                         source='d')

        # And notify the sender of file scanning
        notify_message: str = (f"{message.author.mention}, your files have been downloaded and are now being "
                               "scanned for viruses.")

        # If there's any items in the unscannable files list, append them and a message to the notifying message
        if len(unscannable_message_attachments) > 0:
            # Apparently Python 3.11+ doesn't allow backslash characters inside f-strings, so I have to do this
            newline_char: str = '\n'
            # Add to the notifying message, and use join() to print every item in the unscannable files list
            notify_message = notify_message + ("\n\nThe following files are unscannable and will be skipped. I "
                                               "cannot verify if they are safe.\n```"
                                               f"{newline_char.join(unscannable_message_attachments)}```")

            # Cleanup
            del newline_char

        # Send the notifying message in the channel
        await message.reply(content=notify_message)

        # TODO: Build the actual file scanner
        client = vt.Client(VIRUS_TOTAL_API_KEY)

        for download in os.listdir(download_directory):
            file_hash = computeSHA256(f'{download_directory}/{download}')

            try:
                print("good till here")
                file_report = await client.get_object_async(file_hash)
                if file_report is None:
                    print('no reports')
                    break

                print("good till here 2")
                if file_report.attributes.get("last_analysis_stats", {}).get('malicious') > 0:
                    print(f"The file with SHA-256 hash {file_hash} is malicious.")
                else:
                    print(f"The file with SHA-256 hash {file_hash} is not flagged as malicious.")
            except vt.error.APIError as error:
                logandprint.error(f"Error: {error}")
            except Exception as error:
                logandprint.error(f"Error: {error}")

            print('test')

        # Close the client connection, to prevent errors.
        client.close()

        # Hard-setting this to False until the file scanner is complete
        return False


async def setup(bot) -> None:
    return await bot.add_cog(FileScanner(bot))
