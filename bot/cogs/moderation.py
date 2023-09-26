# Imports
from discord.ext import commands
import discord
import re


def loadBlockedWords():
    with open('data/moderation/blocked_words.txt', 'r') as file:
        lines = file.readlines()
        blocked_words = [line.strip() for line in lines]
        file.close()
    return blocked_words


class Moderation(commands.Cog, description="Tools for moderators to use."):
    # Define vars
    blocked_words = loadBlockedWords()

    def __init__(self, bot):
        self.bot = bot

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')

    # Listener: On Message
    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message was sent by a bot to avoid responding to bots
        if message.author.bot:
            return

        message_content = re.sub(r'[^a-zA-Z0-9]', '', message.content.lower())
        for blocked_word in self.blocked_words:
            if re.search(rf'\b{re.escape(blocked_word)}\b', message_content):
                # Delete the message containing the blocked word
                await message.delete()
                await message.author.send(
                    f"{message.author.mention}, your message contains a rule-breaking word or phrase. If this is in "
                    "error, please reach out to a moderator. This is your (temp) offense.")
                return  # Stop the check after the first word is found

    # Command: Kick
    @commands.command(help="Kick a user from the server.")
    @commands.has_permissions(kick_members=True)  # Only allow users with kick permissions to use this command
    async def kick(self, ctx, user: discord.Member, *, reason="No reason was provided"):
        try:
            await user.kick(reason=reason)
            await ctx.send(f'{user.display_name} has been kicked from the server. Reason: "{reason}"')
        except discord.Forbidden:
            await ctx.send('You don\'t have permission to use this command.')
        except discord.HTTPException as e:
            await ctx.send(f'An error occurred: {e}')

    # Command: Ban
    @commands.command(help='Ban a user from the server..')
    @commands.has_permissions(ban_members=True)  # Only people with the ban permission can use this command
    async def ban(self, ctx, user: discord.Member, *, reason='No reason was provided.'):
        try:
            await user.ban(reason=reason)
            await ctx.send(f'{user.display_name} has been banned from the server. Reason: "{reason}"')
        except discord.Forbidden:
            await ctx.send('You don\'t have permission to use this command.')
        except discord.HTTPException as e:
            await ctx.send(f'An error occurred: {e}')

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
