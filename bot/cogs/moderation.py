# Imports
from discord.ext import commands
import discord


class Moderation(commands.Cog, description="Tools for moderators to use."):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')

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
    @commands.has_permissions(manage_messages=True)  # Only allow users with message management permissions to use this command
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


async def setup(bot):
    await bot.add_cog(Moderation(bot))

