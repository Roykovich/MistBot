import discord
import wavelink
import re
import typing
from discord.ext import commands

from settings import MUSIC_PASS as lavalink_password

class Music(commands.Cog):
    vc : wavelink.Player = None
    music_channel = None # parece que los Player tienen un canal asociado
    view = None
    view_message = None

    def __init__(self, bot):
        self.bot = bot

    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri='ws://localhost:2333', password=lavalink_password)]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f'Node [ {payload.node.identifier} ] is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        print(f'Track started: {payload.track.title}')
    
    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        print(f'Player {player} is inactive')
        


async def setup(bot):
    music_bot = Music(bot)
    await bot.add_cog(music_bot)
    await music_bot.setup_hook()