# Imports
import discord
from discord.ext import commands, tasks
import wavelink
from wavelink.ext import spotify  # Spotify not supported, but maybe eventually...
import datetime
import re
from utils.logger import logCommand, log

# TODO: Add move command, only usable by admins, to move bot from one VC to another
# TODO: Add check to voice client listener to see if bot is all alone in VC, even if music is playing


# The following three functions were written by ChatGPT. I know; shut up.
def convertDuration(milliseconds):
    # Convert milliseconds to seconds
    seconds = milliseconds / 1000

    # Create a timedelta object representing the duration
    duration = datetime.timedelta(seconds=seconds)

    # Format the duration as HH:MM:SS, even if hours exceed 99
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    if int(hours) == 0:
        formatted_time = f"{int(minutes):02}:{int(seconds):02}"
    else:
        formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    return formatted_time


def checkIfTimeFormatValid(input_str):
    # Regular expression patterns for HH:MM:SS and MM:SS formats
    hh_mm_ss_pattern = r'^\d{2}:\d{2}:\d{2}$'
    mm_ss_pattern = r'^\d{2}:\d{2}$'

    # Check if the input matches either pattern
    if re.match(hh_mm_ss_pattern, input_str) or re.match(mm_ss_pattern, input_str):
        return True
    else:
        return False


def timeToMilliseconds(time_str):
    # Regular expression pattern for HH:MM:SS and MM:SS formats
    hh_mm_ss_pattern = r'^(\d{2}):(\d{2}):(\d{2})$'
    mm_ss_pattern = r'^(\d{2}):(\d{2})$'

    # Check if the input matches either pattern
    hh_mm_ss_match = re.match(hh_mm_ss_pattern, time_str)
    mm_ss_match = re.match(mm_ss_pattern, time_str)

    if hh_mm_ss_match:
        hours, minutes, seconds = map(int, hh_mm_ss_match.groups())
        total_seconds = hours * 3600 + minutes * 60 + seconds
    elif mm_ss_match:
        minutes, seconds = map(int, mm_ss_match.groups())
        total_seconds = minutes * 60 + seconds
    else:
        raise ValueError("Invalid time format. Use HH:MM:SS or MM:SS.")

    # Convert total seconds to milliseconds
    milliseconds = total_seconds * 1000
    return milliseconds


async def runChecks(ctx, BotNotInVC=None, UserNotInVCMsg=None, UserInDifferentVCMsg=None):
    user_vc = ctx.author.voice
    bot_vc = ctx.voice_client

    if not BotNotInVC:
        BotNotInVC = 'I am not connected to a voice channel.'

    if not UserNotInVCMsg:
        UserNotInVCMsg = 'You must be connected to the same channel as me to perform this action.'

    if not UserInDifferentVCMsg:
        UserInDifferentVCMsg = 'You must be in the same channel as me to perform this action.'

    # Bot not connected to VC
    if not bot_vc:
        return await ctx.send(BotNotInVC)

    # User not connected to VC
    if not user_vc:
        return await ctx.send(UserNotInVCMsg)

    # User in different VC
    if user_vc.channel != bot_vc.channel:
        return await ctx.send(UserInDifferentVCMsg)


async def checkPlayer(ctx):
    try:
        player: wavelink.Player = ctx.voice_client
        return player
    except:
        await ctx.send('No music player is currently running.')
        return None


