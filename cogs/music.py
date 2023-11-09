import discord
from discord.ext import commands
import wavelink

from settings import MUSIC_PASS as lavalink_password

class Music(commands.Cog):
    vc : wavelink.Player = None
    music_channel = None
    
    def __init__(self, bot):
        self.bot = bot

    # We create the node to listen to the lavalink server
    async def setup(self):
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password=lavalink_password)
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    ######################
    #       EVENTS       #
    ######################
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'node {node.id} is ready')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEventPayload):
        track = payload.track
        await self.music_channel.send(f'`{track.title}` started playing with a duration of {track.length / 1000} seconds')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        await self.music_channel.send(f'`{payload.track.title}` has finished')
        if self.vc.queue.is_empty and not self.vc.is_playing():
            self.vc.queue.clear()
            await self.vc.stop()
            await self.music_channel.send(f'The playlist has ended, lemme know if u want to listen to more music')


    ######################
    #      COMMANDS      #
    ######################
    @commands.command(name='play')
    async def play(self, ctx, *title : str):
        # ensures the user provides a query
        if not title:
            await ctx.send(f'Use the command as f!play <your query here>')
            return

        # Assigns a channel to send info about the player
        self.music_channel = ctx.message.channel
        channel = ctx.message.author.voice.channel

        # checks if the user is connected to a voicechat
        if not channel:
            await ctx.send(f'You need to join a voice channel first')
            return

        # Makes a youtube search of the query provided by the user
        tracks = await wavelink.YouTubeTrack.search(" ".join(title))
        
        # Checks if the query does not return something
        if not tracks:
            await ctx.send(f'No tracks found with query: `{" ".join(title)}`')
            return
        
        # This is the first result of the query
        track = tracks[0]

        # Checks if the bot is already connected to a voicechat
        # if so, the query result is push it to the player queue (or playlist)
        if self.vc:
            # this appends the track to the queue
            self.vc.queue(track)
            await self.music_channel.send(f'`{track.track.title}` has been added to the queue.')
            return

        # We create the player and connect it to the voicechat
        self.vc = await channel.connect(cls=wavelink.Player)
        # sets the attribute that make the player start the next track on when the current track ends
        self.vc.autoplay = True

        await self.vc.play(track, populate=False)

    
    @commands.command(name='disconnect')
    async def disconnect(self, ctx):
        await self.vc.disconnect()

    
    @commands.command(name='pause')
    async def pause(self, ctx):
        await self.vc.pause()

    @commands.command(name='resume')
    async def resume(self, ctx):
        await self.vc.resume()


    @commands.command(name='stop')
    async def stop(self, ctx):
        await self.vc.stop()

    @commands.command(name='queue')
    async def queue(self, ctx):
        print(self.vc.queue)
    

async def setup(bot):
    music_bot = Music(bot)
    await bot.add_cog(music_bot)
    await music_bot.setup()
