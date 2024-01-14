# Imports
import discord
from discord import app_commands
from discord.ext import commands, tasks
import wavelink
import datetime
import random
import re
from utils.logger import Log, LogAndPrint

# TODO: Add cool-downs to commands to prevent spamming(which may or may not work)
# TODO: Create limit on queue size for player
# TODO: Add auto-compression to prevent people from playing deafening tracks and blowing others' ears out (I think
#  Wavelink has audio leveling systems I can use)
# TODO: Add a command to go to specific song in queue
# TODO: Add a queue shuffle command
# TODO: Find a way to prevent people from playing videos with blocked words in the title

# Create object of Log and LogAndPrint class
log = Log()
logandprint = LogAndPrint()


# The following three functions were written by ChatGPT. I know; shut up.
def convertDuration(milliseconds) -> str:
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


def checkIfTimeFormatValid(input_str) -> bool:
    # Regular expression patterns for HH:MM:SS and MM:SS formats
    hh_mm_ss_pattern = r'^\d{2}:\d{2}:\d{2}$'
    mm_ss_pattern = r'^\d{2}:\d{2}$'

    # Check if the input matches either pattern
    if re.match(hh_mm_ss_pattern, input_str) or re.match(mm_ss_pattern, input_str):
        return True
    else:
        return False


# TODO: Add data type declarations to hh_mm... and mm_ss.. vars
def timeToMilliseconds(time_str) -> int:
    # Regular expression pattern for HH:MM:SS and MM:SS formats
    hh_mm_ss_pattern = r'^(\d{2}):(\d{2}):(\d{2})$'
    mm_ss_pattern = r'^(\d{2}):(\d{2})$'
    logandprint.debug(f'Type: {type(hh_mm_ss_pattern)}, {type(mm_ss_pattern)}')

    # Check if the input matches either pattern
    hh_mm_ss_match = re.match(hh_mm_ss_pattern, time_str)
    mm_ss_match = re.match(mm_ss_pattern, time_str)

    if hh_mm_ss_match:
        hours, minutes, seconds = map(int, hh_mm_ss_match.groups())
        total_seconds = hours * 3600 + minutes * 60 + seconds
    elif mm_ss_match:
        minutes, seconds = map(int, mm_ss_match.groups())
        total_seconds = minutes * 60 + seconds
    # TODO: Maybe remove the following, because I don't think error handling is required for this function.
    else:
        raise ValueError(f'Invalid time format in timeToMilliseconds function in {__name__}. Use HH:MM:SS or MM:SS.')

    # Convert total seconds to milliseconds
    milliseconds: int = total_seconds * 1000
    return milliseconds


# Function that runs basic checks for music-related commands
# Checks if user is in VC, bot is in VC, player is running, etc.
async def runChecks(interaction: discord.Interaction, bot_not_in_vc_msg=None, user_not_in_vc_msg=None,
                    user_in_different_vc_msg=None) -> bool:
    user_vc = interaction.user.voice
    bot_vc = interaction.guild.voice_client

    if not bot_not_in_vc_msg:
        bot_not_in_vc_msg: str = 'I am not connected to a voice channel.'

    if not user_not_in_vc_msg:
        user_not_in_vc_msg: str = 'You must be connected to the same channel as me to perform this action.'

    if not user_in_different_vc_msg:
        user_in_different_vc_msg: str = 'You must be in the same channel as me to perform this action.'

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

    return True


# Not defining a return value for this function because I think it would break
async def checkPlayer(interaction: discord.Interaction, custom_message: str = None):
    try:
        player: wavelink.Player = interaction.guild.voice_client
        return player
    except Exception as e:
        # TODO: Remove the following (it's here for testing purposes)
        logandprint.debug(f'This is the error output for the try/except in the checkPlayer function in the music.py '
                          f'cog. The error output is: {e}')
        if not custom_message:
            custom_message: str = 'No music player is currently running.'
        await interaction.response.send_message(custom_message, ephemeral=True)
        return None


