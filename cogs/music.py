import discord
import wavelink
import re
from discord.ext import commands
from wavelink.ext import spotify

from settings import MUSIC_PASS as lavalink_password
from settings import SPOTIFY_ID as spotify_id
from settings import SPOTIFY_SECRET as spotify_secret

# LOFI_GIRL = 'https://www.youtube.com/watch?v=jfKfPfyJRdk'
# LOFI_BOY = 'https://www.youtube.com/watch?v=4xDzrJKXOOY'
# LOFI_NATE = 'https://www.youtube.com/watch?v=UokZMBmnUGM'
# LOFI_2_NATE = 'https://www.youtube.com/watch?v=0ucdLWYhdAc'
# LOFI_MIDU = 'https://www.youtube.com/watch?v=p0OH206z9Wg'

LOFIS = {
    'girl': 'https://www.youtube.com/watch?v=jfKfPfyJRdk',
    'boy': 'https://www.youtube.com/watch?v=4xDzrJKXOOY',
    'nate': 'https://www.youtube.com/watch?v=UokZMBmnUGM',
    'nate2': 'https://www.youtube.com/watch?v=0ucdLWYhdAc',
    'midu': 'https://www.youtube.com/watch?v=p0OH206z9Wg'
}

SPOTIFY_REGEX = r"(?:\bhttps:\/\/open\.spotify\.com\/(?:track|episode|album|playlist)\/[A-Za-z0-9?=]+|spotify:(?:track|episode|album|playlist):[A-Za-z0-9?=]+)"
YOUTUBE_PLAYLIST_REGEX = r"(?:\bhttps:\/\/(?:www|music)*\.*(?:youtube|youtu)\.(?:com|be)\/(?:playlist)*[A-Za-z0-9-_]*\?list\=[A-Za-z0-9-_]+(?:&si\=)*[A-Za-z0-9-_]+)"

def format_time(milliseconds):
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = ((milliseconds % 3600000) % 60000) / 1000

    return f'{"0" if hours < 10 and hours > 0 else ""}{str(hours) + ":" if hours > 0 else ""}{minutes:02d}:{"0" if seconds < 10 else ""}{seconds:.0f}'

def embed_generator(description):
    embed = discord.Embed(
        colour = discord.Colour.dark_purple(),
        description = description
    )

    return embed

def remove_all_items(view):
    for item in view.children:
        view.remove_item(item)


# ! Agregar el view a una variable de la cog para evitar que los comandos
# ! skip, stop, pause o resume la bugeen, basicamente hacerla una view global
# ! para poder manejar su estado
# * HECHO

# ? funcion de current con la current position y buscar una forma de crear una barra de carga con algoritmo
# ! soporte de soundcloud
# ? añadir documentacion a las funciones de arriba
# ? cambiar los iconos de los botones por palabras como el bot kena
# ? Agregar embeds a lo necesario

class MusicView(discord.ui.View):
    paused : bool = False

    # rewind 15 seconds of the track
    @discord.ui.button(label='⏪')
    async def rewind(self, interaction: discord.Interaction, button: discord.ui.Button):
        # self.vc.position are milliseconds, thats why need 15 times 1000
        new_position = self.vc.position - (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)

    # Stops the Player if the ⏹️ is clicked
    @discord.ui.button(label='⏹️')
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        # stops Player
        self.vc.queue.clear()
        await self.vc.stop()
        # Remove the items of the view
        self.clear_items()
        # edits the message of the interaction given
        await interaction.response.edit_message(view=self)

    # Pauses the Player if the ⏸ is clicked
    # When clicked the butto is updated to this ▶️ in order to create
    # user experience
    @discord.ui.button(label='⏸️')
    async def pause_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        # flow of the current state of the Player
        if not self.paused:
            await self.vc.pause()
            self.children[2].label = '▶️'
            self.paused = True
        else:
            await self.vc.resume()
            self.children[2].label = '⏸'
            self.paused = False

        await interaction.response.edit_message(view=self)

    # Skips the Player to the next Track in the Queue when clicked
    @discord.ui.button(label='➡️')
    async def next_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if Queue is empty disonnects the bot and remove the children of the View
        if self.vc.queue.is_empty:
            channel = self.vc.channel.mention
            await self.vc.disconnect()
            self.clear_items()
            await interaction.response.edit_message(view=self)
            await interaction.channel.send(embed=embed_generator(f'🎼 Playlist has ended. Bot disconnected from {channel} 👋'))
            return
        
        # If Queue has tracks it skips the current Track to the next one in Queue
        next_track = await self.vc.queue.get_wait()
        await self.vc.play(next_track, populate=False)

        self.clear_items()
        await interaction.response.edit_message(view=self)
    
    # fast forward 15 seconds of the track
    @discord.ui.button(label='⏩')
    async def fast_forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        # self.vc.position are milliseconds, thats why need 15 times 1000
        new_position = self.vc.position + (15 * 1000)
        await self.vc.seek(new_position)
        await interaction.response.edit_message(view=self)

