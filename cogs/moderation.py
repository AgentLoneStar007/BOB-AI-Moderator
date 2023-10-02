# Imports
import os.path
from discord.ext import commands, tasks
import discord
import re
from datetime import datetime
from datetime import timedelta
import json
import asyncio
from utils.logger import log, logCogLoad
from utils.bot_utils import sendMessage


# TODO: Figure out how to fix spaces issue with blocked words(blocked words/phrases can't have spaces in them,
#  or else it breaks.
def loadBlockedWords():
    with open('data/moderation/blocked_words.txt', 'r') as file:
        lines = file.readlines()
        blocked_words = [line.strip() for line in lines]
        file.close()
    return blocked_words


class Moderation(commands.Cog, description="Tools for moderators to use."):
    # Define vars
    blocked_words = loadBlockedWords()
    bot_output_channel = '1155842466482753656'
    user_message_counts_1 = {}
    user_message_counts_2 = {}
    user_message_counts_3 = {}
    message_reset_interval = 30  # in seconds
    message_limit = 7  # message limit per reset interval

    def __init__(self, bot):
        self.bot = bot

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')
        logCogLoad(self.__class__.__name__)
        self.checkForNeededUnbans.start()
        print('Started background task "Check for Needed Unbans."')

    # Create functions
    async def handleSpam(self, user, level: int):
        user_id = str(user.id)

        if level == 1 and not any(user_id in counts for counts in (self.user_message_counts_2, self.user_message_counts_3)):
            already_run = False
            try:
                del self.user_message_counts_1[user_id]
            except:
                already_run = True
            if not already_run:
                self.user_message_counts_2[user_id] = 0
                await user.send('Stop spamming. This is your first warning. '
                            'You will be muted for five minutes upon your third warning.')

        elif level == 2 and not any(user_id in counts for counts in (self.user_message_counts_1, self.user_message_counts_3)):
            already_run = False
            try:
                del self.user_message_counts_2[user_id]
            except:
                already_run = True
            if not already_run:
                await user.send('Stop spamming. This is your second warning. '
                                'You will be muted for five minutes upon your third.')
                self.user_message_counts_3[user_id] = 0

        elif level == 3 and not any(user_id in counts for counts in (self.user_message_counts_1, self.user_message_counts_2)):
            await user.send('You have been muted for five minutes.')
            role = discord.utils.get(user.guild.roles, name="MUTED")
            await user.add_roles(role)
            await asyncio.sleep(300)
            await user.remove_roles(role)
            del self.user_message_counts_3[user_id]

    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message was sent by a bot to avoid responding to bots
        if message.author.bot:
            return

        # Use Regex formatting to search message for blocked words.
        message_content = re.sub(r'[^a-zA-Z0-9]', '', message.content.lower())
        for blocked_word in self.blocked_words:
            if re.search(rf'\b{re.escape(blocked_word)}\b', message_content):
                # Delete the message containing the blocked word, notify the user, and log the offense
                await message.delete()
                await message.author.send(
                    f"{message.author.mention}, your message contains a rule-breaking word or phrase. If this is in "
                    "error, please reach out to a moderator. This is your (feature coming soon) offense.")
                log('info', f'User {message.author} sent a message containing a blocked word or phrase.')

                # Stop checking for blocked words after the first word is found
                return

        # Make vars accessible without passing self
        user_message_counts_1 = self.user_message_counts_1
        user_message_counts_2 = self.user_message_counts_2
        user_message_counts_3 = self.user_message_counts_3
        message_reset_interval = self.message_reset_interval
        message_limit = self.message_limit
        handleSpam = self.handleSpam

        user_id = str(message.author.id)
        # Check if the user is not in any dictionary. If not, add them to dictionary 1
        if not any(
                user_id in counts for counts in (user_message_counts_1, user_message_counts_2, user_message_counts_3)):
            user_message_counts_1[user_id] = 0

        # Unoptimized code - fix later
        if user_id in user_message_counts_1:
            user_message_counts_1[user_id] += 1
            if user_message_counts_1[user_id] > message_limit:  # 7 messages per 30 seconds
                await handleSpam(message.author, 1)
                return
            await asyncio.sleep(message_reset_interval)
            if user_id in user_message_counts_1:
                user_message_counts_1[user_id] -= 1

        elif user_id in user_message_counts_2:
            user_message_counts_2[user_id] += 1
            if user_message_counts_2[user_id] > message_limit:
                await handleSpam(message.author, 2)
                return
            await asyncio.sleep(message_reset_interval * 1.5)
            if user_id in user_message_counts_2:
                user_message_counts_2[user_id] -= 1

        elif user_id in user_message_counts_3:
            user_message_counts_3[user_id] += 1
            if user_message_counts_3[user_id] > message_limit:
                await handleSpam(message.author, 3)
                return
            await asyncio.sleep(message_reset_interval * 2)
            if user_id in user_message_counts_3:
                user_message_counts_3[user_id] -= 1

    # Task: Check for users needing to be unbanned
    @tasks.loop(minutes=5.0)
    async def checkForNeededUnbans(self):
        # Open and parse data
        with open('data/moderation/unban_times.json', 'r') as file:
            data = json.load(file)

        # Get the current UTC time
        current_time = datetime.utcnow()

        # Iterate through the "temp_banned_users" array and compare times
        for entry in data.get("temp_banned_users", []):
            user = entry.get("user")
            time_to_unban_str = entry.get("time_to_unban")

            # Parse the time string from the entry into a datetime object
            time_to_unban = datetime.strptime(time_to_unban_str, "%Y-%m-%d %H:%M")

            # Compare the current time with the time in the entry
            if current_time >= time_to_unban:
                # Retrieve the user's ID by username (assuming the username is unique in the guild)
                GUILD_ID = int(os.getenv("LONESTAR_GUILD_ID"))
                guild = self.bot.get_guild(GUILD_ID)
                member = discord.utils.get(guild.members, name=user)

                if member:
                    reason = "Temporary ban on user expired."
                    # Unban the user by their ID
                    await guild.unban(member, reason=reason)

                    # Notify that the user has been unbanned
                    await sendMessage(self.bot, self.bot_output_channel, f'User {user} unbanned.'
                                                                         f' Reason: "{reason}"')

                else:
                    # The user was not found in the guild
                    await sendMessage(self.bot, self.bot_output_channel, f'User {user}\'s temporary ban has '
                                                                         f'expired, but could not be found in the guild to unban.')
            else:
                return

    # Command: Kick
    @commands.command(help='Kick a user from the server. Syntax: "!kick <user>"')
    @commands.has_permissions(kick_members=True)  # Only allow users with kick permissions to use this command
    async def kick(self, ctx, user: discord.Member, *, reason="No reason was provided."):
        try:
            # Kick the user and log it to #bot-output and to file
            message = f'{user.display_name} has been kicked from the server. Reason: "{reason}"'
            await user.kick(reason=reason)
            await sendMessage(self.bot, self.bot_output_channel, message)
            log('info', message)
        except discord.Forbidden:
            await ctx.send('You don\'t have permission to use this command.')
        except discord.HTTPException as e:
            await ctx.send(f'An error occurred trying to kick user {user}: {e}')

    # Command: Ban
    @commands.command(help='Ban a user from the server. Syntax: "!ban <user>"')
    @commands.has_permissions(ban_members=True)  # Only people with the ban permission can use this command
    async def ban(self, ctx, user: discord.Member, *, reason='No reason was provided.'):
        try:
            # Ban the user and log it to #bot-output and to file
            message = f'{user.display_name}(ID: {user.id}) has been banned from the server. Reason: "{reason}"'
            await user.ban(reason=reason)
            await sendMessage(self.bot, self.bot_output_channel, message)
            log('info', message)
        except discord.Forbidden:
            await ctx.send('You don\'t have permission to use this command.')
        except discord.HTTPException as e:
            await ctx.send(f'An error occurred: {e}')

    # Command: TempBan
    @commands.command(
        help='Temporarily ban a user from the server. Syntax: "!tempban <user> <duration in minutes> [reason]"')
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.Member, duration: int, *, reason=""):

        # Get the current time in UTC, get the time that it will be to unban the user, and format it to a string
        current_time = datetime.utcnow()
        future_time = current_time + timedelta(minutes=duration)
        unban_time = future_time.strftime("%Y-%m-%d %H:%M")

        # Create the dictionary entry
        temp_banned_user = {'user': f'{member}', 'time_to_unban': unban_time}

        # Create the reason (if needed)
        if reason == "":
            reason = f"No reason was provided. You will be unbanned on {unban_time} UTC."

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
        # await member.ban(reason=reason)
        # TODO: (RE-ENABLE BANNING IN TEMPBAN COMMAND!!)

        # Now log the temp ban in the #bot-output channel, and to file
        message = f'{member.mention}(ID: {member.id}) has been temporarily banned till {unban_time}. Reason: "{reason}".'
        await sendMessage(self.bot, self.bot_output_channel, message)
        log('info', message)

    @commands.command(help='Unbans a user. Syntax: "!unban <user ID>"')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        # Get the guild (server) object
        guild = ctx.guild

        # Check if the user is banned
        bans = await guild.bans()
        banned_user = discord.utils.get(bans, user__id=user_id)

        if banned_user:
            # Unban the user
            await guild.unban(banned_user.user)

            # Notify that the user has been unbanned
            message = f'User with ID "{user_id}" has been unbanned by {ctx.author}.'
            await sendMessage(self.bot, self.bot_output_channel, message)
            await log('info', message)
        else:
            # Notify that the user is not banned.
            await ctx.send('That user has not been banned.')
            log('info', f'{ctx.author} attempted to unban user with ID "{user_id}."')

    # Command: Purge
    @commands.command(help='Delete a specified number of messages. (Limit 100.)')
    @commands.has_permissions(
        manage_messages=True)  # Only allow users with message management permissions to use this command
    async def purge(self, ctx, amount: int):
        # Check if the specified amount is within the allowed range
        if 1 <= amount <= 100:
            logMessage = f'User {ctx.author} purged {amount} message(s) from channel "{ctx.channel}."'
            # Delete the specified number of messages (including the command message)
            deleted = await ctx.channel.purge(limit=amount + 1)
            # Send a notifying message, then delete it after three seconds.
            if amount == 1:
                notifying_message = await ctx.send('Deleted the last sent message.')
                log('info', logMessage)
            else:
                notifying_message = await ctx.send(f'Deleted the last {len(deleted) - 1} messages.')
                log('info', logMessage)
            await asyncio.sleep(3)
            await notifying_message.delete()
        else:
            logMessage = f'User {ctx.author} attempted to purge {amount} message(s) from channel "{ctx.channel}."'
            if amount < 1:
                await ctx.send('The amount must be at least one.')
                log('info', logMessage)
            elif amount > 100:
                await ctx.send("The amount must be under 100.")
                log('info', logMessage)

    @commands.command(help='Reload the list of blocked words.')
    @commands.has_permissions(manage_messages=True)
    async def reloadblockedwords(self, ctx):
        self.blocked_words = loadBlockedWords()
        await ctx.send('Blocked words reloaded!')


async def setup(bot):
    await bot.add_cog(Moderation(bot))
