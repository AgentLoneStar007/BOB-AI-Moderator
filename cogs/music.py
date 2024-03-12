# Imports
import discord
from discord import app_commands
from discord.ext import commands, tasks
import wavelink
import datetime
import re
from utils.logger import Log, LogAndPrint

# TODO: Add cool-downs to commands to prevent spamming(which may or may not work)
# TODO: Create limit on queue size for player
# TODO: Add auto-compression to prevent people from playing deafening tracks and blowing others' ears out (I think
#  Wavelink has audio leveling systems I can use)
# TODO: Find a way to prevent people from playing videos with blocked words in the title(maybe)
# TODO: Add a command to loop the current queue called /loopqueue

# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()


# The following three functions were written by ChatGPT. I know; shut up.
def convertDuration(milliseconds) -> str:
    """
    Converts an

    :param milliseconds:
    :return:
    """

    # Convert milliseconds to seconds
    seconds: int = milliseconds / 1000

    # Create a timedelta object representing the duration
    duration = datetime.timedelta(seconds=seconds)

    # Format the duration as HH:MM:SS, even if hours exceed 99
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    if int(hours) == 0:
        formatted_time: str = f"{int(minutes):02}:{int(seconds):02}"
    else:
        formatted_time: str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    return formatted_time


def padTimeFormat(input_str: str) -> str | bool:
    """
    A function that converts an input string of time that's roughly in the format of
    "HH:MM:SS" or "MM:SS". No field requires a padding of zeroes; an input of "3:39"
    will work just as well as "00:03:39". The function will return a full time string
    in the format "HH:MM:SS", padding each field with a zero, if needed.

    :param input_str: A string in the rough format of "HH:MM:SS" or "MM:SS".
    :returns: A *str* in the format "HH:MM:SS", or a *bool* of False if the
    input cannot be formatted.
    :raises None:
    """

    # Regular expression patterns for various time formats
    time_formats: list = [
        r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$',  # HH:MM:SS
        r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$',  # H:MM:SS (optional leading zero for hours)
        r'^[0-5][0-9]:[0-5][0-9]$'  # MM:SS
    ]

    # Check if the input matches any of the patterns
    for pattern in time_formats:
        # If a match is found,
        if re.match(pattern, input_str):
            # Split the input by the colons
            parts: list = input_str.split(":")

            # If the input is in the form "MM:SS", add "00" to the hours' place
            if len(parts) == 2:
                parts.insert(0, "00")  # Add hours as 00

            # And finally, return the full "HH:MM:SS" string, padding each space with a zero as needed
            return ":".join(part.zfill(2) for part in parts)

    return False  # Return False if the input is invalid


def millisecondsToTime(milliseconds: int) -> str:
    """
    A function that converts an input of milliseconds to a string of either "HH:MM:SS" or "MM:SS", as needed.

    :param milliseconds: The input of milliseconds to convert.
    :returns: a *str* in the format of either "HH:MM:SS" or "MM:SS", negating hours if not needed.
    :raises None:
    """

    seconds = int(milliseconds / 1000)
    minutes = int(seconds / 60) % 60
    remaining_seconds = seconds % 60

    # Check if hours are needed (more than 60 minutes)
    if minutes >= 60:
        hours = int(minutes / 60)
        minutes = minutes % 60
        # Return the string with the hours field
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
    else:
        # Return the string without the hours field
        return f"{minutes:02d}:{remaining_seconds:02d}"


def timeToMilliseconds(time_str: str) -> int:
    """
    A function that converts a time string, in the format of "HH:MM:SS" to milliseconds.

    :param time_str: The time string to convert.
    :returns: int - The milliseconds in an integer format.
    :raises None:
    """

    # Split the input into hours, minutes, and seconds, and put the values in a list
    parts: list = time_str.split(':')

    # Assign each part in the list to hours, minutes, and seconds
    hours, minutes, seconds = map(int, parts)

    # Get the total amount of seconds in the input
    total_seconds = hours * 3600 + minutes * 60 + seconds

    # Convert total seconds to milliseconds
    milliseconds: int = total_seconds * 1000

    # And finally, return it
    return milliseconds


