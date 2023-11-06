# Imports
import os.path
from discord.ext import commands, tasks
import discord
from discord import app_commands
import re
from datetime import datetime
from datetime import timedelta
import json
import asyncio
from utils.logger import log, logCogLoad
from utils.bot_utils import sendMessage


# TODO: (RE-ENABLE BANNING IN TEMP-BAN COMMAND!!)

def loadBlockedWords():
    with open('data/moderation/blocked_words.txt', 'r') as file:
        lines = file.readlines()
        # ha ha spaghetti code go brrrr
        blocked_words = [line.strip().replace(' ', '').lower() for line in lines]
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
    async def on_ready(self) -> None:
        print(f'Extension loaded: {self.__class__.__name__}')
        logCogLoad(self.__class__.__name__)
        self.checkForNeededUnbans.start()
        print('Started background task "Check for Needed Unbans."')
        return

    # TODO: Add returns in this function
    # Create functions
    async def handleSpam(self, user, level: int) -> None:
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

    # TODO: Add returns in this function as well
    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message) -> None:
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

    # TODO: Finish the status checking system
    # Listener: On Member Update
    # NOT WORKING YET!
    @commands.Cog.listener()
    async def on_member_update(self, before, after) -> None:
        # Ignore updates from bots
        if before.bot:
            return

        print('amogus')

        # Check user status to see if it's changed
        if before.status != after.status:
            user_status = str(after.status)
            for blocked_word in self.blocked_words:
                if re.search(rf'\b{re.escape(blocked_word)}\b', user_status):
                    # Notify moderators of the rule-breaking status
                    dm_channel = await after.create_dm()
                    await dm_channel.send(f'{after.author.mention}, your status contains a rule-breaking word or phrase.'
                                          ' If this is in error, please reach out to a moderator. '
                                          'If you do not update your status, you will be kicked from the server.')
                    await sendMessage(self.bot, self.bot_output_channel, f'User {after.author.mention} has a '
                                                                         'status containing a blocked word or phrase.')
                    log('info', f'User {after.author} has a status containing a blocked word or phrase.')

                    # Stop checking for blocked words after the first word is found
                    return

    # TODO: Verify functionality of unbanning system (the rest of it works already)
    # Task: Check for users needing to be unbanned
    @tasks.loop(minutes=5.0)
    async def checkForNeededUnbans(self) -> None:
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
                    return

                else:
                    # The user was not found in the guild
                    await sendMessage(self.bot, self.bot_output_channel, f'User {user}\'s temporary ban has '
                                                                         f'expired, but could not be found in the guild to unban.')
                    return
            else:
                return

    # Command: Kick
    @app_commands.command(name='kick', description='Kick a user from the server. Syntax: "/kick <user>"')
    @app_commands.describe(member='The member to kick.')
    @app_commands.describe(reason='The reason why the member is to be kicked. (Optional.)')
    @discord.app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "No reason was provided.") -> None:
        try:
            # Kick the user and log it to #bot-output and to file
            await interaction.response.send_message(f'User {member.display_name} has been kicked from the server.', ephemeral=True)
            message = f'{member.display_name} has been kicked from the server. Reason: "{reason}"'
            await member.kick(reason=reason)
            await sendMessage(self.bot, self.bot_output_channel, message)
            log('info', message)
            return
        except discord.Forbidden:
            await interaction.response.send_message('You don\'t have permission to use this command.', ephemeral=True)
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f'An error occurred trying to kick user {member}: {e}', ephemeral=True)
            return

    # Command: Ban
    @app_commands.command(name='ban', description='Ban a user from the server. Syntax: "/ban <user> [reason]"')
    @app_commands.describe(member='The member to ban.')
    @app_commands.describe(reason='The reason why the member is to be banned. (Optional.)')
    @app_commands.checks.has_permissions(kick_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = 'No reason was provided.') -> None:
        try:
            # Ban the user and log it to #bot-output and to file
            message = f'{member.display_name}(ID: {member.id}) has been banned from the server. Reason: "{reason}"'
            await member.ban(reason=reason)
            await sendMessage(self.bot, self.bot_output_channel, message)
            await interaction.response.send_message(f'User `{member.display_name}` was banned from the server.', ephemeral=True)
            return log('info', message)
        except discord.Forbidden:
            await interaction.response.send_message('You don\'t have permission to use this command.', ephemeral=True)
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f'An error occurred: {e}', ephemeral=True)
            return

    # Command: TempBan
    @app_commands.command(name='tempban', description=
                          'Temporarily ban a user from the server. Syntax: "/tempban <user> <duration in minutes> [reason]"')
    @app_commands.describe(member='The member to temporarily ban.')
    @app_commands.describe(duration='The duration in minutes to ban the member.')
    @app_commands.describe(reason='The reason why the member is to be banned. (Optional.)')
    @app_commands.checks.has_permissions(ban_members=True)
    async def tempban(self, interaction: discord.Interaction, member: discord.Member, duration: int, *, reason: str = "") -> None:

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

        # TODO: Put in a try/except block
        # Ban the user
        await member.ban(reason=reason)

        # Now log the temp ban in the #bot-output channel, and to file (probably more optimizing could be done here)
        await sendMessage(self.bot, self.bot_output_channel, f'{member.mention}(ID: {member.id}) has been temporarily banned till {unban_time} UTC. Reason: "{reason}".')
        await interaction.response.send_message(f'{member.mention} was temporarily banned. See `#bot-output` for more info.`', ephemeral=True)
        log('info', f'{member.name}(ID: {member.id}) has been temporarily banned till {unban_time} UTC. Reason: "{reason}".')
        return

    # Command: Unban
    @app_commands.command(name='unban', description='Unbans a user. Syntax: "/unban <user ID>"')
    @app_commands.describe(user_id='The ID of the user to unban.')
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str) -> None:
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
                return log('info', message)

        # Notify that the user is not banned.
        await interaction.response.send_message('That user has not been banned.', ephemeral=True)
        return log('info', f'{interaction.user} attempted to unban user with ID "{user_id}."')

    # Command: Purge
    @app_commands.command(name='purge', description='Delete a specified number of messages. (Limit 100.)')
    @app_commands.describe(amount='The amount of messages to be deleted.')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int) -> None:
        # Check if the specified amount is within the allowed range
        if 1 <= amount <= 100:
            logMessage = f'User {interaction.user} purged {amount} message(s) from channel "{interaction.channel}."'
            # Delete the specified number of messages (including the command message)
            deleted = await interaction.channel.purge(limit=amount + 1)
            # Send a notifying message, then delete it after three seconds.
            if amount == 1:
                # Make the message pretty if it's only one message to delete
                notifying_message = await interaction.response.send_message('Deleted the last sent message.', ephemeral=True)
                log('info', logMessage)
            else:
                notifying_message = await interaction.response.send_message(f'Deleted the last {len(deleted) - 1} messages.', ephemeral=True)
                log('info', logMessage)
            # Wait for three seconds, then delete the notification message
            await asyncio.sleep(3)
            await notifying_message.delete()
        else:
            # Log the attempted usage of the command
            logMessage = f'User {interaction.user} attempted to purge {amount} message(s) from channel "{interaction.channel}."'
            if amount < 1:
                await interaction.response.send_message('The amount must be at least one.', ephemeral=True)
                log('info', logMessage)
            elif amount > 100:
                await interaction.response.send_message("The amount must be under 100.", ephemeral=True)
                log('info', logMessage)
            return

    # Command: ReloadBlockedWords
    @app_commands.command(name='reloadblockedwords', description='Reload the list of blocked words.')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def reloadblockedwords(self, interaction: discord.Interaction) -> None:
        self.blocked_words = loadBlockedWords()
        await interaction.response.send_message('Blocked words reloaded!', ephemeral=True)
        return


async def setup(bot):
    await bot.add_cog(Moderation(bot))