class Music(commands.Cog, description="Commands relating to the voice chat music player."):
    def __init__(self, bot):
        self.bot = bot

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')
        self.checkIfConnectedToVoiceChannel.start()
        print('Started background task "Check If Connected to Voice Channel."')

    # Task: Check if connected to voice channel
    @tasks.loop(minutes=5.0)
    async def checkIfConnectedToVoiceChannel(self):
        # Probably a better way to go about the disconnect system

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
                    # Disconnect, and log it to file and console
                    await voice_client.disconnect()
                    # Making a var of this for optimization
                    message = f'Leaving {voice_client.channel} due to inactivity.'
                    print(message)
                    return log('info', message)
        return

    # Run Before Task: Check if connected to voice channel
    @checkIfConnectedToVoiceChannel.before_loop
    async def before_check_if_connected_to_voice_channel(self):
        await self.bot.wait_until_ready()

    # Listener: On Track End
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        player: wavelink.Player = payload.player
        if not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)

    # Command: Play
    @commands.command(help='Play a song in a voice chat. Syntax: "!play <URL or search term>"'
                           'Currently only YouTube URLs and searches are supported.')
    async def play(self, ctx, *, query: str) -> None:
        user_vc = ctx.author.voice

        if not user_vc:
            return await ctx.send('You are not connected to a voice channel.')

        if not ctx.voice_client:
            player: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            player: wavelink.Player = ctx.voice_client
            if player.is_playing() and user_vc.channel != ctx.voice_client.channel:
                return await ctx.send('I am already playing music in another channel.')

        #test_playlist: wavelink.YouTubePlaylist = wavelink.YouTubePlaylist(query)
        #print(test_playlist)
        tracks: list[wavelink.YouTubeTrack] = await wavelink.YouTubeTrack.search(query)
        if not tracks:
            return await ctx.send(f'I could\'nt find any songs with your query of "`{query}`."')

        track: wavelink.YouTubeTrack = tracks[0]
        # Add track to queue
        if player.is_playing():
            # There's probably a more efficient way to go about the embeds, but I'll do it later
            player.queue.put(item=track)

            # Get time left before song plays
            time_left = player.current.duration - player.position
            for x in player.queue:
                time_left = time_left + x.duration
            time_left = time_left - track.duration

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
            await ctx.send(embed=embed)

        # Play track immediately
        else:
            await player.play(track)
            embed = discord.Embed(
                title=track.title,
                url=track.uri,
                description=f'Now playing in {player.channel}.',
                color=discord.Color.from_rgb(1, 162, 186)
            )
            embed.add_field(name='Length:', value=convertDuration(track.duration))
            embed.add_field(name='Author:', value=track.author)
            embed.set_image(url=track.thumb)
            await ctx.send(embed=embed)

        logCommand(ctx.author, 'play')

    # Command: Skip
    @commands.command(help='Skips to the next song in queue. Stops the player if there are no songs left.')
    async def skip(self, ctx):
        # Run checks (is user in vc, is user in same vc as bot, etc.)
        await runChecks(ctx)
        # Check if player is running
        player: wavelink.Player = await checkPlayer(ctx)
        if not player:
            return

        # Stop playback if queue is empty
        if player.queue.is_empty:
            await player.stop()
            # Log the command
            logCommand(ctx.author, 'skip')
            return await ctx.send('Playback was stopped because there are no remaining songs in the queue.')
        # Skip current song in queue
        await player.seek(player.current.duration * 1000)
        if player.is_paused():
            await player.resume()
        logCommand(ctx.author, 'skip')

    # Command: Stop
    @commands.command(help='Stops the music player and clears the queue.')
    async def stop(self, ctx):
        # Run checks
        await runChecks(ctx)

        # Check if player is running
        player: wavelink.Player = await checkPlayer(ctx)
        if not player:
            return
        # Stop playback.
        await player.stop()
        player.queue.reset()
        await ctx.send('Stopped music playback.')
        logCommand(ctx.author, 'stop')

    # Command: Pause
    @commands.command(help='Pauses the player.')
    async def pause(self, ctx):
        # Run checks
        await runChecks(ctx)

        # Check if player is running
        player: wavelink.Player = await checkPlayer(ctx)
        if not player:
            return

        # Check if paused
        if player.is_paused():
            # Don't log the command because it makes no difference
            return await ctx.send('The player is already paused.')
        # Pause the player
        await player.pause()
        await ctx.send('Playback paused.')
        logCommand(ctx.author, 'pause')

    # Command: Resume
    @commands.command(help='Resumes the player, if paused.')
    async def resume(self, ctx):
        await runChecks(ctx)
        # Check if player is running
        player: wavelink.Player = await checkPlayer(ctx)
        if not player:
            return

        # Check if paused
        if not player.is_paused():
            return await ctx.send('The player is currently not paused.')
        # Resume the player
        await player.resume()
        await ctx.send('Playback resumed.')
        logCommand(ctx.author, 'resume')

    # Command: Volume
    @commands.command(help='Adjusts the volume of the music player. Syntax: "!volume <volume>"')
    async def volume(self, ctx, volume: int):
        await runChecks(ctx, UserInDifferentVCMsg='You can only adjust the volume of the music if you\'re in the same voice channel as me.')

        # Check if volume is in acceptable parameters
        if 1 <= volume <= 100:
            # Check if player is running
            player: wavelink.Player = await checkPlayer(ctx)
            if not player:
                return

            # Set volume
            await player.set_volume(volume)
            await ctx.send(f'Volume of player adjusted to `{volume}`.')
            logCommand(ctx.author, 'volume')
        else:
            # Send error message
            return await ctx.send('Volume must be between one and 100.')

    @commands.command(help='Rewinds the player by a number of seconds. Default is 10 seconds. '
                           'Syntax: "!rewind [seconds to rewind]"')
    async def rewind(self, ctx, rewind_time: int = 10):
        await runChecks(ctx)
        # Check if player is running
        player: wavelink.Player = await checkPlayer(ctx)
        if not player:
            return

        rewind_time = rewind_time * 1000
        # If the rewind time is greater than time left before current position...
        if rewind_time > int(player.position) or rewind_time < 0:
            # Restart song playback
            await player.seek(0)
            await ctx.send('Restarted playback.')
            return logCommand(ctx.author, 'rewind')
        position_to_rewind_to = int(player.position - rewind_time)
        await player.seek(position_to_rewind_to)
        await ctx.send(f'Rewound player to position `{convertDuration(position_to_rewind_to)}`.')

    @commands.command(help='Fast-forwards the player by a number of seconds. Default is 10 seconds. '
                           'Syntax: "!fastforward [seconds to fastforward]"')
    async def fastforward(self, ctx, fastforward_time: int = 10):
        await runChecks(ctx)
        # Check if player is running
        player: wavelink.Player = await checkPlayer(ctx)
        if not player:
            return

        ff_time = fastforward_time * 1000
        # If the fastforward time is greater than time left in video...
        if ff_time > int(player.position) or ff_time < 0:
            # Skip to the next song in queue. Stop playback if queue is empty
            if player.queue.is_empty:
                await ctx.send('Stopping playback because there\'s no more songs in the queue.')
                await player.stop()
                return logCommand(ctx.author, 'fastforward')

            await player.play(player.queue.get())
            await ctx.send('Skipping to next song in queue.')
            return await logCommand(ctx.author, 'fastforward')

        position_to_ff_to = int(player.position + ff_time)
        await player.seek(position_to_ff_to)
        await ctx.send(f'Fast-forwarded player to position `{convertDuration(position_to_ff_to)}`.')

    @commands.command(help='Seek a specific position in the currently playing track. Syntax: '
                           '"!seek <position to move to, in format (HH:)MM:SS. HH optional.>"')
    async def seek(self, ctx, position: str):
        await runChecks(ctx)
        # Check if player is running
        player: wavelink.Player = await checkPlayer(ctx)
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
                return await ctx.send('The seek-to position must not be longer than the video, or less than zero.')

            # Seek to the position, and send a corresponding message
            await player.seek(time_to_seek)
            if time_to_seek > current_player_time:
                await ctx.send(f'Fast-forwarded to `{position}` in video.')
            else:
                await ctx.send(f'Re-winded video to `{position}`.')

            # Log command usage
            logCommand(ctx.author, 'seek')

        else:
            return await ctx.send('Invalid position to seek to. Check command help page with '
                                  '"!help seek" for more information.')

    @commands.command(help='ipsum dolor')
    async def playerinfo(self, ctx):
        await runChecks(ctx)
        # Check if player is running
        player: wavelink.Player = await checkPlayer(ctx)
        if not player:
            return

        # Check if player is running
        if not player.current:
            return await ctx.send('No track is currently playing, and the queue is empty.')

        # Create vars
        video_id = player.current.uri.replace('https://www.youtube.com/watch?v=', '')
        thumbnail_url = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'

        # Create the info embed
        embed = discord.Embed(
            title='Current Player Info',
            description=f'Information on the currently playing track.',
            color=discord.Color.from_rgb(1, 162, 186),
        )
        embed.add_field(name='Current Track Length:', value=convertDuration(player.current.duration))
        embed.add_field(name='Current Track Position:', value=convertDuration(player.position))
        embed.add_field(name='Author:', value=player.current.author)
        embed.add_field(name='URL:', value=player.current.uri)
        embed.add_field(name='Current Queue Length:', value=len(player.queue))
        embed.set_image(url=thumbnail_url)
        await ctx.send(embed=embed)

        # Log command usage
        logCommand(ctx.author, 'playerinfo')


async def setup(bot):
    await bot.add_cog(Music(bot))