class QueueInfoUI(discord.ui.View):
    # Vars
    player: wavelink.Player
    queue: list
    nav_buttons_needed: bool
    embed_title: str = 'Queue - Page 1'
    current_page: int
    current_position: int

    # TODO: Fix this class because the init function can't be async but the class needs to be asynchronous

    # Class init function
    def __init__(self, player: wavelink.Player, interaction: discord.Interaction):
        # Run init function for parent class(discord.ui.View)
        super().__init__()

        # Vars
        player_queue = player.queue
        self.player = player

        # Reset existing(if any) vars
        self.nav_buttons_needed = False
        self.queue = []
        self.current_page = 0
        self.current_position = 0

        # Convert the player queue to another list with Discord-recognizable links with the names and URLs of the tracks
        for x in player_queue:
            self.queue.append(f'[{x.title}]({x.uri})')

        # If the queue is shorter than 5 items, remove the navigation buttons
        if len(self.queue) <= 5:
            self.remove_item(self.previous)
            self.remove_item(self.next)
            self.embed_title = 'Queue'
        else:
            self.current_page = 1

    # Update message
    async def updateMessage(self, interaction: discord.Interaction, embed: discord.Embed):
        ...
        #await interaction.response.

    async def generateFirstEmbed(self, interaction: discord.Interaction):
        print(interaction.id)

        # Create the embed
        embed = discord.Embed(
            title=self.embed_title,
            description=f'There are currently {len(self.queue)} tracks in queue.',
            color=discord.Color.from_rgb(1, 162, 186)
        )

        while self.current_position < 5:
            embed.add_field(name=f'Track {self.current_position + 1}:', value=self.queue[self.current_position],
                            inline=False)
            self.current_position += 1

            # If the current count is greater than queue length
            if self.current_position >= len(self.queue):
                break
        self.current_page += 1

        await self.updateMessage(interaction, embed)

    async def generateEmbed(self, interaction: discord.Interaction, direction: int = 1, page: int = 0):
        # Set/update vars
        queue = self.queue
        embed_title = self.embed_title

        if page == 0:
            self.current_position = 0
            self.current_page = 1

        # Change embed title if there are multiple pages
        if self.current_page > 0:
            embed_title = f'Queue - Page {self.current_page}'
            self.current_page = self.current_page + direction

        # Create the embed
        embed = discord.Embed(
            title=embed_title,
            description=f'There are currently {len(queue)} tracks in queue.',
            color=discord.Color.from_rgb(1, 162, 186)
        )

        # Remove previous button if on first page
        if self.current_page == 1:
            self.remove_item(self.previous)
            embed.add_field(name='Current Track:', value=f'[{self.player.current.title}]({self.player.current.uri})')

        print(f'''
Current Page: {self.current_page}
Current Position: {self.current_position}
Current Direction: {direction}
''')

        # Add a few items in the playlist to the embed
        if direction == 1:
            limit = self.current_position + 5
            while self.current_position < limit:
                embed.add_field(name=f'Track {self.current_position + 1}:', value=queue[self.current_position], inline=False)
                self.current_position += 1

                # If the current count is greater than queue length
                if self.current_position >= len(queue):
                    break
            self.current_page += 1
        else:
            limit = self.current_position - 5
            while self.current_position < limit:
                embed.add_field(name=f'Track {self.current_position + 1}:', value=queue[self.current_position], inline=False)
                self.current_position -= 1

                # If the current count is greater than queue length
                if self.current_position <= len(queue):
                    break
            self.current_page -= 1

        # Send the embed by updating the original message
        await interaction.response.edit_message(embed=embed)
        print('amogus')

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        await self.generateEmbed(interaction, -1)
        #await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        await self.generateEmbed(interaction, 1)
        #embed = discord.Embed(title='Next Embed', description='ipsum dolor')
        #await interaction.response.edit_message(embed=embed)


