# Imports
import os.path
from discord.ext import commands, tasks
import discord
from discord import app_commands
import re
from datetime import datetime
from datetime import timedelta
import json
import os
from dotenv import load_dotenv
from utils.logger import Log, LogAndPrint
from utils.bot_utils import sendMessage, loggingMention, checkIfAdmin, prettyPrintInt
from thefuzz import fuzz
import nltk
import concurrent.futures

### DEBUG
import time
import sys

###


# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()


# Function to load blocked words from file
def loadBlockedWords() -> list:
    with open('data/moderation/blocked_words.txt', 'r') as file:
        lines = file.readlines()
        # ha ha spaghetti code go brrrr
        blocked_words = [line.strip().replace(' ', '').lower() for line in lines]
        file.close()

    return blocked_words


def loadWhitelistedWords() -> list:
    with open('data/moderation/whitelisted_words.txt', 'r') as file:
        lines = file.readlines()
        # ha ha spaghetti code go brrrr
        whitelisted_words = [line.strip().replace(' ', '').lower() for line in lines]
        file.close()

    return whitelisted_words


def exportBlockedWord(word: str) -> int:
    # Get the current list of whitelisted words
    whitelisted_words: list = loadWhitelistedWords()
    blocked_words: list = loadBlockedWords()

    # Stop and return one if the blocked word is already whitelisted
    if word in whitelisted_words:
        return 1

    # Stop and return two if the blocked word is already in the blocklist
    if word in blocked_words:
        return 2

    # Run some cleanup
    del whitelisted_words
    del blocked_words

    # Check and see if a newline characters is needed at the end of the list
    with open('data/moderation/blocked_words.txt', 'rb') as file:
        file.seek(-1, 2)  # Move the cursor to the second-to-last byte of the file
        if file.read(1).decode('utf-8') == '\n':  # Read the last byte as a character
            file_ends_with_newline_char: bool = True
        else:
            file_ends_with_newline_char: bool = False
        file.close()

    # Export the provided word to the blocked words file
    with open('data/moderation/blocked_words.txt', 'a') as file:
        if file_ends_with_newline_char:
            file.write(word)
        else:
            file.write('\n' + word)
        file.close()

    # Return zero if there are no issues
    return 0


def exportWhitelistedWord(word: str) -> int:
    # Get the current list of blocked words
    blocked_words: list = loadBlockedWords()
    whitelisted_words: list = loadWhitelistedWords()

    # Stop and return one if the whitelisted word is already in the blocklist
    if word in blocked_words:
        return 1

    # Stop and return two if the whitelisted word is already in the whitelist
    if word in whitelisted_words:
        return 2

    # Run some cleanup
    del blocked_words
    del whitelisted_words

    with open('data/moderation/whitelisted_words.txt', 'rb') as file:
        file.seek(-1, 2)  # Move the cursor to the second-to-last byte of the file
        if file.read(1).decode('utf-8') == '\n':  # Read the last byte as a character
            file_ends_with_newline_char: bool = True
        else:
            file_ends_with_newline_char: bool = False
        file.close()

    # Export the provided word to the whitelisted words file
    with open('data/moderation/whitelisted_words.txt', 'a') as file:
        if file_ends_with_newline_char:
            file.write(word)
        else:
            file.write('\n' + word)
        file.close()

    # Return if there are no issues
    return 0


# Function to change given word to Leetspeak
def generateLeetspeakVariants(word: str) -> dict:
    # Create a dictionary of all Leetspeak character replacements
    leet_replacements: dict = {
        "a": ["4", "@"],
        "b": ["8"],
        "e": ["3"],
        "f": ["ph"],
        "i": ["1", "|"],
        "l": ["1", "|"],
        "o": ["0", "Ꭴ"],
        "s": ["5", "$"],
        "t": ["7"],
    }

    leetspeak_variants: dict = {}
    current_variants: list = [word]

    for i, char in enumerate(word.lower()):
        replacements: list = leet_replacements.get(char, [char])

        # Generate new variants with and without replacements
        new_variants: list = []
        for variant in current_variants:
            for replacement in replacements + [char]:  # Include original character
                new_variants.append(variant[:i] + replacement + variant[i + 1:])

        # Update current variants for the next iteration
        current_variants = new_variants

    # Add final variants to the dictionary with the original word as the key
    leetspeak_variants[word] = current_variants

    # Some quick redneck engineering to remove duplicates
    temp_set: set = set(leetspeak_variants[word])
    leetspeak_variants[word] = list(temp_set)
    del temp_set

    return leetspeak_variants