# Function that runs basic checks for music-related commands
# Checks if user is in VC, bot is in VC, player is running, etc.
async def runChecks(
        interaction: discord.Interaction,
        bot_not_in_vc_msg: str = 'I am not connected to a voice channel.',
        user_not_in_vc_msg: str = 'You must be connected to the same channel as me to perform this action.',
        user_in_different_vc_msg: str = 'You must be in the same channel as me to perform this action.'
        ) -> bool:

    # Create user voice chat and bot voice chat vars
    user_vc = interaction.user.voice
    bot_vc = interaction.guild.voice_client

    # Bot not connected to VC
    if not bot_vc:
        await interaction.response.send_message(bot_not_in_vc_msg, ephemeral=True)
        return False

    # User not connected to VC
    if not user_vc:
        await interaction.response.send_message(user_not_in_vc_msg, ephemeral=True)
        return False

    # User in different VC
    if user_vc.channel != bot_vc.channel:
        await interaction.response.send_message(user_in_different_vc_msg, ephemeral=True)
        return False

    # Return true if all checks are passed
    return True


async def checkPlayer(interaction: discord.Interaction, custom_message: str = None) -> wavelink.Player | None:
    try:
        player: wavelink.Player = interaction.guild.voice_client
        return player
    except Exception as error:
        # TODO: Remove the following (it's here for testing purposes)
        logandprint.debug(f'This is the error output for the try/except in the checkPlayer function in the music.py '
                          f'cog. The error output is: {error}')
        if not custom_message:
            custom_message: str = 'No music player is currently running.'
        await interaction.response.send_message(custom_message, ephemeral=True)
        return None


