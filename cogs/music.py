# Imports
import discord
from discord.ext import commands
import wavelink
from wavelink.ext import spotify  # Spotify not supported, but maybe eventually...
import datetime
from utils.logger import logCommand

# TODO: Add move command, only usable by admins, to move bot from one VC to another


# Function written by ChatGPT. I know; shut up.
def convertDuration(milliseconds):
    # Convert milliseconds to seconds
    seconds = milliseconds / 1000

    # Create a timedelta object representing the duration
    duration = datetime.timedelta(seconds=seconds)

    # Format the duration as HH:MM:SS, even if hours exceed 99
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    return formatted_time


async def runChecks(ctx, BotNotInVC=None, UserNotInVCMsg=None, UserInDifferentVCMsg=None):
    user_vc = ctx.author.voice
    bot_vc = ctx.voice_client

    if not BotNotInVC:
        BotNotInVC = 'I am not connected to a voice channel.'

    if not UserNotInVCMsg:
        UserNotInVCMsg = 'You must be connected to the same channel as me to skip the current song.'

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


class Music(commands.Cog, description="Commands relating to the voice chat music player."):
    def __init__(self, bot):
        self.bot = bot

    # Listener: On Track End
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        player: wavelink.Player = payload.player
        if not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)

    # Command: Play
    @commands.command(help='Play a song in a voice chat. Syntax: "!play <URL or search term>""')
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

        tracks: list[wavelink.YouTubeTrack] = await wavelink.YouTubeTrack.search(query)
        if not tracks:
            return await ctx.send(f'I could\'nt find any songs with your query of "`{query}`."')

        track: wavelink.YouTubeTrack = tracks[0]
        if player.is_playing():
            # More efficient way to go about the embeds, but I'll do it later
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
                color=discord.Color.from_rgb(1, 162, 186),
            )
            embed.add_field(name='Length:', value=convertDuration(track.duration))
            embed.add_field(name='Author:', value=track.author)
            embed.add_field(name='Time Before Track Plays:', value=convertDuration(time_left))
            embed.set_image(url=track.thumb)
            await ctx.send(embed=embed)

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
        try:
            player: wavelink.Player = ctx.voice_client
        except:
            return await ctx.send('No music player is currently running.')

        # Stop playback if queue is empty
        if player.queue.is_empty:
            await player.stop()
            # Log the command
            logCommand(ctx.author, 'skip')
            return await ctx.send('Playback was stopped because there\'s no remaining songs in the queue.')
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

        # See if player is active
        try:
            player: wavelink.Player = ctx.voice_client
        except:
            # Don't log the command because it makes no difference
            return await ctx.send('No music player is currently running.')
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

        # See if player is active
        try:
            player: wavelink.Player = ctx.voice_client
        except:
            return await ctx.send('No music player is currently running.')

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
        # See if player is active
        try:
            player: wavelink.Player = ctx.voice_client
        except:
            return await ctx.send('No music player is currently running.')
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
            # See if player is active
            try:
                player: wavelink.Player = ctx.voice_client
            except:
                return await ctx.send('No music player is currently running.')
            # Set volume
            await player.set_volume(volume)
            await ctx.send(f'Volume of player adjusted to `{volume}`.')
            logCommand(ctx.author, 'volume')
        else:
            # Send error message
            return await ctx.send('Volume must be between one and 100.')


async def setup(bot):
    await bot.add_cog(Music(bot))

