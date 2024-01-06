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
from utils.bot_utils import sendMessage

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


# TODO: Add handling if the last item in the blocked words list already has a newline character
def exportBlockedWord(word: str) -> None:
    blocked_words: list = loadBlockedWords()
    with open('data/moderation/blocked_words.txt', 'a') as file:
        file.write('\n' + word)
        file.close()

    return


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

class Moderation(commands.GroupCog, description='Commands relating to moderation utilities.'):
    # Define vars
    load_dotenv()
    blocked_words: list = loadBlockedWords()
    bot_output_channel: str = os.getenv("BOT_OUTPUT_CHANNEL")
    user_message_counts_1: dict = {}
    user_message_counts_2: dict = {}
    user_message_counts_3: dict = {}
    message_reset_interval: int = 30  # in seconds
    message_limit: int = 7  # message limit per reset interval

    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logandprint.logCogLoad(self.__class__.__name__)
        self.checkForNeededUnbans.start()
        return logandprint.info('Started background task "Check for Needed Unbans."')

    # TODO: Add returns in this function as well
    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Check if message was sent by the bot
        # Using "self.bot.user.id" instead of "is_bot" is an early stage of nuke prevention
        if message.author.id == self.bot.user.id:
            return

        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Vars
        attachment_names: list = []

        # Check if message has any attachments
        if message.attachments:
            # If it does, append the file name of each attachment to a list
            for x in message.attachments:
                attachment_names.append(x.filename)

        # Use Regex formatting to search message for blocked words.
        message_content = re.sub(r'[^a-zA-Z0-9]', '', message.content.lower())
        for blocked_word in self.blocked_words:
            if re.search(rf'\b{re.escape(blocked_word)}\b', message_content):
                original_message_content: str = message.content
                await sendMessage(
                    self.bot,
                    channel_id=self.bot_output_channel,
                    message=f'User {message.author.mention} sent a message containing one or more blocked words or '
                            f'phrases in channel {message.channel.mention}.\n\n**Original message:**'
                            # What the following spaghetti code does is, basically, if the message is more than 1,900
                            #  characters, it cuts off the last 100 characters and appends three dots. If the message is
                            #  not over 1,900 characters, it prints the entire message. The || at the start and finish
                            #  is to mark the message as a spoiler, meaning the server staff don't have to read the 
                            #  message if they don't want to. I set it to 100 characters to account for the possible 
                            #  length of a nickname, since "message.author.mention" is used.
                            f'\n||{(original_message_content[:-100] + "...") if len(original_message_content) > 1900 else original_message_content}||')

                # Delete the message containing the blocked word, notify the user, and log the offense
                await message.delete()
                await message.author.send(
                    f"{message.author.mention}, your message contains a rule-breaking word or phrase. If this is in "
                    "error, please reach out to a moderator.")
                logandprint.warning(f'User {message.author} sent a message containing a blocked word or phrase '
                                    f'in channel #{message.channel.name}.', source='d')

                # Stop checking for blocked words after the first word is found
                return

            # Scan each file name as well
            if attachment_names:
                for name in attachment_names:
                    if re.search(rf'\b{re.escape(blocked_word)}\b', name):
                        # Create a variable containing the filename with the blocked word/phrase
                        blocked_name: str = name

                        # Notify staff of the infraction
                        await sendMessage(self.bot,
                                          self.bot_output_channel,
                                          f'User {message.author.mention} sent a message that had an attached '
                                          'file with a name containing a blocked word or phrase in channel '
                                          f'{message.channel.mention}.\n\n**The filename:**||{blocked_name}||.')

                        # Delete the message
                        await message.delete()

                        notify_message: str = (f'{message.author.mention}, you sent a message with an attached file '
                                               'that had a name containing a rule-breaking word or phrase. If this '
                                               'is in error, reach out to the server staff using '
                                               f'`/question`.\n\n**The filename in question: `{blocked_name}`')

                        # If the message had text attached, attach the original message to the notify message, handling
                        # message length as needed in the one-line if statement
                        if message.content:
                            notify_message = notify_message + '\n\n**Your original message:**\n' + ((message_content[:-200] + '...') if len(message.content) > 1800 else message_content)

                        # Notify the message author
                        await message.author.send(notify_message)

                        # Log the infraction
                        logandprint.warning(
                            f'User {message.author.name} sent a message with an attached file that had a name '
                            f'containing a blocked word or phrase in channel "{message.channel.name}."', source='d')

                        # Stop checking
                        return

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
                # If media scanner returns False, media did not pass the scan.
                if not await image_scanner_cog_instance.scanImage(message):
                    return

            # Third scan: Scan files for viruses
            file_scanner_cog_instance = self.bot.get_cog('FileScanner')
            if file_scanner_cog_instance:
                if not await file_scanner_cog_instance.scanAttachedFiles(message):
                    return

        # Fourth scan: Spam prevention
        spam_prevention_cog_instance = self.bot.get_cog('SpamPrevention')
        if spam_prevention_cog_instance:
            await spam_prevention_cog_instance.checkForSpam(message)

        return

    # TODO: Finish the status checking system by adding an auto-kick system after a certain amount of time has passed
    # Listener: On Member Update
    @commands.Cog.listener()
    async def on_presence_update(self, before, after) -> None:
        # Ignore updates from bots
        if before.bot:
            return

        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Check user status to see if it's changed
        if before.activity != after.activity:
            user_status: str = str(after.activity)
            user_status: str = re.sub(r'[^a-zA-Z0-9]', '', user_status.lower())

            for blocked_word in self.blocked_words:
                if re.search(rf'\b{re.escape(blocked_word)}\b', user_status):
                    # Notify the user of their infraction
                    await after.send(f'{after.mention}, your status contains a rule-breaking word or phrase.'
                                     ' If this is in error, please reach out to a moderator using `/question`.'
                                     'If you do not update your status, you will be kicked or banned from the server.')

                    # Notify moderators of the rule-breaking status
                    await sendMessage(self.bot, channel_id=self.bot_output_channel,
                                      message=f'User {after.mention} has a status containing a blocked word or phrase.')

                    # Log the offense to console and logfile
                    logandprint.warning(f'User {after.display_name} has a status containing a blocked word or phrase.',
                                        source='d')

                    # Stop checking for blocked words after the first word is found
                    break

            # Return if no bad words found
            return
        # Return if status is unchanged
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
            await interaction.response.send_message(f'The following error occurred when trying to ban member {member.mention}: ```{e}```', ephemeral=True)

            return logandprint.error(f'The following error occurred when trying to ban member {member.mention}: {e}')

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
        unban_timestamp = int(future_time.timestamp())
        unban_time = future_time.strftime("%Y-%m-%d %H:%M")

        # Create the dictionary entry
        temp_banned_user = {'user_id': f'{member.id}', 'time_to_unban': unban_timestamp}

        # Create the reason (if needed)
        if reason == "":
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
                f'The following error occurred when trying to temporarily ban member {member.mention}: ```{e}```', ephemeral=True)

        # Now log the temp ban in the #bot-output channel, and to file (probably more optimizing could be done here)
        await sendMessage(self.bot, self.bot_output_channel,
                          f'{member.mention}(ID: `{member.id}`) has been temporarily banned till <t:{unban_timestamp}:f> UTC. Reason: "{reason}".')
        await interaction.response.send_message(
            f'{member.mention} was temporarily banned. See `#bot-output` for more info.', ephemeral=True)
        return logandprint.info(f'{member.name}(ID: {member.id}) has been temporarily banned till {unban_time} UTC. Reason: "{reason}".')

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
                await interaction.response.send_message(f'Deleted the last {len(deleted) - 1} messages.', ephemeral=True)
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
    @app_commands.command(name='reloadblockedwords', description='Reload the list of blocked words. (Only usable by staff.)')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def reloadblockedwords(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        try:
            self.blocked_words = loadBlockedWords()
            await interaction.response.send_message('Blocked words reloaded!', ephemeral=True)
            return logandprint.info(f'User {interaction.user.name} reloaded blocked words list.', source='d')
        except Exception as e:
            await interaction.response.send_message('Failed to reload blocked words list with the following error:'
                                                    f'\n```{e}```', ephemeral=True)
            return logandprint.error(f'Failed to reload blocked words list with the following error: {e}', source='d')

    @app_commands.command(name='addblockedword', description='Add a blocked word or phrase to the blocked words list. (Only usable by staff.)')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def addblockedword(self, interaction: discord.Interaction, blocked_word: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        try:
            # Add the word to the list
            exportBlockedWord(blocked_word)

            # Reload blocked words
            self.blocked_words = loadBlockedWords()

            # Notify of success
            await interaction.response.send_message(f'Added ||{blocked_word}|| to blocklist.', ephemeral=True)

            # Censor the blocked word or phrase for logging
            if len(blocked_word) < 2:
                censored_blocked_word: str = blocked_word
            else:
                censored_blocked_word: str = blocked_word[0] + '*' * (len(blocked_word) - 2) + blocked_word[-1]

            # Log and print the word being added
            log.debug(f'Added word "{blocked_word}" to blocked words list.', source='d')
            return logandprint.info(f'User {interaction.user} added word "{censored_blocked_word}" to blocked '
                                    f'words list.', source='d')

        except Exception as e:
            await interaction.response.send_message(f'The following error occurred when trying to add to the blocked words list: ```{e}```', ephemeral=True)
            return logandprint.error(f'The following error occurred when user {interaction.user.name} tried to add to the blocked words list: {e}', source='d')


# Cog setup hook
async def setup(bot):
    await bot.add_cog(Moderation(bot))

