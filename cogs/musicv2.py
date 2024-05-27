import discord
import wavelink
from typing import cast
from discord.ext import commands
from utils.formatTime import format_time
from utils.removeAllItems import remove_all_items
from utils.embedGenerator import music_embed_generator
from settings import MUSIC_PASS as lavalink_password
from views.MusicView import MusicView
from views.PlaylistView import PlaylistView

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

    async def reset_player(self) -> None:
        self.vc = None
        self.music_channel = None
        self.view = None
        self.view_message = None

    ########################
    # - - - EVENTS - - - - #
    ########################
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f'\nNode [[ {payload.node.identifier} ]] is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        track = payload.track
        duration = format_time(track.length) if not track.is_stream else '🎙 live'
        thumbnail = track.artwork

        embed = discord.Embed(
            colour= discord.Colour.blurple(),
            description= f'[{track.title}]({track.uri})',
        )
        embed.set_author(name='🎵 | Suena')
        embed.add_field(name='Duración:', value=f'`{duration}`', inline=True)
        embed.add_field(name='Autor:', value=f'`{track.author}`', inline=True)
        embed.set_thumbnail(url=thumbnail)

        view_timeout = track.length / 1000 if not track.is_stream else None
        view = MusicView(timeout=view_timeout)

        view_message = await self.music_channel.send(embed=embed, view=view)
        view.vc = self.vc
        self.view_message = view_message
        self.view = view
        
        print(f'\n[+] Track started: {track.title}')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackStartEventPayload) -> None:
        print(f'\n[+] Track ended: {payload.track.title}')
        print(f'[!] reason: {payload.reason}\n')

        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)
        
        if self.vc.queue.is_empty and not self.vc.playing:
            await self.music_channel.send(embed=music_embed_generator(f'🎼 La playlist termino.'))

        if payload.reason == 'stopped':
            await self.vc.disconnect(force=True)
            await self.reset_player()
            return

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        print(f'[+] Player in guild: {player.guild.name} is inactive.')
        print(f'[+] Player disconnected from: {player.channel}\n')
        await player.disconnect(force=True)
        await self.reset_player()
        

    ########################
    # - - - COMMANDS - - - #
    ########################
    @commands.command(name='play')
    async def play(self, ctx, *query) -> None:
        # if no query is provided return
        if len(query) < 1:
            await ctx.send(embed=music_embed_generator('No se ha especificado ninguna canción'))
            return

        # join the query into a single string
        formated_query = " ".join(query)

        # check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send(embed=music_embed_generator('Debes estar en un canal de voz para usar este comando'))
            return
            
        # if the bot is not connected to a voice channel
        if not self.vc:
            # try to connect to the voice channel
            try:
                self.vc = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True, self_mute=True)   
            except AttributeError: # if the user is not connected to a voice channel
                await ctx.send(embed=music_embed_generator('No estas conectado a un canal de voz'))
                return
            except discord.ClientException: # if the bot can't connect to the voice channel
                await ctx.send(embed=music_embed_generator('No me pude conectar a este canal de voz'))
                return
        
        # this makes the bot play the next song in the queue when the current one ends
        # and does not make any recommendations
        self.vc.autoplay = wavelink.AutoPlayMode.partial
        self.vc.inactive_timeout = 10

        if not self.music_channel:
            self.music_channel = ctx.channel
        elif self.music_channel != ctx.channel:
            await ctx.send(embed=music_embed_generator(f'No puedes usar este comando en otro canal porque el bot ya está en uso en {self.music_channel.mention}'))
            return
                
        tracks: wavelink.Search = await wavelink.Playable.search(formated_query)

        if not tracks:
            await ctx.send(f'{ctx.author.mention} ninguna pista fue encontrada con: `{formated_query}`')
        
        if isinstance(tracks, wavelink.Playlist):
            added: int = await self.vc.queue.put_wait(tracks)
            link = f'[{tracks.name}]({tracks.url})'
            await ctx.send(embed=music_embed_generator(f'Playlist {link} (**{added}** songs) added to the queue'))
        else:
            track: wavelink.Playable = tracks[0]
            await self.vc.queue.put_wait(track)
            duration = format_time(track.length) if not track.is_stream else '🎙 live'
            description = f'Song [{track.title}]({track.uri}) added to the playlist {duration}'
            await ctx.send(embed=music_embed_generator(description))
        
        if not self.vc.playing:
            self.vc = cast(wavelink.Player, ctx.voice_client)
            await self.vc.play(self.vc.queue.get(), volume=100)
            
    @commands.command(name='pause')
    async def pause(self, ctx):
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send(embed=music_embed_generator('No estas en el mismo canal de voz que el bot'))
            return

        if not self.vc:
            await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento'))
            return
        
        if self.vc.paused:
            await ctx.send(embed=music_embed_generator('El bot ya está en pausa'))
            return

        await self.vc.pause(True)
        self.view.children[2].label = 'Resumir'
        self.view.children[2].emoji = '▶️'
        self.view.paused = True

    @commands.command(name='resume')
    async def resume(self, ctx):
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send(embed=music_embed_generator('No estas en el mismo canal de voz que el bot'))
            return
        
        if not self.vc:
            await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento'))
            return
        
        if not self.vc.paused:
            await ctx.send(embed=music_embed_generator('El bot ya está reproduciendo música'))
            return

        await self.vc.pause(False)
        self.view.children[2].label = 'Pausar'
        self.view.children[2].emoji = '⏸️'
        self.view.paused = False

    @commands.command(name='current')
    async def current(self, ctx):
        if not self.vc:
            await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento'))
            return
        
        track = self.vc.current
        current_position = format_time(int(self.vc.position))
        duration = format_time(track.length) if not track.is_stream else '🎙 live'
        thumbnail = track.artwork

        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'[{track.title}]({track.uri})'
        )
        embed.set_author(name='🎵 | Suena')
        embed.add_field(name='Duración', value=f'`{current_position}/{duration}`', inline=True)
        embed.add_field(name='autor', value=f'`{track.author}`', inline=True)
        embed.set_thumbnail(url=thumbnail)

        await ctx.send(embed=embed)

    @commands.command(name='playlist')
    async def playlist(self, ctx):
        if not self.vc:
            await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento'))
            return
        
        view = PlaylistView(timeout=None)
        view.vc = self.vc
        view.music_channel = self.music_channel
        await view.send()
    
    @commands.command(name='skip')
    async def skip(self, ctx):
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send(embed=music_embed_generator('No estas en el mismo canal de voz que el bot'))
            return
        
        if not self.vc:
            await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento'))
            return
        
        if self.vc.queue.is_empty:
            channel = self.vc.channel.mention
            remove_all_items(self.view)
            await self.view_message.edit(view=self.view)            
            self.vc.queue.clear()
            await self.vc.stop()
            await ctx.send(embed=music_embed_generator(f'🎼 La playlist termino. Bot desconectado de {channel} 👋'))
            return

        await self.vc.play(self.vc.queue.get())

    @commands.command(name='stop')
    async def stop(self, ctx):
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send(embed=music_embed_generator('No estas en el mismo canal de voz que el bot'))
            return
        
        if not self.vc:
            await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento'))
            return
        
        self.vc.queue.clear()
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)
        await self.vc.stop()
        await ctx.send(embed=music_embed_generator('Playlist detenida'))

    @commands.command(name='disconnect')
    async def disconnect(self, ctx):
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send(embed=music_embed_generator('No estas en el mismo canal de voz que el bot'))
            return
        
        if not self.vc:
            await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento'))
            return
        
        self.vc.queue.clear()
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)
        await self.vc.disconnect(force=True)
        await ctx.send(embed=music_embed_generator('Bot desconectado del canal de voz'))        

async def setup(bot):
    music_bot = Music(bot)
    await bot.add_cog(music_bot)
    await music_bot.setup_hook()