class Music(commands.Cog, description="Commands relating to the voice chat music player."):
    def __init__(self, bot) -> None:
        self.bot = bot

        # Vars
        self.loop_track: bool = False
        self.current_track: wavelink.Playable | None = None

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logandprint.logCogLoad(self.__class__.__name__)
        self.checkIfConnectedToVoiceChannel.start()
        return logandprint.info('Started background task "Check If Connected to Voice Channel."')

    # Task: Check if connected to voice channel
    @tasks.loop(minutes=5.0)
    async def checkIfConnectedToVoiceChannel(self) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            for guild in self.bot.guilds:
                voice_client = guild.voice_client
                await voice_client.disconnect()
            return

        # Vars
        should_leave: bool = False

        # NOTE: If any other feature involving voice chats is added that is NOT Wavelink, the following code will break!

        # Loop through every guild to get connected voice clients
        for guild in self.bot.guilds:
            player: wavelink.Player | None = guild.voice_client
            # If voice client is connected
            if player:
                # If the bot is the only one present, disconnect
                if len(player.channel.members) == 1:
                    should_leave = True

                # Check if player.current exists. If it doesn't, there's no current track playing.
                if not player.current:
                    should_leave = True

                if should_leave:
                    # Log message and print to console
                    logandprint.info(f"Leaving {player.channel} due to inactivity.")

                    # Clear the queue
                    player.queue.reset()

                    # Disconnect from VC
                    await player.disconnect()

                    return

        return

    # Run Before Task: Check if connected to voice channel
    @checkIfConnectedToVoiceChannel.before_loop
    async def before_check_if_connected_to_voice_channel(self) -> None:
        # Wait till bot is ready before starting task
        return await self.bot.wait_until_ready()

    # Listener: On Track End
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Create player object
        player: wavelink.Player = payload.player

        # Loop current track if loop is enabled
        if self.loop_track:
            await player.play(self.current_track)
            return

        # Go to the next song in the queue on track end if queue isn't empty
        if not player.queue.is_empty:
            next_track = player.queue.get()
            self.current_track = next_track
            await player.play(next_track)
        return

    # Command: Play
    @app_commands.command(name='play', description='Play a YouTube video in a voice chat. Syntax: "/play <URL or search term>"')
    @app_commands.describe(query='The search term or YouTube video or playlist URL to play.')
    async def play(self, interaction: discord.Interaction, *, query: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Get user VC
        user_vc = interaction.user.voice

        # Check if user is in VC
        if not user_vc:
            return await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)

        # Check if player is already running. If not, create a new player
        if not interaction.client.voice_clients:
            player: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            # If player is running, check if bot is in a different VC than user with music playing
            player: wavelink.Player = interaction.guild.voice_client
            if player.playing and user_vc.channel != interaction.guild.voice_client.channel:
                return await interaction.response.send_message("I am already playing music in another channel.", ephemeral=True)

            # Check if player is not playing music, and user is in different VC
            if not player.playing and not player.paused and user_vc.channel != interaction.guild.voice_client.channel:
                await player.move_to(user_vc.channel)

        await interaction.response.send_message(f"Loading your query of `{query}`, please wait...", ephemeral=True)

        # If query is playlist URL
        if "https://" and "list=" in query:
            # Error handler in case BOB can't find any playlists matching URL
            try:
                playlist: wavelink.Playlist = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTube)
            except ValueError:
                await interaction.edit_original_response(content="I couldn't find any playlists matching that URL.")
                return

                # Create list of tracks in playlist
            playlist_tracks: list[wavelink.Playable] = playlist.tracks
            notify_about_playlist_too_long: bool = False

            # If playlist is too long, update notify var
            if len(playlist_tracks) > 100:
                notify_about_playlist_too_long = True

            # Create selected track int
            selected_track: int = playlist.selected
            # If selected track is -1(no selected track), selected track is the first item in the playlist
            selected_track = 0 if selected_track == -1 else selected_track
            # If the selected item to the end of the playlist is less than or equal to 100, selection_end equals the
            # end index of the playlist. Otherwise, it equals 100 + selected track. (The point is selection_end must be
            # 100 more than selected_track or less, putting a limit of 100 tracks from a playlist.)
            selection_end = 100 + selected_track if len(playlist_tracks) >= (100 + selected_track) else (len(playlist_tracks))

            # Make the list only 100 tracks in length
            playlist_tracks = playlist_tracks[selected_track:selection_end]

            # Create the embed
            embed = discord.Embed(
                title=f"Playlist: {playlist.name}",
                color=discord.Color.from_rgb(1, 162, 186)
            )

            # Add five items in the playlist to the embed
            limit: int = 6 if len(playlist_tracks) > 5 else len(playlist_tracks)
            i: int = 1
            while i < limit:
                embed.add_field(name=f"Track {i}:", value=f"[{playlist_tracks[i].title}]({playlist_tracks[i].uri})",
                                inline=False)
                i: int = i + 1

            # If playlist is greater than five tracks, add a notifying footer to the embed
            if len(playlist_tracks) > 5:
                embed.set_footer(text=f"And {len(playlist_tracks) - 6} more tracks...")

            # If there's already a song playing:
            if player.current:
                # Add all items to queue
                for track in playlist_tracks:
                    player.queue.put(track)

                # Set embed description var
                embed_description: str = f"Added {len(playlist_tracks)} songs to queue in channel {player.channel}."

                # If playlist is too long, change description of embed to notify user
                if notify_about_playlist_too_long:
                    embed_description = embed_description + " (Playlist size limit is 100 tracks.)"

                # Set the description for the embed
                embed.description = embed_description

                # Send the embed
                await interaction.edit_original_response(embed=embed, content="")

            else:
                # Play the first track in the list
                await player.play(playlist_tracks[0])

                # Unpause the player, if paused
                await player.pause(False)

                # Update the current_track var with the now playing track
                self.current_track = playlist_tracks[0]

                # Add all items to queue, excluding the first song(which is the one that will start playing immediately)
                for track in playlist_tracks[1:]:
                    player.queue.put(track)

                # Set embed description var
                embed_description: str = (f"Now playing [{playlist_tracks[0].title}]({playlist_tracks[0].uri}), and "
                                          f"added {len(playlist_tracks) - 1} songs to queue in channel {player.channel}.")

                # If playlist is too long, change description of embed to notify user
                if notify_about_playlist_too_long:
                    embed_description = embed_description + f' (Playlist size limit is 100 tracks.)'

                # Set the description for the embed
                embed.description = embed_description

                # Send the embed
                await interaction.edit_original_response(embed=embed, content="")

        # Otherwise query is track or search query
        else:
            tracks: wavelink.Search = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTube)
            if not tracks:
                await interaction.edit_original_response(content="I couldn't find any songs with your query"
                                                                 f" of \"`{query}`.\"")
                return

            # The track to play will be the first result
            track: wavelink.Playable = tracks[0]

            # Get the thumbnail of the track
            video_id = track.uri.replace("https://www.youtube.com/watch?v=", '')
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

            # Add track to queue if a track is already playing
            if player.current:
                # There's probably a more efficient way to go about the embeds, but I'll do it later
                player.queue.put(track)

                # Get time left before track plays
                time_left = player.current.length - player.position
                for x in player.queue:
                    time_left = time_left + x.length
                time_left = time_left - track.length

                # Create the embed
                embed = discord.Embed(
                    title=track.title,
                    url=track.uri,
                    description=f"Song added to queue for channel {player.channel}.",
                    color=discord.Color.from_rgb(1, 162, 186)
                )
                embed.add_field(name="Length:", value=convertDuration(track.length))
                embed.add_field(name="Author:", value=track.author)
                embed.add_field(name="Time Before Track Plays:", value=convertDuration(time_left))
                embed.set_image(url=thumbnail_url)
                await interaction.edit_original_response(embed=embed, content="")

            # Play track immediately if nothing else is playing
            else:
                # Play the track
                await player.play(track)

                # Unpause player, if paused
                await player.pause(False)

                # Update the current_track var
                self.current_track = track

                # Create the embed
                embed = discord.Embed(
                    title=track.title,
                    url=track.uri,
                    description=f"Now playing in {player.channel}.",
                    color=discord.Color.from_rgb(1, 162, 186)
                )
                embed.add_field(name="Length:", value=convertDuration(track.length))
                embed.add_field(name="Author:", value=track.author)
                embed.set_image(url=thumbnail_url)
                await interaction.edit_original_response(embed=embed, content="")

        # Log the usage of the command
        return log.logCommand(interaction)

    # Command: Skip
    @app_commands.command(name="skip", description="Skips to the next song in queue. Stops the player if there are no"
                                                   "songs left.")
    async def skip(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks (is user in vc, is user in same vc as bot, etc.)
        if not await runChecks(interaction):
            return
        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Disable looping, if enabled
        if self.loop_track:
            self.loop_track = False

        # Stop playback if queue is empty
        if player.queue.is_empty:
            # Stop playback
            await player.stop()

            # Remove current playing track var (for loop command)
            # TODO: Test the following. It may cause an error.
            self.current_track = None

            # Respond to command
            await interaction.response.send_message("Playback was stopped because there are no remaining songs in the"
                                                    "queue.", ephemeral=True)

            # Log the command
            return log.logCommand(interaction)

        # Skip current song in queue
        await player.seek(player.current.length)
        # Resume playback if paused
        await player.pause(False)
        await interaction.response.send_message(f"Skipped track **\"{player.current.title}.\"**", ephemeral=True)

    # Command: Stop
    @app_commands.command(name="stop", description="Stops the music player and clears the queue.")
    async def stop(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Disable looping, if enabled
        if self.loop_track:
            self.loop_track = False

        # Resume playback if paused
        await player.pause(False)

        # Empty queue
        player.queue.reset()

        # Stop playback
        await player.stop()

        # Remove current playing track var (for loop command)
        self.current_track = None

        await interaction.response.send_message("Stopped music playback.", ephemeral=True)
        return log.logCommand(interaction)

    # Command: Resume
    @app_commands.command(name="togglepause", description="Toggles whether the player is paused or not.")
    async def togglePause(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Check if the player has an active track
        if not player.current and not player.queue:
            return interaction.response.send_message("There's currently no track playing.", ephemeral=True)

        # Create response message based off of the current pause status
        if player.paused:
            message: str = "Resumed playback."
        else:
            message: str = "Paused the player."

        # Toggle whether the player's paused
        await player.pause(not player.paused)

        # Send notify message
        await interaction.response.send_message(message, ephemeral=True)

        # Log usage of command
        return log.logCommand(interaction)

    # Command: Volume
    @app_commands.command(name="volume", description="Adjusts the volume of the music player."
                                                     " Syntax: \"/volume <volume>\"")
    @app_commands.describe(volume="The volume to set the player to.")
    async def volume(self, interaction: discord.Interaction, volume: int) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction, user_in_different_vc_msg="You can only adjust the volume of the music if"
                                                                     " you're in the same voice channel as me."):
            return

        # Check if volume is in acceptable parameters (or if it's me, so I can set the volume to whatever I want)
        if 1 <= volume <= 100 or interaction.user.id == self.bot.owner_id and volume >= 1:
            # Check if player is running
            player: wavelink.Player = await checkPlayer(interaction)
            if not player:
                return

            # Set volume
            await player.set_volume(volume)
            await interaction.response.send_message(f"Volume of player adjusted to `{volume}`.", ephemeral=True)
            return log.logCommand(interaction)
        else:
            # Send error message
            await interaction.response.send_message("Volume must be between one and 100.", ephemeral=True)
            return

    # Command: Rewind
    @app_commands.command(name="rewind", description="Rewinds the player by a number of seconds. Syntax: \"/rewind "
                                                     "[seconds to rewind]\"")
    @app_commands.describe(rewind_time="The time, in seconds, to rewind. Default is 10 seconds.")
    async def rewind(self, interaction: discord.Interaction, rewind_time: int = 10) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Prevent negative inputs
        if rewind_time < 0:
            return interaction.response.send_message("Rewind time must be a positive integer.", ephemeral=True)

        # Convert the rewind time from seconds to milliseconds
        rewind_time = rewind_time * 1000

        # If the rewind time is greater than time left before current position,
        if rewind_time > int(player.current.length):
            # Restart song playback
            await player.seek(0)
            await interaction.response.send_message("Restarted playback.", ephemeral=True)
            return log.logCommand(interaction)

        # Rewind the player
        position_to_rewind_to = int(player.position - rewind_time)
        await player.seek(position_to_rewind_to)

        # Notify the user
        await interaction.response.send_message(f"Rewound player to position `{convertDuration(position_to_rewind_to)}`.", ephemeral=True)

        # Log the usage
        return log.logCommand(interaction)

    # Command: FastForward
    @app_commands.command(name="fastforward", description="Fast-forwards the player by a number of seconds. Syntax: "
                                                          "\"/fastforward [seconds to fastforward]\"")
    @app_commands.describe(fastforward_time="The time, in seconds, to fast-forward. Default is 10 seconds.")
    async def fastForward(self, interaction: discord.Interaction, fastforward_time: int = 10) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Prevent negative inputs
        if fastforward_time < 0:
            return interaction.response.send_message("Fast-forward time must be a positive integer.", ephemeral=True)

        # Convert the fast-forward time from seconds to milliseconds
        ff_time: int = fastforward_time * 1000

        # If the fastforward time is greater than time left in video...
        if ff_time > int(player.current.length):
            # Skip to the next song in queue. Stop playback if queue is empty
            if player.queue.is_empty:
                await interaction.response.send_message("Stopping playback because there's no more songs in the queue.",
                                                        ephemeral=True)
                await player.stop()
                return log.logCommand(interaction)

            await player.seek(player.current.length * 1000)
            await interaction.response.send_message("Skipping to the next track in queue.", ephemeral=True)
            return log.logCommand(interaction)

        # Fast-forward the player
        position_to_ff_to: int = int(player.position + ff_time)
        await player.seek(position_to_ff_to)

        # Notify the user
        await interaction.response.send_message(f"Fast-forwarded player to position `{convertDuration(position_to_ff_to)}`.",
                                                ephemeral=True)

        # Log the usage
        return log.logCommand(interaction)

    # Command: Seek
    @app_commands.command(name="seek", description="Seek to a position in the currently playing track. "
                                                   "Syntax: \"/seek <position, in format (HH:)MM:SS>\"")
    @app_commands.describe(position="The time to seek to in the track.")
    async def seek(self, interaction: discord.Interaction, position: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # If the input is in the correct format,
        if padTimeFormat(position):
            # Define the time to seek to, which is the input converted to milliseconds
            time_to_seek: int = timeToMilliseconds(padTimeFormat(position))
            # Get the current position of the player, which is in milliseconds
            current_player_time: float = player.position
            # And get the length of the current track in the player
            current_player_length: int = player.current.length

            # If the position is not less than zero or greater than the video length
            if not 0 < time_to_seek < current_player_length:
                return await interaction.response.send_message("The seek-to position must not be longer than the video,"
                                                               " or less than zero.", ephemeral=True)

            # Seek to the position in the current track
            await player.seek(time_to_seek)

            # Add some pretty formatting to the notify message
            if time_to_seek > current_player_time:
                await interaction.response.send_message(f"Fast-forwarded to position `{millisecondsToTime(time_to_seek)}`"
                                                        " in the current track.", ephemeral=True)
            else:
                await interaction.response.send_message("Re-winded the current track to position"
                                                        f" `{millisecondsToTime(time_to_seek)}`.", ephemeral=True)

            # Log command usage
            return log.logCommand(interaction)

        else:
            # Notify that the input is an invalid format
            await interaction.response.send_message("Invalid position to seek to. Check command help page with "
                                                    "`/help seek` for more information.", ephemeral=True)
            return

    # Command: Loop
    @app_commands.command(name="toggleloop", description="Toggle looping the current track.")
    async def toggleLoop(self, interaction: discord.Interaction):
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Check if player is playing a track
        if not player.current:
            return await interaction.response.send_message("No track is currently playing.", ephemeral=True)

        # Toggle track loop
        if not self.loop_track:
            self.loop_track = True
            await interaction.response.send_message("Enabled looping of current track.", ephemeral=True)
        else:
            self.loop_track = False
            await interaction.response.send_message("Disabled looping of current track.", ephemeral=True)

        # Log the command usage
        return log.logCommand(interaction)

    # Command: Shuffle
    @app_commands.command(name="shuffle", description="Shuffle the tracks in the queue.")
    async def shuffle(self, interaction: discord.Interaction):
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # If there is more than 1 item in the queue, shuffle it
        if player.queue and len(player.queue) > 1:
            player.queue.shuffle()
            await interaction.response.send_message("Shuffled queue.", ephemeral=True)

        # Otherwise, inform the user the queue can't be shuffled
        else:
            return await interaction.response.send_message("There are not enough items in the queue to shuffle.",
                                                           ephemeral=True)

        # Log the command usage
        return log.logCommand(interaction)

    # Command: QueueRemove
    @app_commands.command(name="queueremove", description="Remove one or more items from the queue. Syntax: "
                                                          "\"/queueremove <index>\" or \"<index_start:index_end>\"", )
    @app_commands.describe(index="The index of the item to remove from queue, in the format \"index,\" "
                                 "or \"index start:index end.\"")
    async def queueRemove(self, interaction: discord.Interaction, index: str):
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Check if there's anything in the queue
        if not player.queue:
            return await interaction.response.send_message("There are no items in the queue to remove.", ephemeral=True)

        # Check if the index is in the correct format
        if not index.isnumeric() and ':' not in index:
            return await interaction.response.send_message("Invalid format. Accepted formats are `/queueremove <index "
                                                           "of item to remove>` or `/queueremove <index start:index end>`.",
                                                           ephemeral=True)

        # If the index is a singular item to remove,
        if index.isnumeric():
            # If the index is negative or zero, it's invalid
            if int(index) < 1:
                return await interaction.response.send_message("Index must be greater than zero.", ephemeral=True)

            # If the index given is greater than the queue's length, it's invalid
            if int(index) > len(player.queue):
                return await interaction.response.send_message(f"There is no item in the queue with the index of "
                                                               f"{index}. The queue's length is {len(player.queue)}",
                                                               ephemeral=True)

            # Get the item that will be removed and store it in a variable
            track: wavelink.Playable = player.queue.__getitem__(int(index) - 1)

            # Remove the item from the queue
            player.queue.__delitem__(int(index) - 1)

            # Stylize the response message depending on whether there's items remaining in the queue or not
            if not player.queue:
                await interaction.response.send_message(f"Removed item [{track.title}]({track.uri}) from queue. The queue is now empty.",
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(f"Removed item [{track.title}]({track.uri}) from queue.",
                                                        ephemeral=True)

        # Otherwise, it's start index:end index format
        else:
            # Split the string at the colon
            indexes: list = index.split(':')

            # If there's more than two items in the indexes list, it's an invalid format
            if len(indexes) != 2:
                return await interaction.response.send_message("Invalid format. Accepted formats are `/queueremove "
                                                               "<index of item to remove>` or `/queueremove <index "
                                                               "start:index end>`.", ephemeral=True)

            # If either of the items are not numeric, it's an invalid format
            for x in indexes:
                if not x.isnumeric():
                    return await interaction.response.send_message(
                        "Invalid format. Accepted formats are `/queueremove <index "
                        "of item to remove>` or `/queueremove <index start:index end>`.", ephemeral=True)

            # To make life easier, convert the indexes to integers
            indexes: list[int] = [int(x) for x in indexes]

            # If the first index is less than one, it's an invalid format
            if indexes[0] < 1:
                return await interaction.response.send_message("Starting index must be greater than zero.",
                                                               ephemeral=True)

            # If either of the indexes are greater than the length of the queue, it's an invalid format
            for x in indexes:
                if x > len(player.queue):
                    return await interaction.response.send_message("Indexes must be less than or equal to the length "
                                                                   "of the queue.", ephemeral=True)

            # If the starting index is greater than the ending index, it's an invalid format
            if indexes[0] > indexes[1]:
                return await interaction.response.send_message("The starting index must be less than the ending index.",
                                                               ephemeral=True)

            # Create a variable to store the count of items removed from the queue
            count: int = 0
            # For every number between starting index and ending index, remove the index from queue. This is reversed
            # to prevent the queue index changing while items are being removed.
            for x in reversed(range(int(indexes[0]), int(indexes[1]) + 1)):
                # Delete the item in queue
                player.queue.__delitem__(x - 1)
                # Add to the count variable
                count = count + 1

            # Send notifying message, with stylization
            if count == 1:
                await interaction.response.send_message(f"Removed one item from queue.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Removed {count} items from queue.", ephemeral=True)

        # Log the command usage
        return log.logCommand(interaction)

    # Command: PlayerInfo
    @app_commands.command(name="playerinfo", description="Shows information regarding the current track and queue.")
    async def playerInfo(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Check if player is playing any tracks
        if not player.current:
            return await interaction.response.send_message("No track is currently playing, and the queue is empty.", ephemeral=True)

        # Create vars
        video_id = player.current.uri.replace("https://www.youtube.com/watch?v=", '')
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        # Create the info embed
        embed = discord.Embed(
            title=f'Current Track:',
            description=f'**{player.current.title}**',
            color=discord.Color.from_rgb(1, 162, 186),
        )
        embed.add_field(name='Track Length:', value=millisecondsToTime(player.current.length))
        embed.add_field(name='Track Position:', value=millisecondsToTime(player.position))
        embed.add_field(name='Author:', value=player.current.author)
        embed.add_field(name='URL:', value=player.current.uri, inline=False)
        embed.add_field(name='Current Queue Length:', value=len(player.queue))
        embed.add_field(name='Volume:', value=player.volume)
        embed.add_field(name='Looping:', value=("Enabled" if self.loop_track else "Disabled"))
        embed.set_image(url=thumbnail_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log command usage
        return log.logCommand(interaction)

    # Command: QueueInfo
    @app_commands.command(name="queuelist", description="Shows a list of items in the queue. "
                                                        "Syntax: \"/queuelist (page)\"")
    @app_commands.describe(page="The page of the queue list to show. Defaults to one.")
    async def queueList(self, interaction: discord.Interaction, page: int = 1) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Check if the queue is empty
        if not player.queue:
            return await interaction.response.send_message("The queue is currently empty.", ephemeral=True)

        # Create a var containing the maximum amount of pages, which is the queue length divided by 5 with no
        # remainder, plus one, unless the length of the queue is 5 exactly, then it's hard set to one
        max_pages: int = (len(player.queue) // 5) + 1 if len(player.queue) != 5 else 1

        # Check if the given page number is greater than the maximum amount of pages
        if page > max_pages:
            return await interaction.response.send_message(
                f"The input page number {page} is higher than the available amount of pages, {max_pages}.",
                ephemeral=True)

        # Set the embed title to include the page number if the queue's longer than 5, otherwise don't include it
        embed_title: str = f"Queue - Page {page}" if len(player.queue) > 5 else "Queue"

        # Create the embed
        embed = discord.Embed(
            title=embed_title,
            # Some spaghetti stylization code
            description=f"There are currently {len(player.queue)} tracks in queue." if len(player.queue) > 1 else "There is currently one track in queue.",
            color=discord.Color.from_rgb(1, 162, 186)
        )

        # Loop through the first five items in queue, adding each to the embed
        for i in range((page - 1) * 5, min(page * 5, len(player.queue))):
            # Add the item to the embed
            embed.add_field(
                name=f"Track {i + 1}:",
                value=f"[{player.queue[i].title}]({player.queue[i].uri})",
                inline=False
            )

        # Set the footer to show current page, and max pages
        embed.set_footer(text=f"Page {str(page)} of {str(max_pages)}")

        # Send the list
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log command usage
        return log.logCommand(interaction)

    # Command: SkipTo
    @app_commands.command(name="skipto", description="Skip to a specific song in queue.")
    @app_commands.describe(index="The index of the song you want to skip to. You can get this using the /queuelist "
                                 "command.")
    @app_commands.describe(remove_preceding_songs="Whether you want to remove all songs preceding the specified song "
                                                  "in the queue.")
    async def skipTo(self, interaction: discord.Interaction, index: int, remove_preceding_songs: bool = False):
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction):
            return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        # Skip current song, if playing
        await player.seek(player.current.length * 1000)

        # Resume playback if paused
        await player.pause(False)

        # If remove preceding songs, remove all songs before the specified song, including the specified song
        if remove_preceding_songs:
            track_to_seek_to: wavelink.Playable = player.queue.get_at(index - 1)

            # Reversing this so the indexes don't change as items get deleted
            for x in reversed(range(0, index - 1)):
                player.queue.delete(x)

            # Put the specified track at the front of the queue
            player.queue.put_at(0, track_to_seek_to)

            # Send notifying message
            await interaction.response.send_message(
                f"Skipped to track [{track_to_seek_to.title}]({track_to_seek_to.uri}), removing preceeding items in queue.", ephemeral=True)

        # Otherwise, just skip to the song without removing anything from queue
        else:
            # Get the track in the queue to skip to
            track_to_seek_to: wavelink.Playable = player.queue.get_at(index - 1)

            # Delete the track from the queue
            player.queue.delete(index)

            # Put said track in the front of the queue
            player.queue.put_at(0, track_to_seek_to)

            # Send notifying message
            await interaction.response.send_message(
                f"Skipped to track [{track_to_seek_to.title}]({track_to_seek_to.uri}).", ephemeral=True)

        # Log command usage
        return log.logCommand(interaction)


# Cog setup hook
async def setup(bot):
    await bot.add_cog(Music(bot))
