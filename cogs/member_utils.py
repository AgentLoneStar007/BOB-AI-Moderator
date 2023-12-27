# Imports
import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import Log, logCommand, logCogLoad
from dotenv import load_dotenv
import os

# Create object of Log class
log = Log()

# Vars
load_dotenv()
QUESTION_CHANNEL_ID: int = int(os.getenv("QUESTION_CHANNEL_ID"))


# Modal(pop-up text input box) class
class QuestionModal(discord.ui.Modal, title='Question for Staff'):
    # Create user variable to get the name of the user asking the question
    user: discord.Member

    # Create question input field
    question = discord.ui.TextInput(
        style=discord.TextStyle.long,
        max_length=500,
        label='Question',
        required=True,
        placeholder='What\'s the question you want to leave for the server staff?'
    )

    # This function will be run once the user clicks "Submit"
    async def on_submit(self, interaction: discord.Interaction) -> None:
        # Create an embed that contains the question the user left, and the user himself
        embed: discord.Embed = discord.Embed(
            title='Question',
            description=self.question.value,
            color=discord.Color.from_rgb(1, 162, 186)
        )
        embed.add_field(name='Asked by:', value=self.user.mention)

        # Get the channel from the server/guild
        channel: discord.channel.TextChannel = interaction.guild.get_channel(QUESTION_CHANNEL_ID)
        # Send the embed in the channel
        await channel.send(embed=embed)
        await interaction.response.send_message(f'Your question was submitted, {self.user.mention}, and a response will '
                                                'be issued shortly.', ephemeral=True)
        return logCommand('info', f'User {interaction.user.name} submitted a question to staff.')

    # This function will be run if there's an error
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('The following error occurred when trying to submit your form: '
                                                 f'{error}', ephemeral=True)
        return log('info', f'An error occurred when user {interaction.user.name} tried to submit a question.')


class MemberUtils(commands.Cog, description="Utilities for server members."):
    def __init__(self, bot) -> None:
        self.bot = bot
        return

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logCogLoad(self.__class__.__name__)
        return print(f'Extension loaded: {self.__class__.__name__}')

    # Command: Question
    @app_commands.command(name='question', description='Leave a question for the server staff to answer.')
    # By specifying i.guid_id and i.user.id, it's a member cooldown, meaning that a member in a server can use the
    # command, go on cooldown, but go to another server and use the command. In other words, the cooldown is
    # guild-specific, and not bot-wide, if the bot is on multiple servers. This is unnecessary for this bot because
    # he'll probably only ever be on one server, but it's good practice.
    @app_commands.checks.cooldown(1, 300.0, key=lambda i: (i.guild_id, i.user.id))
    async def question(self, interaction: discord.Interaction) -> None:
        question_modal: discord.ui.Modal = QuestionModal()
        question_modal.user = interaction.user
        await interaction.response.send_modal(question_modal)
        return log.info(f'{interaction.user.name} started a questionnaire form for staff to answer.')


async def setup(bot) -> None:
    return await bot.add_cog(MemberUtils(bot))