class LofiView(discord.ui.View):
    # When clicked the lofi is added to the Queue
    @discord.ui.button(label='Add', style=discord.ButtonStyle.success)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.description = f'Lofi added succesfully to the playlist!'
        self.vc.queue(self.track)
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

    # When clicked the Player clear its Queue and plays the lofi instead
    @discord.ui.button(label='Remove', style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.description = f'Removed. Here comes the lofi'
        self.vc.queue.clear()
        await self.vc.play(self.track, populate=False)
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

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
        print(f'node {node.id} is ready')

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
        embed.add_field(name='Duración', value=f'`{duration}`', inline=True)
        embed.add_field(name='autor', value=f'`{track.author}`', inline=True)
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
            self.vc.queue.reset()
            await self.vc.disconnect()
            await self.music_channel.send(embed=embed_generator(f'🎼 Playlist has ended. Bot disconnected from {channel} 👋'))
        
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)

    ######################
    #      COMMANDS      #
    ######################
    @commands.command(name='play')
    async def play(self, ctx, *title : str):
        # ensures the user provides a query
        if not title:
            await ctx.send(embed=embed_generator(f'Use the command as `f!play <your query here>`'))
            return
        
        # Set the tuple query into a string, usefull for spotify and youtube
        query = " ".join(title)
        # If theres no spotify link in the query it returns an empty list
        spotify_query = re.findall(SPOTIFY_REGEX, query)
        # If theres no youtube playlist link in the query it returns an empty list
        youtube_playlist_query = re.findall(YOUTUBE_PLAYLIST_REGEX, query)
        # stores tracks if they are found
        tracks = None
        # Boolean switch
        playlist = False
        # in case theres an album or playlist given by the user we store the title here
        playlist_title = ''

        # Assigns a channel to send info about the player
        self.music_channel = ctx.message.channel
        voice = ctx.message.author.voice

        # checks if the user is connected to a voicechat
        if not voice:
            await ctx.send(embed=embed_generator(f'Join a voice channel!'))
            return

        # We check depending on the query if we search for a spotify track, a souncloud track or a youtube track
        if spotify_query:
            # Looks for the first URL match
            payload = spotify.decode_url(spotify_query[0])
            # Checks if the query is an album or a playlist
            if payload.type == spotify.SpotifySearchType.playlist or spotify.SpotifySearchType.album:
                # stores in form of a list the current Playables from the playlist or album
                tracks: list[spotify.SpotifyTrack] = await spotify.SpotifyTrack.search(query=spotify_query[0])
                playlist_title = tracks[0].album
                playlist = True
            else:
                # Makes a spotify search of the query provided by the user
                tracks = await spotify.SpotifyTrack.search(query=spotify_query[0])
        # We check if the query url is a youtube playlist
        elif youtube_playlist_query:
            tracks = await wavelink.YouTubePlaylist.search(youtube_playlist_query[0])
            playlist_title = tracks.name
            playlist = True

        else:
            # Makes a youtube search of the query provided by the user
            tracks = await wavelink.YouTubeTrack.search(query)
        
        # Checks if the query does not return something
        if not tracks:
            await ctx.send(embed=embed_generator(f'No tracks found with query: `{query}`.'))
            return

        # ensures the tracks object is Playable because Playabes does not have the attribute "tracks"
        # if it does it means the provided link was a playlist
        # ! This makes me think that I need to refactor all this code at the time of Soundcloud implementation
        # ! NO SOUNDCLOUD IMPLEMENTATION WILL BE NEEDED BECAUSE SOUNDCLOUD IS NOT SUPPORTED BY WAVELINK
        if hasattr(tracks, 'tracks'):
            playlist_title = tracks.name
            playlist = True
        
        track = tracks.tracks[0] if youtube_playlist_query else tracks[0]

        # Checks if the bot is already connected to a voicechat
        # if so, the query result is push it to the player queue (or playlist)
        if self.vc and self.vc.is_connected():
            if playlist:
                if youtube_playlist_query:
                    for track in tracks.tracks:
                        self.vc.queue(track)
                    message = await self.music_channel.send(embed=embed_generator(f"`{playlist_title} added succesfully!`"))
                    await message.delete(delay=5)
                    return
                elif spotify_query:
                    for track in tracks:
                        self.vc.queue(track)
                    message = await self.music_channel.send(embed=embed_generator(f"`{playlist_title} added succesfully!`"))
                    await message.delete(delay=5)
                    return
            else:
                self.vc.queue(track)
                message = await self.music_channel.send(embed=embed_generator(f'`{track.title}` has been added to the queue.'))
                await message.delete(delay=5)
                return

        # We create the player and connect it to the voicechat
        self.vc = await voice.channel.connect(cls=wavelink.Player)
        # sets the attribute that make the player start the next track on when the current track ends
        self.vc.autoplay = True

        await self.vc.play(track, populate=False)

        if playlist:
            if youtube_playlist_query:
                for track in tracks.tracks[1:]:
                    self.vc.queue(track)
                message = await self.music_channel.send(embed=embed_generator(f"`{playlist_title} added succesfully!`"))
                await message.delete(delay=5)
                return
            elif spotify_query:
                for track in tracks[1:]:
                    self.vc.queue(track)
                message = await self.music_channel.send(embed=embed_generator(f"`{playlist_title} added succesfully!`"))
                await message.delete(delay=5)
                return

    @commands.command(name='disconnect')
    async def disconnect(self, ctx):
        await self.vc.disconnect()

    @commands.command(name='skip', aliases=['next'])
    async def skip(self, ctx):
        if self.vc.queue.is_empty and not self.vc.is_connected():
            await ctx.send(embed=embed_generator(f'There is no playlist'))
            return
        
        next_track = await self.vc.queue.get_wait()
        await self.vc.play(next_track, populate=False)
    
    @commands.command(name='pause')
    async def pause(self, ctx):
        await self.vc.pause()
        await ctx.message.delete(delay=1)
        self.view.children[2].label = "▶️"
        await self.view_message.edit(view=self.view)

    @commands.command(name='resume')
    async def resume(self, ctx):
        await self.vc.resume()
        await ctx.message.delete(delay=1)
        self.view.children[2].label = "⏸️"
        await self.view_message.edit(view=self.view)

    @commands.command(name='stop')
    async def stop(self, ctx):
        self.vc.queue.clear()
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)
        await ctx.message.delete(delay=1)
        await self.vc.stop()

    @commands.command(name='playlist', aliases=['queue'])
    async def playlist(self, ctx):

        if not self.vc or self.vc.queue.is_empty:
            await ctx.send(embed=embed_generator(f'There\'s no playlist'))
            return 

        print(self.vc.queue)
        queue = ''

        for track in self.vc.queue:
            queue += f'- {track} \n'

        await ctx.send(f'{queue}')

    @commands.command(name='ff')
    async def ff(self, ctx, seconds:int = 15):
        new_position = self.vc.position + (seconds * 1000)
        await self.vc.seek(new_position)
    
    @commands.command(name='gb')
    async def gb(self, ctx, seconds:int = 15):
        new_position = self.vc.position - (seconds * 1000)
        await self.vc.seek(new_position)

    @commands.command(name='lofi')
    async def lofi(self, ctx, choose:str = 'girl'):
        # lofi_search = None
        
        # match lofi:
        #     case 'boy':
        #         lofi_search = LOFI_BOY
        #     case 'nate':
        #         lofi_search = LOFI_NATE
        #     case 'nate2':
        #         lofi_search =  LOFI_2_NATE
        #     case 'midu':
        #         lofi_search = LOFI_MIDU
        #     case _:
        #         lofi_search = LOFI_GIRL

        # returns a list of the keys from LOFIS constant
        lofis = list(LOFIS.keys())
        # uses list comprehesion to lookup for values inside the lofis list
        # if the choose input from the user is inside the key list it will
        # return an array with the current key provided by the user
        lofi_search = [lofi for lofi in lofis if choose.lower() in lofi]

        # Assigns a channel to send info about the player
        self.music_channel = ctx.message.channel
        voice = ctx.message.author.voice

        # checks if the user is connected to a voicechat
        if not voice:
            await ctx.send(embed=embed_generator(f'Join a voice channel!'))
            return
        
        # using lofi_search list if is empty uses the default girl lofi or if the input is not in the list
        # if is in the list, it plays the url in LOFIS constant dict
        tracks = await wavelink.YouTubeTrack.search(LOFIS['girl'] if not lofi_search else LOFIS[lofi_search[0]])
        
        # Checks if the query does not return something
        if not tracks:
            await ctx.send(f'If you are reading this, it means that something happened to the links of the streams or the playlist')
            return

        track = tracks[0]

        if self.vc and self.vc.is_connected():
            view = LofiView(timeout=10)
            # this appends the new track to the queue
            message = await self.music_channel.send(embed=embed_generator(f'Wanna add the lofi radio to the playlist or you want to remove the playlist and let the radio alone?'), view=view)
            view.vc = self.vc
            view.track = track

            await view.wait()
            await message.delete(delay=5)
            return
        
        self.vc = await voice.channel.connect(cls=wavelink.Player)
        self.vc.autoplay = False

        await self.vc.play(track, populate=False)

async def setup(bot):
    music_bot = Music(bot)
    await bot.add_cog(music_bot)
    await music_bot.setup()
