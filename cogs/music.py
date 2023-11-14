import discord
from discord.ext import commands
import wavelink

from settings import MUSIC_PASS as lavalink_password

LOFI_GIRL = 'https://www.youtube.com/watch?v=jfKfPfyJRdk'
LOFI_BOY = 'https://www.youtube.com/watch?v=4xDzrJKXOOY'
LOFI_NATE = 'https://www.youtube.com/watch?v=UokZMBmnUGM'
LOFI_2_NATE = 'https://www.youtube.com/watch?v=0ucdLWYhdAc&t=8974s'
LOFI_MIDU = 'https://www.youtube.com/watch?v=p0OH206z9Wg'

def format_time(milliseconds):
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = ((milliseconds % 3600000) % 60000) / 1000

    return f'{"0" if hours < 10 else ""}{str(hours) + ":" if hours > 0 else ""}{minutes:02d}:{"0" if seconds < 10 else ""}{seconds:.0f}'

def embed_generator(description):
    embed = discord.Embed(
        colour = discord.Colour.dark_purple(),
        description = description
    )

    return embed


# ! Agregar el view a una variable de la cog para evitar que los comandos
# ! skip, stop, pause o resume la bugeen, basicamente hacerla una view global
# ! para poder manejar su estado

# ! Agregar una funcion para cler_items e interaciont response bla bla, it repites a lot.