# Function to turn a string into a list of words
def tokenize(text: str) -> list:
    # Convert the input to lowercase and remove all characters but letters, numbers, and whitespace
    text: str = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    # Tokenize into words
    tokens = nltk.word_tokenize(text)
    return tokens


# TODO: Add cool-downs to commands to prevent spamming(which may or may not work)
# TODO: Add nuke prevention
# TODO(maybe): Add server lock command
# TODO: Add an AI-powered image detection system that can detect blocked words in an image and NSFW content
# TODO: See if the above system can also work with videos, gifs, and so forth.
# TODO: See if media with audio can be scanned using text-to-speech in order to detect blocked words/phrases.
# TODO: Add a system that will scan user profile pictures using image detection system
# TODO: Add the ability for BOB to run a server-wide scan either upon startup or upon request to scan all user statuses
#  and profile pictures to verify they're not rule-breaking, because if someone updates their profile picture or status
#  while BOB is offline, he won't detect the change and won't check for blocked words/images.
# TODO: Add nickname scanning
# TODO: Add command to remove a word or phrase from the blocklist
# TODO: Make moderation system even smarter by taking into context previous messages to see if user is trying to
#  bypass moderation system by typing blocked word across two messages

class Moderation(commands.GroupCog, description='Commands relating to moderation utilities.'):
    # Define vars
    load_dotenv()
    blocked_words: list = loadBlockedWords()
    whitelisted_words: list = loadWhitelistedWords()
    bot_output_channel: str = os.getenv("BOT_OUTPUT_CHANNEL")

    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

        # Vars
        self.leet_variant_dict: dict = {}
        self.triggering_blocked_word: str = ""
        self.triggering_word: str = ""
        self.image_file_types: set = {".svg", ".ico", ".jpg", ".webp", ".jpeg", ".hdr", ".bmp", ".dds", ".gif", ".cur",
                                      ".psd", ".tiff", ".tga", ".avif", ".rgb", ".xpim", ".heic", ".ppm", ".rgba",
                                      ".exr", ".jfif", ".wbmp", ".pgm", ".xbm", ".jp2", ".pcx", ".jbg", ".heif", ".map",
                                      ".pdb", ".picon", ".pnm", ".jpe", ".jif", ".jps", ".pbm", ".g3", ".yuv", ".pict",
                                      ".ras", ".pal", ".g4", ".pcd", ".sixel", ".rgf", ".sgi", ".six", ".mng", ".jbig",
                                      ".xv", ".xwd", ".fts", ".vips", ".ipl", ".pct", ".hrz", ".pfm", ".pam", ".uyvy",
                                      ".otb", ".mtv", ".viff", ".fax", ".pgx", ".sun", ".palm", ".rgbo", ".jfi"}

    def scanText(self, text_input: str) -> bool:
        """
        A function that scans an input string to see if it contains
        a blocked word or phrase. Returns True if one is found, and
        False if not.

        Example:\n
        if scanText("input text"):
            print("Blocked text found.")

        :param text_input: The text to scan.
        :returns: True, False
        :raises None:
        """

        # Update these vars
        self.triggering_word = ""
        self.triggering_blocked_word = ""

        # Search for blocked words (raw text)
        for blocked_word in self.blocked_words:
            # Convert the message to a list of strings
            for word in tokenize(text_input):
                # If the fuzzy-matching score is higher than 80 and the word is not whitelisted, mark it as blocked
                if fuzz.ratio(word, blocked_word) >= 80 and not (word in self.whitelisted_words):
                    # Update class vars as needed
                    self.triggering_blocked_word = blocked_word
                    self.triggering_word = word
                    return True

        # Search for blocked words (Leetspeak)

        # This function tests the input string against every Leetspeak variant
        # of the blocked words dictionary
        def runScan(string_input: str) -> bool:
            # For every key in the dictionary,
            for blocked_word_key in self.leet_variant_dict:
                # And for every item in the list, which is the key's value
                for leet_variant in self.leet_variant_dict[blocked_word_key]:
                    # If the fuzzy-matching ratio score is higher than 80, mark it as blocked
                    if fuzz.ratio(string_input, leet_variant) >= 80:
                        self.triggering_blocked_word = blocked_word_key
                        self.triggering_word = string_input
                        return True  # Stop after a blocked word is found
            return False

        # The following system splits the task of comparing tokens from the input message or file name to
        # Leetspeak variants of blocked words into multiple threads. This massively speeds up the
        # process, which otherwise would take over 17 seconds for 300+ blocked words using a set, and
        # multiple minutes for the same amount of blocked words and their variants stored in a list.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            tokens: list = tokenize(text_input)
            results: list = list(executor.map(runScan, tokens))

            if True in results and not (self.triggering_word in self.whitelisted_words):
                return True

        # Return false if no blocked words are found in the input
        return False

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logandprint.logCogLoad(self.__class__.__name__)

        # Start background task(s)
        self.checkForNeededUnbans.start()
        logandprint.info('Started background task "Check for Needed Unbans."')

        ## The following two functions are put here and not in __init__ to prevent them from
        ## loading again when the cog is reloaded. (There's no need to reload them.)

        # Download/load needed libraries for word_tokenize()
        punkt_path = os.path.join(os.path.expanduser('~'), 'nltk_data/tokenizers/punkt.zip')
        if not os.path.exists(punkt_path):
            nltk.download("punkt")

        # Pre-cache the Leetspeak variants list
        logandprint.debug("Pre-caching Leetspeak variants of blocked words. (This may take a moment.)")
        for word in self.blocked_words:
            self.leet_variant_dict.update(generateLeetspeakVariants(word))

        logandprint.debug(f"Done! Size of list: {float((sys.getsizeof(self.leet_variant_dict)) / 1048576):.2f} Mb")

        return

    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # DEBUG: Check function performance time
        start_time = time.perf_counter()

        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Prevent scanning of webhooks
        # TODO: Eventually see if there's a way to scan webhooks as well
        if not message.author:
            return

        # Check if message was sent by the bot
        # Using "self.bot.user.id" instead of "is_bot" is an early stage of nuke prevention
        if message.author.id == self.bot.user.id:
            return

        # Vars
        attachment_names: list = []

        # Check if message has any attachments
        if message.attachments:
            # If it does, make a string list of attachment names
            for file in message.attachments:
                attachment_names.append(file.filename)

        # TODO: Add a system for "potentially bad" words or phrases that aren't deleted immediately, but the staff are
        #  notified of the message

        async def handleBlockedPhrase(
                blocked_phrase_is_in_file_name: bool = False,
                blocked_file_name: str = ""
        ) -> None:
            # Get the message content
            original_message_content: str = message.content

            # Delete the message
            await message.delete()

            # If the function is triggered to handle a blocked file name, do the following
            if blocked_phrase_is_in_file_name:
                # Notify staff of the infraction
                await sendMessage(self.bot,
                                  self.bot_output_channel,
                                  f'User {message.author.mention} sent a message that had an attached '
                                  'file with a name containing a blocked word or phrase in channel '
                                  f'{message.channel.mention}.\n\n**The filename:** ||{blocked_file_name}||.\n\n**Triggering'
                                  f' word in blocklist:** ||{self.triggering_blocked_word}||\n\nRemember, if this is'
                                  f' an error, you can add words and phrases to the whitelist using `/moderation'
                                  f' addwhitelistedword <word>`.')

                notify_message: str = (f'{message.author.mention}, you sent a message with an attached file '
                                       'that had a name containing a rule-breaking word or phrase. If this '
                                       'is in error, reach out to the server staff using `/question`.'
                                       f'\n\n**The filename:** `{blocked_file_name}`')

                # If the message had text attached, attach the original message to the notify message, handling
                # message length as needed in the one-line if statement
                if message.content:
                    notify_message = notify_message + '\n\n**Your original message:**\n' + (
                        (message.content[:-200] + '...') if len(message.content) > 1800 else message.content)

                # Notify the message author
                await message.author.send(notify_message)

                log_message: str = (f"User {loggingMention(message.author)} sent a message with an attached file that "
                                    f"had a name containing a blocked word or phrase in channel #\"{message.channel.name}.\""
                                    f" Triggering filename: \"{blocked_file_name}\". Triggering blocked word or "
                                    f"phrase: \"{self.triggering_blocked_word}\"")
            # Otherwise, handle just the text part of the message
            else:
                await sendMessage(
                    self.bot,
                    channel_id=self.bot_output_channel,
                    message=f'User {message.author.mention} sent a message containing one or more blocked words or '
                            f'phrases in channel {message.channel.mention}.\n\n**Original message:**'
                    # What the following spaghetti code does is if the message is more than 1,900 characters,
                    # it cuts off the last 100 characters and appends three dots. If the message is not over
                    # 1,900 characters, it prints the entire message. The || at the start and finish is to
                    # mark the message as a spoiler, meaning the server staff don't have to read the message
                    # if they don't want to. I set it to 100 characters to account for the possible length of
                    # a nickname, since "message.author.mention" is used.
                            f'\n||{(original_message_content[:-200] + "...") if len(original_message_content) > 1800 else original_message_content}||'
                            f'\n\n**The triggering word:** ||{self.triggering_word}||\n\n**Triggering word in blocklist:** ||{self.triggering_blocked_word}||'
                            '\n\nRemember, if this is an error, you can add words and phrases to the whitelist using `/moderation addwhitelistedword <word>`.')

                # Delete the message containing the blocked word, notify the user, and log the offense
                await message.author.send(
                    f"{message.author.mention}, your message contains a rule-breaking word or phrase. If this is in "
                    "error, please reach out to the server staff using `/question`.")
                log_message: str = (f"User {loggingMention(message.author)} sent a message containing a blocked word or"
                                    f" phrase in channel #{message.channel.name}. Triggering word in message: \"{self.triggering_word}.\" Triggering word in blocklist: \"{self.triggering_blocked_word}\"")

            logandprint.warning(log_message, source="d")

            return

        # Remove only whitespace from the message, and convert to lowercase
        message_content: str = re.sub(r"[^\w\s]", "", message.content.lower().replace("_", " ").replace("-", " ").replace(".", " "))
        message_content_with_ints: str = re.sub(r"\W", "", message.content.lower().replace("_", " ").replace("-", " ").replace(".", " "))

        # Scan the message
        if self.scanText(message_content) or self.scanText(message_content_with_ints):
            return await handleBlockedPhrase()

        # And the attachment names as well
        if attachment_names:
            for file_name in attachment_names:
                if self.scanText(file_name):
                    return await handleBlockedPhrase(blocked_phrase_is_in_file_name=True, blocked_file_name=file_name)

        # TODO: Check message attachments here. If there are any, first scan the names using the system above and see
        #  if they contain blocked words. (Delete the message and stop scans if they do.) If they pass, then check if
        #  any of the files are images/media. If they are, run an image scan on them first, even if there are files
        #  needing scanning. If they pass the image scanner, then scan the files, if any, and if possible. (And through
        #  this, the files themselves will be passed to the individual scan functions, if needed. If not needed, the
        #  functions won't be run at all. This should help performance.) Finally, pass the message to the spam
        #  prevention system. This should be the best and most fool-proof system.

        if message.attachments:
            # Second scan: Scan images for bad content (this is the second scan because scanning for blocked words is
            # first)
            image_scanner_cog_instance = self.bot.get_cog('ImageScanner')
            if image_scanner_cog_instance:
                try:
                    result = await image_scanner_cog_instance.scanImage(message=message)
                    # If the media was deemed NSFW,
                    if result:
                        # Delete the message,
                        await message.delete()

                        # Notify the author
                        await message.author.send(f"{message.author.mention}, your message had media attached that was"
                                                  f" deemed NSFW and was therefore removed. If this is in error, please"
                                                  f" reach out to the server staff using `/question`.")

                        # And notify staff
                        await sendMessage(self.bot,
                                          self.bot_output_channel,
                                          f"User {message.author.mention}sent a message with media attached"
                                          " that was deemed NSFW.")

                        # Stop if the message has been deleted; no further scans are needed
                        return

                except Exception as error:
                    await sendMessage(self.bot, self.bot_output_channel,
                                      f"Failed to scan attached media from user {message.author.mention} in"
                                      f" channel #{message.channel.name} with the following error:```{error}```")

            # TODO: Finish the file scanner
            # Third scan: Scan files for viruses
            # file_scanner_cog_instance = self.bot.get_cog('FileScanner')
            # if file_scanner_cog_instance:
            #    if await file_scanner_cog_instance.scanAttachedFiles(message):
            #        ...handle virus

        # TODO: Fix the spam prevention system
        # Fourth scan: Spam prevention
        # spam_prevention_cog_instance = self.bot.get_cog('SpamPrevention')
        # if spam_prevention_cog_instance:
        #    await spam_prevention_cog_instance.checkForSpam(message)

        end_time = time.perf_counter()  # Stop the timer
        elapsed_time = end_time - start_time
        logandprint.debug(f"Total time for message scan: {elapsed_time:.4f} seconds")

        return

    # TODO: Finish the status checking system by adding an auto-kick system after a certain amount of time has passed
    # Listener: On Presence Update
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        # Ignore updates from bots
        if before.bot:
            return

        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check user status to see if it's changed
        if before.activity != after.activity:
            status: str = re.sub(r"[^\w\s]", "",str(after.activity).lower().replace("_", " ").replace("-", " ").replace(".", " "))
            status_with_ints: str = re.sub(r"\W", "",str(after.activity).lower().replace("_", " ").replace("-", " ").replace(".", " "))

            if self.scanText(status) or self.scanText(status_with_ints):
                await after.send(f"{after.mention}, your status contains a rule-breaking word or phrase."
                                 " If this is in error, please reach out to the server staff using `/question`."
                                 " If you do not update your status, you will be kicked or banned from the server.")

                # Notify moderators of the rule-breaking status
                await sendMessage(self.bot, channel_id=self.bot_output_channel,
                                  message=f"User {after.mention} has a status containing a blocked word or phrase."
                                          f"\n\n**Triggering word:** ||{self.triggering_word}||\n\n**Triggering word in"
                                          f" blocklist:** ||{self.triggering_blocked_word}||")

                # Log the offense to console and logfile
                logandprint.warning(f"User {loggingMention(after)} has a status containing a blocked word or phrase. Triggering word: \"{self.triggering_word}.\" Triggering word in blocklist: \"{self.triggering_blocked_word}.\"",
                                    source='d')

            # Stop if no blocked words found
            return

        # Stop if status is unchanged
        return

    # Listener: On Member Update
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        # Ignore updates from bots
        if before.bot:
            return

        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # TODO: Add handling for guild avatar update in this listener

        # Check user nickname to see if it's changed
        if before.nick != after.nick:
            # Create the formatted nickname variables using Regex
            nick: str = re.sub(r"[^\w\s]", "",after.nick.lower().replace("_", " ").replace("-", " ").replace(".", " "))
            nick_with_ints: str = re.sub(r"\W", "",after.nick.lower().replace("_", " ").replace("-", " ").replace(".", " "))

            if self.scanText(nick) or self.scanText(nick_with_ints):
                await after.send(f"{after.mention}, your nickname contains a rule-breaking word or phrase."
                                 " If this is in error, please reach out to the server staff using `/question`."
                                 " If you do not update your nickname, you will be kicked or banned from the server.")

                # Notify moderators of the rule-breaking status
                await sendMessage(self.bot, channel_id=self.bot_output_channel,
                                  message=f"User {after.mention} has a nickname containing a blocked word or phrase."
                                          f"\n\n**Triggering word:** ||{self.triggering_word}||\n\n**Triggering word in"
                                          f" blocklist:** ||{self.triggering_blocked_word}||")

                # Log the offense to console and logfile
                logandprint.warning(f"User {loggingMention(after)} has a nickname containing a blocked word or phrase. Triggering word: \"{self.triggering_word}.\" Triggering word in blocklist: \"{self.triggering_blocked_word}.\"",
                                    source='d')

            # Stop if no blocked words are found
            return

        # Stop if there's no change
        return

    # Listener: On User Update
    @commands.Cog.listener()
    async def on_user_update(self, before: discord.Member, after: discord.Member) -> None:
        # Just putting this listener here for handling username and avatar updates
        return

    # Task: Check for users needing to be unbanned
    @tasks.loop(minutes=2.0)
    async def checkForNeededUnbans(self) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Open and parse data
        with open('data/moderation/unban_times.json', 'r') as file:
            data = json.load(file)

        # Get the current UTC time
        current_time_unformatted = datetime.utcnow()
        current_timestamp = int(current_time_unformatted.timestamp())

        # Get the guild info
        GUILD_ID = int(os.getenv("LONESTAR_GUILD_ID"))
        guild = self.bot.get_guild(GUILD_ID)

        # Iterate through the "temp_banned_users" array and compare times
        for index, entry in enumerate(data.get("temp_banned_users", [])):
            user_id: str = entry.get("user_id")
            time_to_unban: int = entry.get("time_to_unban")

            # Compare the current time with the time in the entry
            if current_timestamp >= time_to_unban:
                # Retrieve the user's ID by username (assuming the username is unique in the guild)
                member: discord.Member = await self.bot.fetch_user(user_id)

                if member:
                    # Try to unban the user
                    message: str = f'User {member.display_name} was unbanned because their temporary ban expired.'

                    try:
                        await guild.unban(member, reason='Temporary ban on user expired.')
                    except discord.NotFound:
                        # If the user can't be unbanned, update the message to log
                        message = (f'{member.display_name}\'s temporary ban expired, but the user could not be '
                                   f'unbanned. This usually means the user has already been unbanned.')

                    # Remove the temp-ban entry from the file, as because it's not needed anymore
                    with open('data/moderation/unban_times.json', 'w') as file:
                        del data['temp_banned_users'][index]
                        json.dump(data, file, indent=2)

                    # Notify that the user has been unbanned
                    await sendMessage(self.bot, self.bot_output_channel, message)

                    # Return with log to console and file
                    return logandprint.info(message, source='d')

                else:
                    # If the user can't be found, log it to Discord, console, and file
                    message = f'User {member.display_name}\'s temporary ban has expired, but the user could not be found to be unbanned.'
                    await sendMessage(self.bot, self.bot_output_channel, message)
                    return logandprint.warning(message, source='d')
            else:
                continue

        return

    # Command: Kick
    @app_commands.command(name='kick', description='Kick a user from the server. Syntax: "/kick <user>"')
    @app_commands.describe(member='The member to kick.')
    @app_commands.describe(reason='The reason why the member is to be kicked. (Optional.)')
    @discord.app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, *,
                   reason: str = "No reason was provided.") -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        try:
            # Kick the user and log it to #bot-output and to file
            await interaction.response.send_message(f'User {member.display_name} has been kicked from the server.',
                                                    ephemeral=True)
            message: str = f'{member.display_name} has been kicked from the server. Reason: "{reason}"'
            await member.kick(reason=reason)
            await sendMessage(self.bot, self.bot_output_channel, message)

            return log.info(message, source='d')
        except discord.Forbidden:
            await interaction.response.send_message('You don\'t have permission to use this command.', ephemeral=True)

            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f'An error occurred trying to kick user {member}: {e}',
                                                    ephemeral=True)

            return

    # Command: Ban
    @app_commands.command(name='ban', description='Ban a user from the server. Syntax: "/ban <user> [reason]"')
    @app_commands.describe(member='The member to ban.')
    @app_commands.describe(reason='The reason why the member is to be banned. (Optional.)')
    @app_commands.checks.has_permissions(kick_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, *,
                  reason: str = 'No reason was provided.') -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        try:
            # Ban the user and log it to #bot-output and to file
            message = f'{member.display_name}(ID: {member.id}) has been banned from the server. Reason: "{reason}"'
            await member.ban(reason=reason)
            await sendMessage(self.bot, self.bot_output_channel, message)
            await interaction.response.send_message(f'User `{member.display_name}` was banned from the server.',
                                                    ephemeral=True)
            return logandprint.info(message, source='d')
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f'The following error occurred when trying to ban member {member.mention}: ```{e}```', ephemeral=True)

            return logandprint.error(f'The following error occurred when trying to ban member {member.mention}: {e}',
                                     source='d')

    # Command: TempBan
    @app_commands.command(name='tempban', description=
    'Temporarily ban a user from the server. Syntax: "/tempban <user> <duration in minutes> [reason]"')
    @app_commands.describe(member='The member to temporarily ban.')
    @app_commands.describe(duration='The duration in minutes to ban the member.')
    @app_commands.describe(reason='The reason why the member is to be banned. (Optional.)')
    @app_commands.checks.has_permissions(ban_members=True)
    async def tempban(self, interaction: discord.Interaction, member: discord.Member, duration: int, *,
                      reason: str = "") -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Get the current time in UTC, get the time that it will be to unban the user, and format it to a string
        current_time = datetime.utcnow()
        future_time = current_time + timedelta(minutes=duration)
        unban_timestamp: int = int(future_time.timestamp())
        unban_time: str = future_time.strftime("%Y-%m-%d %H:%M")

        # Create the dictionary entry
        temp_banned_user: dict = {'user_id': f'{member.id}', 'time_to_unban': unban_timestamp}

        # Create the reason (if needed)
        if not reason:
            reason = f"You have been temporarily banned from the server. You will be unbanned on <t:{unban_timestamp}:f> UTC."

        # Now log that, along with the temp-banned user to a file (and create the file if it doesn't exist)
        if not os.path.exists('data/unban_times.json'):
            with open('data/moderation/unban_times.json', 'w') as file:
                empty_data = {"temp_banned_users": []}
                json.dump(empty_data, file, indent=2)

        with open('data/moderation/unban_times.json', 'r') as file:
            existing_temp_bans = json.load(file)
            existing_temp_bans['temp_banned_users'].append(temp_banned_user)

        with open('data/moderation/unban_times.json', 'w') as file:
            json.dump(existing_temp_bans, file, indent=2)

        # Ban the user
        try:
            await member.ban(reason=reason)
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                f'The following error occurred when trying to temporarily ban member {member.mention}: ```{e}```',
                ephemeral=True)

        # Now log the temp ban in the #bot-output channel, and to file (probably more optimizing could be done here)
        await sendMessage(self.bot, self.bot_output_channel,
                          f'{member.mention}(ID: `{member.id}`) has been temporarily banned till <t:{unban_timestamp}:f> UTC. Reason: "{reason}".')
        await interaction.response.send_message(
            f'{member.mention} was temporarily banned. See <#{self.bot_output_channel}> for more info.', ephemeral=True)
        return logandprint.info(
            f'{member.name}(ID: {member.id}) has been temporarily banned till {unban_time} UTC. Reason: "{reason}".',
            source='d')

    # Command: Unban
    @app_commands.command(name='unban', description='Unbans a user. Syntax: "/unban <user ID>"')
    @app_commands.describe(user_id='The ID of the user to unban.')
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check if user ID is all numbers, and is equal to 18 characters
        message = f'`{user_id}` is an invalid user ID. User IDs are a string of 18 digits.'
        if not user_id.isdigit():
            return await interaction.response.send_message(message, ephemeral=True)

        if len(user_id) != 18:
            return await interaction.response.send_message(message, ephemeral=True)

        # Create a list of every ban for the guild (slow, might need to find better system)
        bans = [entry async for entry in interaction.guild.bans()]

        # Loop through the list to see if the user in question is in it
        for entry in bans:
            if entry.user.id == int(user_id):
                # Unban the user
                await interaction.guild.unban(entry.user)

                # Notify that the user has been unbanned
                message = f'{entry.user.mention}(ID: `{entry.user.id}`) has been unbanned by {interaction.user.mention}.'
                await sendMessage(self.bot, self.bot_output_channel, message)
                await interaction.response.send_message(f'Unbanned user {entry.user.display_name}.', ephemeral=True)
                return logandprint.info(message)

        # Notify that the user is not banned.
        await interaction.response.send_message('That user has not been banned.', ephemeral=True)
        return logandprint.info(f'{interaction.user} attempted to unban user with ID "{user_id}."')

    # Command: Purge
    @app_commands.command(name='purge', description='Delete a specified number of messages. (Limit 100.)')
    @app_commands.describe(amount='The amount of messages to be deleted.')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check if the specified amount is within the allowed range
        if 1 <= amount <= 100:
            logMessage = f'User {interaction.user} purged {amount} message(s) from channel "{interaction.channel}."'
            # Delete the specified number of messages (including the command message)
            deleted = await interaction.channel.purge(limit=amount)
            # Send a notifying message, then delete it after three seconds.
            if amount == 1:
                # Make the message pretty if it's only one message to delete
                await interaction.response.send_message('Deleted the last sent message.', ephemeral=True)
                logandprint.info(logMessage)
            else:
                await interaction.response.send_message(f'Deleted the last {len(deleted) - 1} messages.',
                                                        ephemeral=True)
                logandprint.info(logMessage)
        else:
            # Log the attempted usage of the command
            logMessage = f'User {interaction.user} attempted to purge {amount} message(s) from channel "{interaction.channel}."'
            if amount < 1:
                await interaction.response.send_message('The amount must be at least one.', ephemeral=True)
                logandprint.info(logMessage)
            elif amount > 100:
                await interaction.response.send_message("The amount must be under 100.", ephemeral=True)
                logandprint.info(logMessage)
            return

    # Command: ReloadBlockedWords
    @app_commands.command(name='reloadblockedwords',
                          description='Reload the list of blocked words. (Only usable by staff.)')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def reloadBlockedWords(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check is the user is an admin or greater
        if not checkIfAdmin(interaction):
            return interaction.response.send_message("You have to be an administrator or greater to use this command!",
                                                     ephemeral=True)

        try:
            # Reload the blocked words list
            self.blocked_words = loadBlockedWords()

            # Notify of the success
            await interaction.response.send_message("Reloaded blocked words list. Updating pre-cache of Leetspeak"
                                                    " variants. (This may take a moment depending on the size of the"
                                                    " blocked words list.)", ephemeral=True)

            # Update Leetspeak variants pre-cache
            logandprint.debug("Updating pre-cache of Leetspeak variants of blocked words. (This may take a moment.)")
            for word in self.blocked_words:
                self.leet_variant_dict.update(generateLeetspeakVariants(word))
            logandprint.debug("Done!")

            # Get the total amount of blocked word Leetspeak variants
            total_length: str = prettyPrintInt(int(sum(len(lst) for lst in self.leet_variant_dict.values())))

            # Update notification
            await interaction.edit_original_response(
                content=f"Done! Loaded a total of {prettyPrintInt(len(self.blocked_words))} blocked words list and "
                        f"cached {total_length} Leetspeak variants.")

            # Log the reload
            return logandprint.info(f'User {loggingMention(interaction.user)} reloaded blocked words list.', source='d')
        except Exception as e:
            await interaction.response.send_message("Failed to reload blocked words list with the following error:"
                                                    f"\n```{e}```", ephemeral=True)
            return logandprint.error(f"Failed to reload blocked words list with the following error: {e}", source='d')

    # Command: ReloadWhitelistedWords
    @app_commands.command(name='reloadwhitelistedwords',
                          description='Reload the list of blocked words. (Only usable by staff.)')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def reloadWhitelistedWords(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check is the user is an admin or greater
        if not checkIfAdmin(interaction):
            return interaction.response.send_message(
                "You have to be an administrator or greater to use this command!",
                ephemeral=True)

        try:
            # Reload the whitelisted words list
            self.whitelisted_words = loadWhitelistedWords()

            # Notify of success
            await interaction.response.send_message("Reloaded whitelisted words list successfully.", ephemeral=True)

            # Log the reload
            return logandprint.info(f'User {loggingMention(interaction.user)} reloaded whitelisted words.', source='d')
        except Exception as e:
            await interaction.response.send_message("Failed to reload whitelisted words with the following error:"
                                                    f"\n```{e}```", ephemeral=True)
            return logandprint.error(f"Failed to reload whitelisted words with the following error: {e}",
                                     source='d')

    @app_commands.command(name='addblockedword',
                          description='Add a blocked word or phrase to the blocked words list. (Only usable by administrators.)')
    @app_commands.describe(blocked_word='The word or phrase to add to the blocked words list.')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def addBlockedWord(self, interaction: discord.Interaction, blocked_word: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check if the user is an admin or greater
        if not checkIfAdmin(interaction):
            return interaction.response.send_message("You have to be an administrator or greater to use this command!",
                                                     ephemeral=True)

        return_value: int = exportBlockedWord(blocked_word)

        # If the return value is one, the word is already on the whitelist
        if return_value == 1:
            await interaction.response.send_message(f"Failed to export the word \"{blocked_word}\" to the "
                                                    f"blocked words list because it's already on the whitelisted words list.",
                                                    ephemeral=True)
            return log.error(f"User {loggingMention(interaction.user)} failed to add word "
                             f"\"{blocked_word}\" to the blocked words list because it's already on the whitelist.",
                             source="d")

        # If the return value is two, the word is already on the blocklist
        elif return_value == 2:
            await interaction.response.send_message(f"Failed to export the word \"{blocked_word}\" to the blocked words"
                                                    " list because it's already blocked.", ephemeral=True)
            return log.error(f"User {loggingMention(interaction.user)} failed to add word \"{blocked_word}\" to the"
                             "blocklist because it's already blocked.")

        # Reload blocked words
        self.blocked_words = loadBlockedWords()

        # Notify of success
        await interaction.response.send_message(f'Added ||{blocked_word}|| to blocklist.', ephemeral=True)

        # Log and print the word being added
        log.debug(f"Added word \"{blocked_word}\" to blocked words list.", source='d')
        return logandprint.info(f"User {interaction.user} added word \"{blocked_word}\" to blocked "
                                f"words list.", source='d')

    @app_commands.command(name='addwhitelistedword',
                          description="Adds a whitelisted word or phrase to the whitelist. (Only usable by administrators.)")
    @app_commands.describe(whitelisted_word="The word or phrase to add to the whitelisted words list.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def addWhitelistedWord(self, interaction: discord.Interaction, whitelisted_word: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return
        # Check if the user is an admin or greater
        if not checkIfAdmin(interaction):
            return await interaction.response.send_message("You have to be an administrator or greater to use this command!",
                                                     ephemeral=True)

        return_value: int = exportWhitelistedWord(whitelisted_word)

        # If the return value is one, the word is already on the block list
        if return_value == 1:
            await interaction.response.send_message(f"Failed to export the word \"{whitelisted_word}\" to the "
                                                    f"whitelisted words list because it's already on the blocked words list!",
                                                    ephemeral=True)
            return log.error(f"User {loggingMention(interaction.user)} failed to add word "
                             f"\"{whitelisted_word}\" to the whitelist because it's already on the blocklist.",
                             source="d")

        # If the return value is two, the word is already on the whitelist
        elif return_value == 2:
            await interaction.response.send_message(f"Failed to export the word \"{whitelisted_word}\" to the whitelist"
                                                    " because it's already whitelisted.", ephemeral=True)
            return log.error(f"User {loggingMention(interaction.user)} failed to add word \"{whitelisted_word}\" to the"
                             "whitelist because it's already whitelisted.")

        # Reload whitelisted words
        self.whitelisted_words = loadWhitelistedWords()

        # Notify of success
        await interaction.response.send_message(f'Added \"{whitelisted_word}\" to whitelist.', ephemeral=True)

        # Log and print the word being added
        return logandprint.info(f'User {loggingMention(interaction.user)} added word "{whitelisted_word}" to '
                                'whitelisted words.', source='d')


# Cog setup hook
async def setup(bot):
    await bot.add_cog(Moderation(bot))