class Music(commands.Cog, description="Commands relating to the voice chat music player."):
    def __init__(self, bot) -> None:
        self.bot = bot

    # Vars
    loop_track: bool = False
    current_track: wavelink.YouTubeTrack = None

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
        should_leave = False

        # Loop through every guild to get connected voice clients
        for guild in self.bot.guilds:
            voice_client = guild.voice_client
            # If voice client is connected
            if voice_client and voice_client.is_connected():
                # If the bot is the only one present, disconnect
                if len(voice_client.channel.members) == 1:
                    should_leave = True
                try:
                    # Check if player is running, and if it is, disconnect if not in use and clear the queue
                    player: wavelink.Player = voice_client
                    if not player.is_playing() and not player.is_paused():
                        player.queue.reset()
                        should_leave = True
                except:
                    # Disconnect if player isn't running
                    should_leave = True
                if should_leave:
                    # Log message and print to console
                    logandprint.info(f'Leaving {voice_client.channel} due to inactivity.')
                    # Disconnect from VC
                    await voice_client.disconnect()
                    return

        return

    # Run Before Task: Check if connected to voice channel
    @checkIfConnectedToVoiceChannel.before_loop
    async def before_check_if_connected_to_voice_channel(self) -> None:
        # Wait till bot is ready before starting task
        await self.bot.wait_until_ready()
        return

    # Listener: On Track End
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload) -> None:
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
    @app_commands.describe(query='The search term or YouTube video URL to play.')
    async def play(self, interaction: discord.Interaction, *, query: str) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Get user VC
        user_vc = interaction.user.voice

        # Check if user is in VC
        if not user_vc:
            return await interaction.response.send_message('You are not connected to a voice channel.', ephemeral=True)

        # Check if player is already running. If not, create a new player
        if not interaction.client.voice_clients:
            player: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            # If player is running, check if bot is in a different VC than user with music playing
            player: wavelink.Player = interaction.guild.voice_client
            if player.is_playing() and user_vc.channel != interaction.guild.voice_client.channel:
                return await interaction.response.send_message('I am already playing music in another channel.', ephemeral=True)

            # Check if player is not playing music, and user is in different VC
            if not player.is_playing() and not player.is_paused() and user_vc.channel != interaction.guild.voice_client.channel:
                await player.move_to(user_vc.channel)

        # TODO: Do more debugging on playlists support
        # If query is playlist URL
        if 'https://' and 'list=' in query:
            # Error handler in case BOB can't find any playlists matching URL
            try:
                playlist: wavelink.YouTubePlaylist = await wavelink.YouTubePlaylist.search(query)
            except ValueError:
                return await interaction.response.send_message('I couldn\'nt find any playlists matching that URL.', ephemeral=True)

            # Create list of tracks in playlist
            playlist_tracks: list[wavelink.YouTubeTrack] = playlist.tracks
            notify_about_playlist_too_long: bool = False

            # If playlist is too long, update notify var
            if len(playlist_tracks) > 100:
                notify_about_playlist_too_long = True

            # Create selected track int
            selected_track: int = playlist.selected_track
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
                title=f'Playlist: {playlist.name}',
                color=discord.Color.from_rgb(1, 162, 186)
            )

            # Add five items in the playlist to the embed
            limit: int = 5 if len(playlist_tracks) > 5 else len(playlist_tracks)
            i: int = 0
            while i < limit:
                embed.add_field(name=f'Track {i + 1}:', value=f'[{playlist_tracks[i].title}]({playlist_tracks[i].uri})',
                                inline=False)
                i: int = i + 1

            # If playlist is greater than five tracks, add a notifying footer to the embed
            if len(playlist_tracks) > 5:
                embed.set_footer(text=f'And {len(playlist_tracks) - 5} more tracks...')

            # If there's already a song playing:
            if player.is_playing() or player.is_paused():
                # Add all items to queue
                for track in playlist_tracks:
                    player.queue.put(item=track)

                # Set embed description var
                embed_description: str = f'Added {len(playlist_tracks)} songs to queue in channel {player.channel}.'

                # If playlist is too long, change description of embed to notify user
                if notify_about_playlist_too_long:
                    embed_description = embed_description + ' (Playlist size limit is 100 tracks.)'

                # Set the description for the embed
                embed.description = embed_description

                # Send the embed
                await interaction.response.send_message(embed=embed, ephemeral=True)

            else:
                # Play the first track in the list
                await player.play(playlist_tracks[0])

                # Update the current_track var with the now playing track
                self.current_track = playlist_tracks[0]

                # Add all items to queue, excluding the first song(which is the one that will start playing immediately)
                for track in playlist_tracks[1:]:
                    player.queue.put(item=track)

                # Set embed description var
                embed_description: str = f'Now playing [{playlist_tracks[0].title}]({playlist_tracks[0].uri}), and added {len(playlist_tracks) - 1} songs to queue in channel {player.channel}.'

                # If playlist is too long, change description of embed to notify user
                if notify_about_playlist_too_long:
                    embed_description = embed_description + f' (Playlist size limit is 100 tracks.)'

                # Set the description for the embed
                embed.description = embed_description

                # Send the embed
                await interaction.response.send_message(embed=embed, ephemeral=True)

        # Otherwise query is track or search query
        else:
            tracks: list[wavelink.YouTubeTrack] = await wavelink.YouTubeTrack.search(query)
            if not tracks:
                return await interaction.response.send_message(f'I could\'nt find any songs with your query of "`{query}`."', ephemeral=True)

            # The track to play will be the first result
            track: wavelink.YouTubeTrack = tracks[0]
            # Add track to queue if a track is already playing
            if player.is_playing() or player.is_paused():
                # There's probably a more efficient way to go about the embeds, but I'll do it later
                player.queue.put(item=track)

                # Get time left before track plays
                time_left = player.current.duration - player.position
                for x in player.queue:
                    time_left = time_left + x.duration
                time_left = time_left - track.duration

                # Create the embed
                embed = discord.Embed(
                    title=track.title,
                    url=track.uri,
                    description=f'Song added to queue for channel {player.channel}.',
                    color=discord.Color.from_rgb(1, 162, 186)
                )
                embed.add_field(name='Length:', value=convertDuration(track.duration))
                embed.add_field(name='Author:', value=track.author)
                embed.add_field(name='Time Before Track Plays:', value=convertDuration(time_left))
                embed.set_image(url=track.thumb)
                await interaction.response.send_message(embed=embed, ephemeral=True)

            # Play track immediately if nothing else is playing
            else:
                # Play the track
                await player.play(track)

                # Update the current_track var
                self.current_track = track

                # Create the embed
                embed = discord.Embed(
                    title=track.title,
                    url=track.uri,
                    description=f'Now playing in {player.channel}.',
                    color=discord.Color.from_rgb(1, 162, 186)
                )
                embed.add_field(name='Length:', value=convertDuration(track.duration))
                embed.add_field(name='Author:', value=track.author)
                embed.set_image(url=track.thumb)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log the usage of the command
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: Skip
    @app_commands.command(name='skip', description='Skips to the next song in queue. Stops the player if there are no songs left.')
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
            await interaction.response.send_message('Playback was stopped because there are no remaining songs in the queue.', ephemeral=True)

            # Log the command
            return log.logCommand(interaction.user, interaction.command.name)

        # Skip current song in queue
        await player.seek(player.current.duration * 1000)
        if player.is_paused():
            await player.resume()
        await interaction.response.send_message(f'Skipped track **"{player.current.title}."**', ephemeral=True)

    # Command: Stop
    @app_commands.command(name='stop', description='Stops the music player and clears the queue.')
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

        # Stop playback
        await player.stop()

        # Empty queue
        player.queue.reset()

        # Remove current playing track var (for loop command)
        self.current_track = None

        await interaction.response.send_message('Stopped music playback.', ephemeral=True)
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: Pause
    @app_commands.command(name='pause', description='Pauses the player.')
    async def pause(self, interaction: discord.Interaction) -> None:
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

        # Check if paused
        if player.is_paused():
            # Don't log the command because it makes no difference
            await interaction.response.send_message('The player is already paused.', ephemeral=True)
            return

        # Pause the player
        await player.pause()
        await interaction.response.send_message('Playback paused.', ephemeral=True)
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: Resume
    @app_commands.command(name='resume', description='Resumes the player, if paused.')
    async def resume(self, interaction: discord.Interaction) -> None:
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

        # Check if paused
        if not player.is_paused():
            await interaction.response.send_message('The player is currently not paused.', ephemeral=True)
            return
        # Resume the player
        await player.resume()
        await interaction.response.send_message('Playback resumed.', ephemeral=True)
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: Volume
    @app_commands.command(name='volume', description='Adjusts the volume of the music player. Syntax: "/volume <volume>"')
    @app_commands.describe(volume='The volume to set the player to.')
    async def volume(self, interaction: discord.Interaction, volume: int) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # Run checks
        if not await runChecks(interaction, user_in_different_vc_msg='You can only adjust the volume of the music if you\'re in the same voice channel as me.'):
            return

        # Check if volume is in acceptable parameters
        if 1 <= volume <= 100:
            # Check if player is running
            player: wavelink.Player = await checkPlayer(interaction)
            if not player:
                return

            # Set volume
            await player.set_volume(volume)
            await interaction.response.send_message(f'Volume of player adjusted to `{volume}`.', ephemeral=True)
            return log.logCommand(interaction.user, interaction.command.name)
        else:
            # Send error message
            await interaction.response.send_message('Volume must be between one and 100.', ephemeral=True)
            return

    # Command: Rewind
    @app_commands.command(name='rewind', description='Rewinds the player by a number of seconds. Syntax: "/rewind [seconds to rewind]"')
    @app_commands.describe(rewind_time='The time, in seconds, to rewind.')
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

        rewind_time = rewind_time * 1000
        # If the rewind time is greater than time left before current position...
        if rewind_time > int(player.position) or rewind_time < 0:
            # Restart song playback
            await player.seek(0)
            await interaction.response.send_message('Restarted playback.', ephemeral=True)
            return log.logCommand(interaction.user, interaction.command.name)
        position_to_rewind_to = int(player.position - rewind_time)
        await player.seek(position_to_rewind_to)
        await interaction.response.send_message(f'Rewound player to position `{convertDuration(position_to_rewind_to)}`.', ephemeral=True)
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: FastForward
    @app_commands.command(name='fastforward', description='Fast-forwards the player by a number of seconds. Syntax: "/fastforward [seconds to fastforward]"')
    @app_commands.describe(fastforward_time='The time, in seconds, to fast-forward.')
    async def fastforward(self, interaction: discord.Interaction, fastforward_time: int = 10) -> None:
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

        ff_time = fastforward_time * 1000
        # If the fastforward time is greater than time left in video...
        if ff_time > int(player.position) or ff_time < 0:
            # Skip to the next song in queue. Stop playback if queue is empty
            if player.queue.is_empty:
                await interaction.response.send_message('Stopping playback because there\'s no more songs in the queue.', ephemeral=True)
                await player.stop()
                return log.logCommand(interaction.user, interaction.command.name)

            await player.play(player.queue.get())
            await interaction.response.send_message('Skipping to next song in queue.', ephemeral=True)
            return log.logCommand(interaction.user, interaction.command.name)

        position_to_ff_to = int(player.position + ff_time)
        await player.seek(position_to_ff_to)
        await interaction.response.send_message(f'Fast-forwarded player to position `{convertDuration(position_to_ff_to)}`.', ephemeral=True)
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: Seek
    @app_commands.command(name='seek', description='Seek to a position in the currently playing track. Syntax: "/seek <position, in format (HH:)MM:SS>"')
    @app_commands.describe(position='The time to seek to in the track.')
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

        # If the input is in the correct format
        if checkIfTimeFormatValid(position):
            # Define vars
            time_to_seek = timeToMilliseconds(position)
            current_player_time = player.position
            current_player_length = player.current.length

            # If the position is not less than zero or greater than the video length
            if not 0 <= time_to_seek < current_player_length:
                await interaction.response.send_message('The seek-to position must not be longer than the video, or less than zero.', ephemeral=True)
                return

            # Seek to the position, and send a corresponding message
            await player.seek(time_to_seek)
            if time_to_seek > current_player_time:
                await interaction.response.send_message(f'Fast-forwarded to `{position}` in video.', ephemeral=True)
            else:
                await interaction.response.send_message(f'Re-winded video to `{position}`.', ephemeral=True)

            # Log command usage
            return log.logCommand(interaction.user, interaction.command.name)

        else:
            await interaction.response.send_message('Invalid position to seek to. Check command help page with '
                           '"/help seek" for more information.', ephemeral=True)
            return

    # Command: Loop
    @app_commands.command(name='loop', description='Loops the currently playing track.')
    async def loop(self, interaction: discord.Interaction):
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
            return await interaction.response.send_message('No track is currently playing.', ephemeral=True)

        # Toggle track loop
        if not self.loop_track:
            self.loop_track = True
            await interaction.response.send_message('Enabled looping of current track.', ephemeral=True)
        else:
            self.loop_track = False
            await interaction.response.send_message('Disabled looping of current track.', ephemeral=True)

        # Log the command usage
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: Shuffle
    @app_commands.command(name='shuffle', description='Shuffle the tracks in the queue.')
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
            random.shuffle(player.queue)
            await interaction.response.send_message('Shuffled queue.', ephemeral=True)

        # Otherwise, inform the user the queue can't be shuffled
        else:
            return interaction.response.send_message('There are not enough items in the queue to shuffle.', ephemeral=True)

        # Log the command usage
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: PlayerInfo
    @app_commands.command(name='playerinfo', description='Shows information regarding the current track and queue.')
    async def playerinfo(self, interaction: discord.Interaction) -> None:
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

        # Check if player is running
        if not player.current:
            return await interaction.response.send_message('No track is currently playing, and the queue is empty.', ephemeral=True)

        # Create vars
        video_id = player.current.uri.replace('https://www.youtube.com/watch?v=', '')
        thumbnail_url = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'

        # Get loop status
        if self.loop_track:
            is_looping = 'Enabled'
        else:
            is_looping = 'Disabled'

        # Create the info embed
        embed = discord.Embed(
            title=f'Current Track:',
            description=f'**{player.current.title}**',
            color=discord.Color.from_rgb(1, 162, 186),
        )
        embed.add_field(name='Track Length:', value=convertDuration(player.current.duration))
        embed.add_field(name='Track Position:', value=convertDuration(player.position))
        embed.add_field(name='Author:', value=player.current.author)
        embed.add_field(name='URL:', value=player.current.uri, inline=False)
        embed.add_field(name='Current Queue Length:', value=len(player.queue))
        embed.add_field(name='Volume:', value=player.volume)
        embed.add_field(name='Looping:', value=is_looping)
        embed.set_image(url=thumbnail_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log command usage
        return log.logCommand(interaction.user, interaction.command.name)

    # TODO: Finish queue info command
    # TODO: Maybe temporarily abandon the fancy QueueInfo UI for a less advanced system that allows you to specify a
    #  page number in the command
    # Command: QueueInfo
    @app_commands.command(name='queueinfo', description='Shows the current track queue.')
    async def queueinfo(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        return await interaction.response.send_message('This command is still a work-in-progress.', ephemeral=True)

        # Run checks
        #if not await runChecks(interaction):
        #    return

        # Check if player is running
        player: wavelink.Player = await checkPlayer(interaction)
        if not player:
            return

        if len(player.queue) < 1:
            return await interaction.response.send_message('The queue is currently empty.', ephemeral=True)

        view = QueueInfoUI(player=player, interaction=interaction)
        await view.generateFirstEmbed(interaction=interaction)
        await interaction.response.send_message('Generating queue list...', view=view)

        # Log command usage
        return log.logCommand(interaction.user, interaction.command.name)

    # Command: Move
    @app_commands.command(name='move', description='Move the bot from one VC to another. Only usable by staff.')
    @discord.app_commands.checks.has_permissions(move_members=True)
    async def move(self, interaction: discord.Interaction) -> None:
        # Check if maintenance mode is on
        if self.bot.maintenance_mode:
            return

        # I'm not using the runChecks function here because the conditions are different
        user_vc = interaction.user.voice
        bot_vc = interaction.guild.voice_client

        # Bot not connected to VC
        if not bot_vc:
            return await interaction.response.send_message('I am not connected to a voice channel.', ephemeral=True)

        # User not connected to VC
        if not user_vc:
            return await interaction.response.send_message('You must be connected to a voice channel to use this command.',
                                                           ephemeral=True)

        if user_vc.channel == bot_vc.channel:
            return await interaction.response.send_message('I\'m already in the same channel as you.', ephemeral=True)

        # Try to get the player
        player: wavelink.Player = await checkPlayer(interaction, 'No music player is currently running. Use the play '
                                                                 'command to play music in your current voice chat.')
        if not player:
            return

        await player.move_to(user_vc.channel)
        await interaction.response.send_message(f'Moved to voice channel "{user_vc.channel.name}."', ephemeral=True)

        # Log command usage
        return log.logCommand(interaction.user, interaction.command.name)


# Cog setup hook
async def setup(bot):
    await bot.add_cog(Music(bot))
