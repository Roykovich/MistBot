import discord
import wavelink
import re
from discord.ext import commands
from discord import app_commands
from wavelink.ext import spotify

from settings import MUSIC_PASS as lavalink_password
from settings import SPOTIFY_ID as spotify_id
from settings import SPOTIFY_SECRET as spotify_secret

LOFIS = {
    'girl': 'https://www.youtube.com/watch?v=jfKfPfyJRdk',
    'boy': 'https://www.youtube.com/watch?v=4xDzrJKXOOY',
    'nate': 'https://www.youtube.com/watch?v=UokZMBmnUGM',
    'nate2': 'https://www.youtube.com/watch?v=0ucdLWYhdAc',
    'midu': 'https://www.youtube.com/watch?v=p0OH206z9Wg'
}

YOUTUBE_PLAYLIST_REGEX = r"(?:\bhttps:\/\/(?:www|music)*\.*(?:youtube|youtu)\.(?:com|be)\/(?:playlist)*[A-Za-z0-9-_]*\?list\=[A-Za-z0-9-_]+(?:&si\=)*[A-Za-z0-9-_]+)"

# Formats the time in milliseconds to a human readable format
def format_time(milliseconds):
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = ((milliseconds % 3600000) % 60000) / 1000

    return f'{"0" if hours < 10 and hours > 0 else ""}{str(hours) + ":" if hours > 0 else ""}{minutes:02d}:{"0" if seconds < 10 else ""}{seconds:.0f}'

# Generates an embed with the description given
def embed_generator(description):
    embed = discord.Embed(
        colour = discord.Colour.dark_purple(),
        description = description
    )

    return embed

# Removes all the items from the view
def remove_all_items(view):
    for item in view.children:
        view.remove_item(item)

class MusicExceptionHandler(app_commands.CheckFailure):
    ...

def check_voice():
    async def predicate(interaction: discord.Interaction)  -> bool:
        if interaction.user.voice is None:
            raise MusicExceptionHandler('not_in_voice')
        
        if interaction.client.voice_clients is None:
            raise MusicExceptionHandler('no_bot_in_voice')
        
        if interaction.client.voice_clients and (interaction.user.voice.channel != interaction.client.voice_clients[0].channel):
            raise MusicExceptionHandler('not_in_same_voice')
        
        return True
    return app_commands.check(predicate)

class MusicView(discord.ui.View):
    paused : bool = False

    # rewind 15 seconds of the track
    @discord.ui.button(label='Atrasar', emoji='⏪')
    async def rewind(self, interaction: discord.Interaction, button: discord.ui.Button):
        # self.vc.position are milliseconds, thats why need 15 times 1000
        new_position = self.vc.position - (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)

    # Stops the Player if the ⏹️ is clicked
    @discord.ui.button(label='Parar', emoji='⏹️')
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        # stops Player
        self.vc.queue.clear()
        await self.vc.stop()
        # Remove the items of the view
        self.clear_items()
        # edits the message of the interaction given
        await interaction.response.edit_message(view=self)

    # Pauses the Player if the ⏸ is clicked
    # When clicked the button is updated to this ▶️ in order to create
    # user experience
    @discord.ui.button(label='Pausar', emoji='⏸️')
    async def pause_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        # flow of the current state of the Player
        if not self.paused:
            await self.vc.pause()
            self.children[2].label = 'Resumir'
            self.children[2].emoji = '▶️'
            self.paused = True
        else:
            await self.vc.resume()
            self.children[2].label = 'Pausar'
            self.children[2].emoji = '⏸️'
            self.paused = False

        await interaction.response.edit_message(view=self)

    # fast forward 15 seconds of the track
    @discord.ui.button(label='Adelantar', emoji='⏩')
    async def fast_forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        # self.vc.position are milliseconds, thats why need 15 times 1000
        new_position = self.vc.position + (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)

    # Skips the Player to the next Track in the Queue when clicked
    @discord.ui.button(label='Siguiente', emoji='⏭️')
    async def next_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if Queue is empty disonnects the bot and remove the children of the View
        if self.vc.queue.is_empty:
            channel = self.vc.channel.mention
            await self.vc.disconnect()
            self.clear_items()
            await interaction.response.edit_message(view=self)
            await interaction.channel.send(embed=embed_generator(f'🎼 La playlist termino. Bot desconectado de {channel} 👋'))
            return
        
        # If Queue has tracks it skips the current Track to the next one in Queue
        next_track = await self.vc.queue.get_wait()
        await self.vc.play(next_track, populate=False)

        self.clear_items()
        await interaction.response.edit_message(view=self)

