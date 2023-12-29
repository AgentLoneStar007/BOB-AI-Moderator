# Imports
import discord
import asyncio
from discord.ext import commands
from utils.logger import Log, LogAndPrint


# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()

# TODO: Redo spam prevention system. My ideas are a more "smart" way of preventing spam, and getting less false
#  positives by comparing the message author to the author of the last message sent, and adjusting cooldown times more.
#  (The current system seems like it could have a lot of people getting muted when not spamming.)


class SpamPrevention(commands.Cog, description="Prevents users from sending large amounts of messages at once."):
    # Define vars
    bot_output_channel = '1155842466482753656'
    user_message_counts_1 = {}
    user_message_counts_2 = {}
    user_message_counts_3 = {}
    message_reset_interval = 30  # in seconds
    message_limit = 7  # message limit per reset interval

    def __init__(self, bot) -> None:
        self.bot = bot
        return

    # TODO: Add returns in this function
    # Create functions
    async def handleSpam(self, user: discord.Member, level: int) -> None:
        # Convert user ID to a string
        user_id = str(user.id)

        # Run level 1 spam checks
        if level == 1 and not any(
                user_id in counts for counts in (self.user_message_counts_2, self.user_message_counts_3)):
            already_run = False
            # Putting this in a try/except because Discord's API can be slow, and the bot will send duplicate
            #  messages if not handled
            try:
                del self.user_message_counts_1[user_id]
            except:
                already_run = True
            if not already_run:
                self.user_message_counts_2[user_id] = 0
                await user.send('Stop spamming. This is your first warning. '
                                'You will be muted for five minutes upon your third warning.')

        # Run level 2 spam checks
        elif level == 2 and not any(
                user_id in counts for counts in (self.user_message_counts_1, self.user_message_counts_3)):
            already_run = False
            try:
                del self.user_message_counts_2[user_id]
            # TODO: Make the except statement more specific so PyCharm will stop yelling at me
            except:
                already_run = True
            if not already_run:
                await user.send('Stop spamming. This is your second warning. '
                                'You will be muted for five minutes upon your third.')
                self.user_message_counts_3[user_id] = 0

            # Run level 3 spam checks
        elif level == 3 and not any(
                user_id in counts for counts in (self.user_message_counts_1, self.user_message_counts_2)):
            await user.send('You have been muted for five minutes.')
            # Mute the user for five minutes
            role = discord.utils.get(user.guild.roles, name="MUTED")
            await user.add_roles(role)
            await asyncio.sleep(300)

            # Remove the mute after the five minutes are up
            await user.remove_roles(role)
            del self.user_message_counts_3[user_id]

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        return logandprint.logCogLoad(self.__class__.__name__)

    # Check message for spam function
    async def checkForSpam(self, message: discord.Message) -> None:
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

        return


async def setup(bot) -> None:
    return await bot.add_cog(SpamPrevention(bot))