class MusicView(discord.ui.View):
    paused : bool = False

    # Stops the Player if the ❌ is clicked
    @discord.ui.button(label='❌')
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        # stops Player
        await self.vc.stop()
        # Remove the items of the view
        self.clear_items()
        # edits the message of the interaction given
        await interaction.response.edit_message(view=self)

    # Pauses the Player if the ⏸ is clicked
    # When clicked the butto is updated to this ▶️ in order to create
    # user experience
    @discord.ui.button(label='⏸')
    async def pause_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        # flow of the current state of the Player
        if not self.paused:
            await self.vc.pause()
            self.children[1].label = '▶️'
            self.paused = True
        else:
            await self.vc.resume()
            self.children[1].label = '⏸'
            self.paused = False

        await interaction.response.edit_message(view=self)

    # Skips the Player to the next Track in the Queue when clicked
    @discord.ui.button(label='⏭️')
    async def next_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if Queue is empty disonnects the bot and remove the children of the View
        if self.vc.queue.is_empty:
            await interaction.response.send_message(embed=embed_generator(f'That was the last song'))
            await self.vc.disconnect()
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)
            return
        
        # If Queue has tracks it skips the current Track to the next one in Queue
        next_track = await self.vc.queue.get_wait()
        await self.vc.play(next_track, populate=False)

        self.clear_items()
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

        await self.music_channel.send(embed=embed, view=view)
        view.vc = self.vc

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        # basically disconnects the bot if the playlist has ended
        if self.vc.queue.is_empty and not self.vc.is_playing():
            channel = self.vc.channel.mention
            self.vc.queue.reset()
            await self.vc.disconnect()
            await self.music_channel.send(embed=embed_generator(f'🎛 The playlist has ended and bot has been disconnected from {channel}'))


    ######################
    #      COMMANDS      #
    ######################
    @commands.command(name='play')
    async def play(self, ctx, *title : str):
        # ensures the user provides a query
        if not title:
            await ctx.send(embed=embed_generator(f'Use the command as `f!play <your query here>`'))
            return

        # Assigns a channel to send info about the player
        self.music_channel = ctx.message.channel
        voice = ctx.message.author.voice

        # checks if the user is connected to a voicechat
        if not voice:
            await ctx.send(embed=embed_generator(f'Join a voice channel!'))
            return

        # Makes a youtube search of the query provided by the user
        tracks = await wavelink.YouTubeTrack.search(" ".join(title))
        
        # Checks if the query does not return something
        if not tracks:
            await ctx.send(embed=embed_generator(f'No tracks found with query: `{" ".join(title)}`.'))
            return
        
        # This is the first result of the query
        track = tracks[0]

        # Checks if the bot is already connected to a voicechat
        # if so, the query result is push it to the player queue (or playlist)
        if self.vc and self.vc.is_connected():
            # this appends the new track to the queue
            self.vc.queue(track)
            message = await self.music_channel.send(embed=embed_generator(f'`{track.title}` has been added to the queue.'))
            await message.delete(delay=5)
            return

        # We create the player and connect it to the voicechat
        self.vc = await voice.channel.connect(cls=wavelink.Player)
        # sets the attribute that make the player start the next track on when the current track ends
        self.vc.autoplay = True

        await self.vc.play(track, populate=False)

    @commands.command(name='disconnect')
    async def disconnect(self, ctx):
        await self.vc.disconnect()

    @commands.command(name='skip', aliases=['next'])
    async def skip(self, ctx):
        if self.vc.queue.is_empty:
            await ctx.send(embed=embed_generator(f'That was the last song'))
            await self.vc.disconnect()
            return

        next_track = await self.vc.queue.get_wait()
        await self.vc.play(next_track, populate=False)
    
    @commands.command(name='pause')
    async def pause(self, ctx):
        await self.vc.pause()

    @commands.command(name='resume')
    async def resume(self, ctx):
        await self.vc.resume()

    @commands.command(name='stop')
    async def stop(self, ctx):
        await self.vc.stop()

    @commands.command(name='playlist')
    async def playlist(self, ctx):

        if not self.vc or self.vc.queue.is_empty:
            await ctx.send(embed=embed_generator(f'There\'s no playlist'))
            return 

        print(self.vc.queue)
        queue = ''

        for track in self.vc.queue:
            queue += f'- {track} \n'

        await ctx.send(f'{queue}')

    # ! añadir controlador para decir que pasa del tiempo de la cancion y esto provocara skipearla
    # ! agregar a eso la cantidad de segundos restantes 
    @commands.command(name='ff')
    async def ff(self, ctx, seconds:int = 15):
        new_position = self.vc.position + (seconds * 1000)
        await self.vc.seek(new_position)
    
    # ! añadir controlador para decir que pasa del tiempo de la cancion y esto provocara skipearla
    # ! agregar a eso la cantidad de segundos restantes 
    @commands.command(name='gb')
    async def gb(self, ctx, seconds:int = 15):
        new_position = self.vc.position - (seconds * 1000)
        await self.vc.seek(new_position)

    # Agregar arguments para elegir que si lofi girl, lofi boy 
    # y 1 o 2 curated playlist de lofi para coding
    @commands.command(name='lofi')
    async def lofi(self, ctx, lofi:str = LOFI_GIRL):
        lofi_search = None
        if lofi:
            if lofi == 'boy':
                lofi_search = LOFI_BOY
            elif lofi == 'nate':
                lofi_search = LOFI_NATE
            elif lofi == 'nate2':
                lofi_search =  LOFI_2_NATE
            elif lofi == 'midu':
                lofi_search = LOFI_MIDU
            else:
                lofi_search = LOFI_GIRL

        # Assigns a channel to send info about the player
        self.music_channel = ctx.message.channel
        voice = ctx.message.author.voice

        # checks if the user is connected to a voicechat
        if not voice:
            await ctx.send(embed=embed_generator(f'Join a voice channel!'))
            return
        
        # aqui dberias hacer un condicional para los argumentos de los distintos
        # tipos de lofi
        tracks = await wavelink.YouTubeTrack.search(lofi_search)
        
        # Checks if the query does not return something
        if not tracks:
            await ctx.send(f'If you are reading this, it means that something happened to the links of the streams or the playlist')
            return

        track = tracks[0]

        if self.vc and self.vc.is_connected():
            view = LofiView(timeout=15)
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
