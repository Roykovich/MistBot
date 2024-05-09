import discord
import wavelink
import re
from typing import cast
from discord.ext import commands

from settings import MUSIC_PASS as lavalink_password

class Music(commands.Cog):
    vc : wavelink.Player = None
    music_channel = None
    view = None
    view_message = None

    def __init__(self, bot):
        self.bot = bot

    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri='http://localhost:2333', password=lavalink_password)]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f'Node [[ {payload.node.identifier} ]] is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        print(f'[+] Track started: {payload.track.title}')
        print(f'link: {payload.track.uri}')
    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackStartEventPayload) -> None:
        print(f'[+] Track ended: {payload.track.title}')
    
    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        print(f'[+] Player in guild: {player.guild.name} is inactive.')
        print(f'[+] Player disconnected from: {player.channel}\n')
        await player.disconnect()
        

    ########################
    # - - - COMMANDS - - - #
    ########################
    @commands.command(name='play')
    async def play(self, ctx, *query) -> None:
        # if no query is provided return
        if len(query) < 1:
            await ctx.send('No se ha especificado ninguna canción')
            return
        
        # join the query into a single string
        formated_query = " ".join(query)
        print(formated_query)
        # check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send('Necesitas estar en un canal de voz para usar este comando')
            return
            
        # if the bot is not connected to a voice channel
        if not self.vc:
            # try to connect to the voice channel
            try:
                self.vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            # if the user is not connected to a voice channel
            except AttributeError:
                await ctx.send('No estas conectado a un canal de voz')
                return
            # if the bot can't connect to the voice channel
            except discord.ClientException:
                await ctx.send('No me pude conectar a este canal de voz')
                return
        
        # this makes the bot play the next song in the queue when the current one ends
        # and does not make any recommendations
        self.vc.autoplay = wavelink.AutoPlayMode.partial
        self.vc.inactive_timeout = 10

        if not self.music_channel:
            self.music_channel = ctx.channel
        elif self.music_channel != ctx.channel:
            await ctx.send(f'No puedes usar este comando en otro canal porque el bot ya está en uso en {self.music_channel.mention}')
            return
                
        tracks: wavelink.Search = await wavelink.Playable.search(formated_query)

        if not tracks:
            await ctx.send(f'{ctx.author.mention} ninguna pista fue encontrada con: `{formated_query}`')
        
        if isinstance(tracks, wavelink.Playlist):
            added: int = await self.vc.queue.put_wait(tracks)
            await ctx.send(f'Added playlist {tracks.name}. ({added} songs) to the queue')
        else:
            track: wavelink.Playable = tracks[0]
            await self.vc.queue.put_wait(track)
            await ctx.send('query: ' + formated_query)
        
        if not self.vc.playing:
            self.vc = cast(wavelink.Player, ctx.voice_client)
            await self.vc.play(self.vc.queue.get(), volume=100)
            
    @commands.command(name='pause')
    async def pause(self, ctx):
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        await self.vc.pause(True)
        await ctx.send('Pausado')

    @commands.command(name='resume')
    async def resume(self, ctx):
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        await self.vc.pause(False)
        await ctx.send('Reanudado')

    @commands.command(name='current')
    async def current(self, ctx):
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        print(self.vc.playing)
        print(type(self.vc))
        await ctx.send(f'Now playing: {self.vc.current}')

    @commands.command(name='playlist')
    async def playlist(self, ctx):
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        queue = ""
        for track in self.vc.queue:
            queue += f'[+] {track.title}\n'

        await ctx.send(f'Playlist: \n{queue}')
    
    @commands.command(name='skip')
    async def skip(self, ctx):
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        await self.vc.skip()
        await ctx.send('Saltando canción...')

    @commands.command(name='stop')
    async def stop(self, ctx):
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        await self.vc.stop()
        await ctx.send('Deteniendo...')


async def setup(bot):
    music_bot = Music(bot)
    await bot.add_cog(music_bot)
    await music_bot.setup_hook()