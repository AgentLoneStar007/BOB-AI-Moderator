# Imports
import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import Log, LogAndPrint
from utils.bot_utils import checkIfOwner, sendMessage
from dotenv import load_dotenv
import os


# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()

# Vars
load_dotenv()
BOT_OUTPUT_CHANNEL: str = os.getenv("BOT_OUTPUT_CHANNEL")


class Training(commands.Cog, description="Utilities for training new staff members."):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.output_channel: str = BOT_OUTPUT_CHANNEL
        self.last_message_deleter = None
        self.last_notify_message = None
        self.last_message_deleted_author = None
        self.last_message_deleted_channel = None
        self.message_delete_count: int = 0
        return

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return logandprint.logCogLoad(self.__class__.__name__)

    # Listener: On Message Delete
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Prevent testing webhooks(webhooks return NoneType for an author)
        if not message.author:
            return

        # Create variable containing the name of the staff in training role
        training_role: str = 'Staff in Training'

        # Since there's no attribute of who deleted the message, I have to get this from the audit logs
        async for entry in message.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
            # If the entry target(the message author) is the message's author,
            if entry.target == message.author:
                # Create a var of who deleted the message
                deleter: discord.Member = entry.user

                # If the deleter is the bot, stop the function
                if deleter.id == self.bot.user.id:
                    return

                # If the user doesn't have the staff in training role, stop the function
                if not discord.utils.get(deleter.roles, name=training_role):
                    return

                # To prevent spamming the message deleter, check if last_message_deleter has a value
                if not self.last_message_deleter:
                    # Update last deleted message variables
                    self.last_message_deleter: discord.Member = deleter
                    self.last_message_deleted_author: discord.Member = message.author
                    self.last_message_deleted_channel: discord.TextChannel = message.channel
                    # Update the last sent notify message var by sending a new message
                    self.last_notify_message: discord.Message = await sendMessage(
                        self.bot, self.output_channel,
                        f'Trainee @{deleter.name} deleted message from user {message.author.mention} in channel {message.channel.mention}.')

                # WHERE I LEFT OFF: Add a system that checks all vars, and edits the notify message to say "trainee
                # deleted two messages from author in channel," or "trainee deleted two messages from author in channels
                # one and two," or "trainee deleted message from authors one and two in channel," and so on
                elif self.last_message_deleter.id == deleter.id:
                    # spaghetti code warning
                    if self.last_message_deleted_channel == message.channel and self.last_message_deleted_author == message.author:
                        await self.last_notify_message.edit(content=f'Trainee @{deleter.name} deleted message from user {message.author.mention} in channel {message.channel.mention}.')

        return


async def setup(bot) -> None:
    return await bot.add_cog(Training(bot))
