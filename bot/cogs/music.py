# Imports
from discord.ext import commands
import wavelink


class Music(commands.Cog, description="Commands relating to the voice chat music player."):
    def __init__(self, bot):
        self.bot = bot

    async def setup_hook(self) -> None:
        # Wavelink 2.0 has made connecting Nodes easier... Simply create each Node
        # and pass it to NodePool.connect with the client/bot.
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='YouShallNotPass')
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])
        print('test')

    # Example listener
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Extension loaded: {self.__class__.__name__}')


async def setup(bot):
    await bot.add_cog(Music(bot))

