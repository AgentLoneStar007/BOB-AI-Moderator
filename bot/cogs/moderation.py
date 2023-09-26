# Imports
from discord.ext import commands
import discord
import re
import datetime
from datetime import timedelta
from utils.logger import log, logCommand, logCogLoad
from utils.bot_utils import sendMessage


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

    def __init__(self, bot):
        self.bot = bot

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')
        logCogLoad(self.__class__.__name__)

    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message was sent by a bot to avoid responding to bots
        if message.author.bot:
            return

        message_content = re.sub(r'[^a-zA-Z0-9]', '', message.content.lower())
        for blocked_word in self.blocked_words:
            if re.search(rf'\b{re.escape(blocked_word)}\b', message_content):
                # Delete the message containing the blocked word, notify the user, and log the offense
                await message.delete()
                await message.author.send(
                    f"{message.author.mention}, your message contains a rule-breaking word or phrase. If this is in "
                    "error, please reach out to a moderator. This is your (temp) offense.")
                log('info', f'User {message.author} sent a message containing a blocked word or phrase.')

                # Stop checking for blocked words after the first word is found
                return

    # Command: Kick
    @commands.command(help="Kick a user from the server.")
    @commands.has_permissions(kick_members=True)  # Only allow users with kick permissions to use this command
    async def kick(self, ctx, user: discord.Member, *, reason="No reason was provided."):
        try:
            # Kick the user and log it to #bot-output and to file
            message = f'{user.display_name} has been kicked from the server. Reason: "{reason}"'
            await user.kick(reason=reason)
            await sendMessage(self.bot, ctx, self.bot_output_channel, message)
            log('info', message)
        except discord.Forbidden:
            await ctx.send('You don\'t have permission to use this command.')
        except discord.HTTPException as e:
            await ctx.send(f'An error occurred trying to kick user {user}: {e}')

    # Command: Ban
    @commands.command(help='Ban a user from the server..')
    @commands.has_permissions(ban_members=True)  # Only people with the ban permission can use this command
    async def ban(self, ctx, user: discord.Member, *, reason='No reason was provided.'):
        try:
            # Ban the user and log it to #bot-output and to file
            message = f'{user.display_name} has been banned from the server. Reason: "{reason}"'
            await user.ban(reason=reason)
            await sendMessage(self.bot, ctx, self.bot_output_channel, message)
            log('info', message)
        except discord.Forbidden:
            await ctx.send('You don\'t have permission to use this command.')
        except discord.HTTPException as e:
            await ctx.send(f'An error occurred: {e}')

    # Command: TempBan
    @commands.command(
        help='Temporarily ban a user from the server. Syntax: "!tempban <user> <duration in minutes> [reason]"')
    async def tempban(self, ctx, member: discord.Member, duration: int, *, reason="No reason was provided."):
        # Calculate the unban time (current time + duration)
        #unban_time = datetime.utcnow() + timedelta(seconds=duration_seconds)

        try:
            # Get the current time in UTC, get the time that it will be to unban the user, and format it to a string
            current_time = datetime.utcnow()
            future_time = current_time + timedelta(minutes=duration)
            unban_time = future_time.strftime("%Y-%m-%d %H:%M")




            # await member.ban(reason=reason)
            #await member.unban(reason="Temporary ban expired")

            # Send a confirmation message
            #message = f'{member.mention} has been temporarily banned till {duration}. Reason: "{reason}".'
            #await sendMessage(self.bot, ctx, self.bot_output_channel, message)






            #await ctx.send(f"{member.mention} has been unbanned after {duration} minutes.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban members.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    # Command: Purge
    @commands.command(help='Delete a specified number of messages. (Limit 100.)')
    @commands.has_permissions(
        manage_messages=True)  # Only allow users with message management permissions to use this command
    async def purge(self, ctx, amount: int):
        # Check if the specified amount is within the allowed range
        if 1 <= amount <= 100:
            # Delete the specified number of messages (including the command message)
            deleted = await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f'Deleted the last {len(deleted) - 1} messages.')
        else:
            if amount < 1:
                await ctx.send('The amount must be at least one.')
            elif amount > 100:
                await ctx.send("The amount must be under 100.")

    @commands.command()
    async def reloadblockedwords(self, ctx):
        self.blocked_words = loadBlockedWords()
        await ctx.send('Blocked words reloaded!')


async def setup(bot):
    await bot.add_cog(Moderation(bot))