class LofiView(discord.ui.View):
    # When clicked the lofi is added to the Queue
    @discord.ui.button(label='Agregar', style=discord.ButtonStyle.success)
    async def add_to(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.description = f'El lofi ha sido agregado a la playlist!'
        self.vc.queue(self.track)
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

    # When clicked the Player clear its Queue and plays the lofi instead
    @discord.ui.button(label='Quitar', style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.description = f'Playlist limpiada. ¡Ahí va el lofi!'
        self.vc.queue.clear()
        await self.vc.play(self.track, populate=False)
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

class PlaylistView(discord.ui.View):
    # The current page of the playlist
    current_page: int = 1
    # The separator of the playlist, in this case is 10 tracks per page
    separator: int = 10

    # Sends the playlist to the channel where the command was invoked from 
    async def send(self):
        embed = await self.create_embed(list(self.vc.queue)[:self.separator])
        self.message = await self.music_channel.send(embed=embed, view=self)
        await self.update_message(list(self.vc.queue)[:self.separator])

    # Creates the embed of the playlist
    async def create_embed(self, tracks):
        current_track = self.vc.current
        current_position = format_time(int(self.vc.position))
        duration = format_time(current_track.length) if not current_track.is_stream else '🎙 live'
        thumbnail = await current_track.fetch_thumbnail()

        # if the queue is empty it returns the current track
        if not self.vc.queue or self.vc.queue.is_empty:
            embed = discord.Embed(
                colour = discord.Colour.dark_purple(),
                description = f'[{current_track.title}]({current_track.uri})'
            )
            embed.set_author(name='🎵 | Suena')
            embed.add_field(name='Duración', value=f'`{current_position}/{duration}`', inline=True)
            embed.add_field(name='autor', value=f'`{current_track.author}`', inline=True)
            embed.set_thumbnail(url=thumbnail)

            return embed

        description = f'**Ahora suena:**\n[{current_track} - {current_track.author}]({current_track.uri})\n**Duración:**\n`{current_position}/{duration}`\n\n**Playlist:**\n'
        
        for i, track in enumerate(tracks):
            description += f'`[{i}]`丨**{track.title}**\n'

        embed = discord.Embed(
            title=f"Página {self.current_page} / {int(len(self.vc.queue) / self.separator) + 1}",
            color=discord.Colour.dark_purple(), 
            description=description
        )

        return embed

    # Updates the message of the playlist
    async def update_message(self, data):
        self.update_buttons()
        embed = await self.create_embed(data)
        await self.message.edit(embed=embed, view=self)

    # Updates the buttons of the playlist
    def update_buttons(self):
        if self.current_page == 1:
            self.previous.disabled = True
            self.previous.style = discord.ButtonStyle.grey
        else:
            self.previous.disabled = False
            self.previous.style = discord.ButtonStyle.primary
        
        if self.current_page == int(len(self.vc.queue) / self.separator) + 1:
            self.next.disabled = True
            self.next.style = discord.ButtonStyle.grey
        else:
            self.next.disabled = False
            self.next.style = discord.ButtonStyle.primary

    # Gets the current page of the playlist
    def get_current_page(self):
        until_page = self.current_page * self.separator
        from_page = until_page - self.separator

        if self.current_page == 1:
            from_page = 0
            until_page = self.separator
        
        if self.current_page == int(len(self.vc.queue) / self.separator) + 1:
            from_page = self.current_page - 1 * self.separator - self.separator
            until_page = len(self.vc.queue)

        return list(self.vc.queue)[from_page:until_page]


    @discord.ui.button(label='Anterior', emoji='⬅️', style=discord.ButtonStyle.gray, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.get_current_page())

    @discord.ui.button(label='Siguiente', emoji='➡️', style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.get_current_page())

class Music(commands.Cog):
    vc : wavelink.Player = None
    music_channel = None
    view = None
    view_message = None
    
    def __init__(self, bot):
        self.bot = bot

    # We create the node to listen to the lavalink server
    async def setup(self):
        spotify_client =  spotify.SpotifyClient(
            client_id=spotify_id,
            client_secret=spotify_secret
        )

        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password=lavalink_password)
        await wavelink.NodePool.connect(client=self.bot, nodes=[node], spotify=spotify_client)

    ######################
    #       EVENTS       #
    ######################
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'Nodo de lavalink: {node.id} está listo.')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEventPayload):
        track = payload.track
        # check if the track is a stream or not
        duration = format_time(track.length) if not track.is_stream else '🎙 live'\
        # fetchs thumbnail
        thumbnail = await payload.original.fetch_thumbnail()
        
        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'[{track.title}]({track.uri})'
        )
        embed.set_author(name='🎵 | Suena')
        embed.add_field(name='Duración:', value=f'`{duration}`', inline=True)
        embed.add_field(name='Autor:', value=f'`{track.author}`', inline=True)
        embed.set_thumbnail(url=thumbnail)

        # check if is stream for the timeout of the buttons
        view_timeout = track.length / 1000 if not track.is_stream else None 
        view = MusicView(timeout=view_timeout)

        view_message = await self.music_channel.send(embed=embed, view=view)
        view.vc = self.vc
        self.view_message = view_message
        self.view = view

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        print(payload.reason)
        # basically disconnects the bot if the playlist has ended
        if self.vc.queue.is_empty and not self.vc.is_playing():
            channel = self.vc.channel.mention
            self.vc.auto_queue.reset()
            await self.vc.stop()
            await self.music_channel.send(embed=embed_generator(f'🎼 La playlist termino. Bot desconectado de {channel} 👋'))
        
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)

    async def cog_app_command_error(self, interaction: discord.Interaction, exception: discord.DiscordException):
        if isinstance(exception, MusicExceptionHandler):
            if exception.args[0] == 'not_in_voice':
                return await interaction.response.send_message(embed=embed_generator(f'¡Únete a un canal de voz primero!'), ephemeral=True, delete_after=3)
            elif exception.args[0] == 'no_bot_in_voice':
                return await interaction.response.send_message(embed=embed_generator(f'El bot no está conectado.'), ephemeral=True, delete_after=3)
            elif exception.args[0] == 'not_in_same_voice':
                return await interaction.response.send_message(embed=embed_generator(f'El bot ya esta reproduciendo en otro canal'), ephemeral=True, delete_after=3)
        
        print(exception)

    ######################
    #      COMMANDS      #
    ######################
    @app_commands.command(name='play', description='Agrega el bot a un canal de voz y reproduce la canción que le pases')
    @check_voice()
    @app_commands.describe(query='La canción que quieres reproducir')
    async def play(self, interaction: discord.Interaction, query : str):
        # If theres no spotify link in the query it returns an empty list
        spotify_query = spotify.decode_url(query)
        # If theres no youtube playlist link in the query it returns an empty list
        youtube_playlist_query = re.search(YOUTUBE_PLAYLIST_REGEX, query)
        # stores tracks if they are found
        tracks = None
        # Boolean switch
        playlist = False
        # in case theres an album or playlist given by the user we store the title here
        playlist_title = ''

        # Assigns a channel to send info about the player
        self.music_channel = interaction.channel
        voice = interaction.user.voice

        # We check depending on the query if we search for a spotify track, a souncloud track or a youtube track
        if spotify_query:
            print('spotify')
            if spotify_query.type == spotify.SpotifySearchType.unusable:
                await interaction.response.send_message(embed=embed_generator(f'Este link de spotify no puede ser reproducido.'), ephemeral=True, delete_after=10)
                return
            
            # Checks if the query is an album or a playlist
            if spotify_query.type == spotify.SpotifySearchType.playlist or spotify.SpotifySearchType.album:
                # stores in form of a list the current Playables from the playlist or album
                tracks: list[spotify.SpotifyTrack] = await spotify.SpotifyTrack.search(query=query)
                playlist_title = tracks[0].album
                playlist = True
            else:
                # Makes a spotify search of the query provided by the user
                tracks = await spotify.SpotifyTrack.search(query=query)

        elif youtube_playlist_query: # We check if the query url is a youtube playlist
            results = await wavelink.YouTubePlaylist.search(query)
            tracks: list[wavelink.YouTubeTrack] = results.tracks if hasattr(results, 'tracks') else None
            playlist_title = results.name
            playlist = True
        else: # Makes a youtube search of the query provided by the user
            tracks = await wavelink.YouTubeTrack.search(query)
        
        # Checks if the query does not return something
        if not tracks:
            await interaction.response.send_message(f'Ninguna pista fue encontrada con: `{query}`.', ephemeral=True, delete_after=10)
            return

        track = tracks[0]

        # Checks if the bot is already connected to a voicechat
        # if so, the query result is push it to the player queue (or playlist)
        if self.vc and self.vc.is_connected():
            # Is the bot is connected to the voice channel and is not playing anything
            # it plays the track
            if not self.vc.is_playing():
                await interaction.response.send_message(content=f'👍', ephemeral=True, delete_after=0.3)
                await self.vc.play(track, populate=False)
                return

            # if the query is a playlist or an album it adds the tracks to the queueq
            if playlist:
                self.vc.queue += tracks[1:]
                await interaction.response.send_message(embed=embed_generator(f"¡La playlist `{playlist_title}` se ha añadido exitosamente!"), ephemeral=True, delete_after=5)
                return
            
            # if the query is a single track it adds it to the queue 
            self.vc.queue(track)
            await interaction.response.send_message(embed=embed_generator(f'`{track.title}` se ha agregado a la playlist.'), ephemeral=True, delete_after=5)
            return

        # We create the player and connect it to the voicechat
        self.vc = await voice.channel.connect(cls=wavelink.Player)
        # sets the attribute that make the player start the next track on when the current track ends
        self.vc.autoplay = True

        await self.vc.play(track, populate=False)

        if playlist:
            self.vc.queue += tracks[1:]
            await interaction.response.send_message(embed=embed_generator(f"¡La playlist `{playlist_title}` se ha añadido exitosamente!"), ephemeral=True, delete_after=5)
            return
        
        await interaction.response.send_message(content=f'👍🏻', ephemeral=True, delete_after=0.5)

    @app_commands.command(name='disconnect', description='Desconecta el bot del canal de voz y limpia la playlist')
    @check_voice()
    async def disconnect(self, interaction: discord.Interaction):
        self.vc.queue.clear()
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)
        await interaction.response.send_message(content=f'👍', ephemeral=True, delete_after=0.5)
        await self.vc.disconnect()

    @app_commands.command(name='skip', description='Salta a la siguiente canción de la playlist')
    @check_voice()
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=f'👍', ephemeral=True, delete_after=0.5)
        next_track = await self.vc.queue.get_wait()
        await self.vc.play(next_track, populate=False)
    
    @app_commands.command(name='pause', description='Pausa el bot si está reproduciendo')
    @check_voice()
    async def pause(self, interaction: discord.Interaction):
        await self.vc.pause()
        self.view.children[2].label = 'Resumir'
        self.view.children[2].emoji = '▶️'
        await self.view_message.edit(view=self.view)
        await interaction.response.send_message(content=f'👍', ephemeral=True, delete_after=0.5)

    @app_commands.command(name='resume', description='Resume el bot si está pausado')
    @check_voice()
    async def resume(self, interaction: discord.Interaction):
        await self.vc.resume()
        self.view.children[2].label = 'Pausar'
        self.view.children[2].emoji = '⏸️'
        await self.view_message.edit(view=self.view)
        await interaction.response.send_message(content=f'👍', ephemeral=True, delete_after=0.5)

    @app_commands.command(name='stop', description='Detiene el bot y limpia la playlist')
    @check_voice()
    async def stop(self, interaction: discord.Interaction):
        self.vc.queue.clear()
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)
        await self.vc.stop()
        await interaction.response.send_message(embed=embed_generator(f'Bot detenido 👍'), ephemeral=True, delete_after=3)

    @app_commands.command(name='playlist', description='Muestra la playlist')
    @check_voice()
    async def playlist(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=f'👍', ephemeral=True, delete_after=0.3)
        view = PlaylistView(timeout=None)
        view.vc = self.vc
        view.music_channel = self.music_channel
        await view.send()


    @app_commands.command(name='forward', description='Adelanta 15 segundos de la canción actual')
    @check_voice()
    async def ff(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=f'👍', ephemeral=True, delete_after=0.5)
        new_position = self.vc.position + (15 * 1000)
        await self.vc.seek(new_position)
    
    @app_commands.command(name='rewind', description='Atrasa 15 segundos de la canción actual')
    @check_voice()
    async def gb(self, interaction: discord.Interaction):     
        await interaction.response.send_message(content=f'👍', ephemeral=True, delete_after=0.5)
        new_position = self.vc.position - (15 * 1000)
        await self.vc.seek(new_position)

    @app_commands.command(name='current', description='Muestra la canción actual')
    @check_voice()
    async def current(self, interaction: discord.Interaction):
        track = self.vc.current
        current_position = format_time(int(self.vc.position))
        duration = format_time(track.length) if not track.is_stream else '🎙 live'
        thumbnail = await track.fetch_thumbnail()

        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'[{track.title}]({track.uri})'
        )
        embed.set_author(name='🎵 | Suena')
        embed.add_field(name='Duración', value=f'`{current_position}/{duration}`', inline=True)
        embed.add_field(name='autor', value=f'`{track.author}`', inline=True)
        embed.set_thumbnail(url=thumbnail)

        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=10)

    @app_commands.command(name='shuffle', description='Mezcla la playlist')
    @check_voice()
    async def shuffle(self, interaction: discord.Interaction):
        self.vc.queue.shuffle()
        await interaction.response.send_message(embed=embed_generator(f'Playlist mezclada 👍'), delete_after=3)

    @app_commands.command(name='loop', description='Repite la playlist')
    @check_voice()
    @app_commands.choices(loop = [
        app_commands.Choice(name='apagado', value='apagado'),
        app_commands.Choice(name='encendido', value='encendido')
    ])
    async def loop(self, interaction: discord.Interaction, loop: app_commands.Choice[str]):
        self.vc.queue.loop = True if loop.value == 'encendido' else False
        await interaction.response.send_message(embed=embed_generator(f'Loop {"activado" if loop.value == "encendido" else "desactivado"} 👍'), delete_after=3)

    @app_commands.command(name='lofi', description='Reproduce una radio con lofi')
    @check_voice()
    @app_commands.choices(playlists = [
        app_commands.Choice(name='relax/study', value='girl'),
        app_commands.Choice(name='chill/game', value='boy'),
        app_commands.Choice(name='[coding] nate', value='nate'),
        app_commands.Choice(name='[coding] nate v2', value='nate2'),
        app_commands.Choice(name='[coding] midu ', value='midu')
    ])
    async def lofi(self, interaction: discord.Interaction, playlists: app_commands.Choice[str]):
        # Assigns a channel to send info about the player
        self.music_channel = interaction.channel
        voice = interaction.user.voice
        
        # using lofi_search list if is empty uses the default girl lofi or if the input is not in the list
        # if is in the list, it plays the url in LOFIS constant dict
        tracks = await wavelink.YouTubeTrack.search(LOFIS[playlists.value])
        
        # Checks if the query does not return something
        if not tracks:
            await interaction.response.send_message(f'Si estás viendo esto es porque algo salió mal, por favor reportalo a Rubén')
            return

        track = tracks[0]

        if self.vc and self.vc.is_connected():
            view = LofiView(timeout=10)
            # this appends the new track to the queue
            await interaction.response.send_message(embed=embed_generator(f'¿Quieres agregar la radio a la playlist **o** quiere limpiar la lista y agregar la radio?'), view=view, delete_after=10)
            view.vc = self.vc
            view.track = track
            await view.wait()
            return
        
        self.vc = await voice.channel.connect(cls=wavelink.Player)
        self.vc.autoplay = False

        await self.vc.play(track, populate=False)
        await interaction.response.send_message(embed=embed_generator(f'👍'), ephemeral=True, delete_after=0.3)

async def setup(bot):
    music_bot = Music(bot)
    await bot.add_cog(music_bot)
    await music_bot.setup()
