import discord
import wavelink
import re
from typing import cast
from discord.ext import commands
from utils.formatTime import format_time
from utils.removeAllItems import remove_all_items
from utils.embedGenerator import music_embed_generator

from settings import MUSIC_PASS as lavalink_password

class MusicView(discord.ui.View):
    paused:bool = False
    skipper:bool = False

    @discord.ui.button(label='Atrasar', emoji='⏪')
    async def backward(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_position = self.vc.position - (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Parar', emoji='⏹️')
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.vc.queue.clear() # clears the queue
        await self.vc.stop() # stops the player
        self.clear_items() # clears the buttons
        await interaction.response.edit_message(view=self) # updates the message

    @discord.ui.button(label='Pausar', emoji='⏸️')
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        # pauses the player if it's playing and changes the button label
        await self.vc.pause(True if not self.paused else False)
        self.children[1].label = 'Resumir' if not self.paused else 'Pausar'
        self.children[1].emoji = '▶️' if not self.paused else '⏸️'
        self.paused = not self.paused
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Adelantar', emoji='⏩')
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_position = self.vc.position + (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)
    
    @discord.ui.button(label='Siguiente', emoji='⏭️')
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.queue.is_empty:
            channel = self.vc.channel.mention
            self.clear_items()
            await interaction.response.edit_message(view=self)
            await interaction.channel.send(embed=music_embed_generator(f'🎼 La playlist termino. Bot desconectado de {channel} 👋'))
            return
        
        await self.vc.skip()
        self.clear_items()
        await interaction.response.edit_message(view=self)


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
        
        print(f'[+] Track started: {track.title}')

    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackStartEventPayload) -> None:
        if self.vc.queue.is_empty and not self.vc.playing:
            channel = self.vc.channel.mention
            await self.music_channel.send(embed=music_embed_generator(f'🎼 La playlist termino. Bot desconectado de {channel} 👋'))
        
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)
        print(f'[+] Track ended: {payload.track.title}')
        print(f'[!] reason: {payload.reason}')
    
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
                self.vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            # if the user is not connected to a voice channel
            except AttributeError:
                await ctx.send(embed=music_embed_generator('No estas conectado a un canal de voz'))
                return
            # if the bot can't connect to the voice channel
            except discord.ClientException:
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
            await ctx.send(f'Added playlist {tracks.name}. ({added} songs) to the queue')
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
            await ctx.send('No estas en el mismo canal de voz que el bot')
            return

        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        
        await self.vc.pause(True)
        self.view.children[1].label = 'Resumir'
        self.view.children[1].emoji = '▶️'
        self.view.paused = True

    @commands.command(name='resume')
    async def resume(self, ctx):
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send('No estas en el mismo canal de voz que el bot')
            return
        
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        
        await self.vc.pause(False)
        self.view.children[1].label = 'Pausar'
        self.view.children[1].emoji = '⏸️'
        self.view.paused = False

    @commands.command(name='current')
    async def current(self, ctx):
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
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
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        queue = ""
        for track in self.vc.queue:
            queue += f'[+] {track.title}\n'

        await ctx.send(f'Playlist: \n{queue}')
    
    @commands.command(name='skip')
    async def skip(self, ctx):
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send('No estas en el mismo canal de voz que el bot')
            return
        
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        
        await self.vc.skip()

    @commands.command(name='stop')
    async def stop(self, ctx):
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send('No estas en el mismo canal de voz que el bot')
            return
        
        if not self.vc:
            await ctx.send('No hay ninguna canción sonando en este momento')
            return
        
        await self.vc.stop()

async def setup(bot):
    music_bot = Music(bot)
    await bot.add_cog(music_bot)
    await music_bot.setup_hook()