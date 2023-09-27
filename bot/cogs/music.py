# Imports
from discord.ext import commands
import wavelink


class Music(commands.Cog, description="Commands relating to the voice chat music player."):
    # Vars
    voice_client: wavelink.Player = None
    current_track = None

    def __init__(self, bot):
        self.bot = bot

    async def wavelinkSetup(self):
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='YouShallNotPass')
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    #@commands.Cog.listener()
    #async def on_wavelink_node_ready(self, node: wavelink.Node):
    #    print('Node connected')

    # Listener: On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')

    # Command: Join
    @commands.command(help='ipsum dolor')
    async def join(self, ctx):
        voice_channel = ctx.message.author.voice.channel
        if voice_channel:
            self.voice_client = voice_channel.connect(cls=wavelink.Player)
            await ctx.send(f'Joined {voice_channel.name}')

    # Command: Add
    @commands.command(help='ipsum dolor')
    async def add(self, ctx, *link: str):
        chosen_track = await wavelink.YouTubeTrack.search(query=" ".join(link), return_first=True)
        if chosen_track:
            self.current_track = chosen_track

    # Command: Play
    @commands.command(help='ipsum dolor')
    async def play(self, ctx):
        if self.current_track and self.voice_client:
            await self.voice_client.play(self.current_track)


async def setup(bot):
    # Create object of Music class to run Wavelink setup
    music = Music(bot)
    await bot.add_cog(Music(bot))
    #await music.wavelinkSetup()

