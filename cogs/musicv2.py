import discord
import wavelink
import datetime
from typing import cast
from discord.ext import commands
from utils.FormatTime import format_time
from utils.RemoveAllItems import remove_all_items
from utils.EmbedGenerator import music_embed_generator
from utils.NowPlaying import now_playing
from utils.VoiceChecker import check_voice_channel
from views.MusicView import MusicView
from views.PlaylistView import PlaylistView
from settings import MUSIC_PASS as lavalink_password

class Music(commands.Cog):
    vc : wavelink.Player = None
    music_channel = None
    view = None
    view_message = None
    user_list = []

    players: dict = {}
    

    def __init__(self, bot):
        self.bot = bot

    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri='http://localhost:2333', password=lavalink_password)]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)

    async def reset_player(self, id) -> None:
        self.players.pop(str(id))

    ###############################
    # - - - - E V E N T S - - - - #
    ###############################
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f'\nNode {payload.node.identifier} is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        track = payload.track
        embed = now_playing(track, user=self.user_list[0] if self.user_list else None)
        # self.user_list.pop(0)
        self.players[str(payload.player.guild.id)]['user_list'].pop(0)

        view_timeout = track.length / 1000 if not track.is_stream else None
        view = MusicView(timeout=view_timeout)

        # view_message = await self.music_channel.send(embed=embed, view=view)
        view_message = await self.players[str(payload.player.guild.id)]['music_channel'].send(embed=embed, view=view)
        # view.vc = self.vc
        view.vc = payload.player
        # view.music_channel = self.music_channel
        view.music_channel = self.players[str(payload.player.guild.id)]['music_channel']
        # view.user_list = self.user_list
        view.user_list = self.players[str(payload.player.guild.id)]['user_list']
        
        # self.view_message = view_message
        self.players[str(payload.player.guild.id)]['view_message'] = view_message
        # self.view = view
        self.players[str(payload.player.guild.id)]['view'] = view
        
        print(f'\n[+] Track started: {track.title}')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackStartEventPayload) -> None:
        print(f'\n[+] Track ended: {payload.track.title}')
        print(f'[!] reason: {payload.reason}')

        # remove_all_items(self.view)
        remove_all_items(self.players[str(payload.player.guild.id)]['view'])
        # await self.view_message.edit(view=self.view)
        await self.players[str(payload.player.guild.id)]['view_message'].edit(view=self.players[str(payload.player.guild.id)]['view'])
        
        # if self.vc.queue.is_empty and not self.vc.playing:
        #     await self.music_channel.send(embed=music_embed_generator(f'🎼 La playlist termino.'))
        if self.players[str(payload.player.guild.id)]['vc'].queue.is_empty and not self.players[str(payload.player.guild.id)]['vc'].playing:
            await self.players[str(payload.player.guild.id)]['music_channel'].send(embed=music_embed_generator(f'🎼 La playlist termino.'))

        # if payload.reason == 'stopped':
        #     await self.vc.disconnect(force=True)
        #     await self.reset_player()
        #     return
        if payload.reason == 'stopped':
            await self.players[str(payload.player.guild.id)]['vc'].disconnect(force=True)
            await self.reset_player(payload.player.guild.id)
            return

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        print(f'\n[+] Player in guild: {player.guild.name} is inactive.')
        print(f'[+] Player disconnected from: {player.channel}')
        await player.disconnect(force=True)
        await self.reset_player(player.guild.id)
        

    ###################################
    # - - - - C O M M A N D S - - - - #
    ###################################
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
        
        guild_id = str(ctx.guild.id)

        # if the guild_id is not in the players dictionary, add it
        if not self.players.get(guild_id): 
            self.players[guild_id] = {}

        # if the bot is not connected to a voice channel
        if not self.players[guild_id].get('vc'):
            # try to connect to the voice channel
            try:
                self.players[guild_id] = {
                    'vc': await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True, self_mute=True),
                    'music_channel': ctx.channel,
                    'user_list': [],
                    'view': None,
                    'view_message': None
                }

                # ? self.vc = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True, self_mute=True)
            except AttributeError: # if the user is not connected to a voice channel
                await ctx.send(embed=music_embed_generator('No estas conectado a un canal de voz'))
                return
            except discord.ClientException: # if the bot can't connect to the voice channel
                await ctx.send(embed=music_embed_generator('No me pude conectar a este canal de voz'))
                return
        
        # this makes the bot play the next song in the queue when the current one ends
        # and does not make any recommendations
        # ? self.vc.autoplay = wavelink.AutoPlayMode.partial
        # ? self.vc.inactive_timeout = 10
        vc = self.players[guild_id]['vc']
        user_list = self.players[guild_id]['user_list']
        # ? self.players[guild_id].vc.autoplay = wavelink.AutoPlayMode.partial
        # ? self.players[guild_id].vc.inactive_timeout = 10
        vc.autoplay = wavelink.AutoPlayMode.partial
        vc.inactive_timeout = 10

        # ? if not self.music_channel:
        # ?     self.music_channel = ctx.channel
        # ? elif self.music_channel != ctx.channel:
        # ?     await ctx.send(embed=music_embed_generator(f'No puedes usar este comando en otro canal porque el bot ya está en uso en {self.music_channel.mention}'))
        # ?     return

        # todo: perhaps this is not needed?
        # if self.players[guild_id]['music_channel'] != ctx.channel:
        #     await ctx.send(embed=music_embed_generator(f'No puedes usar este comando en otro canal porque el bot ya está en uso en {vc.music_channel.mention}'))
        #     return
                
        tracks: wavelink.Search = await wavelink.Playable.search(formated_query)

        if not tracks:
            await ctx.send(f'{ctx.author.mention} ninguna pista fue encontrada con: `{formated_query}`')

        # This is the user object that will be added to the user_list
        # adding the user to the user_list is useful to display the user's name and avatar in the playlist view
        user = await self.bot.fetch_user(ctx.author.id)
        nick = ctx.author.nick if ctx.author.nick else user.display_name
        username = user.display_name if ctx.author.nick else ctx.author.name
        user_object = {
            "name": f'{nick} ({username})', 
            "pic": user.display_avatar.url, 
            "timestamp": datetime.datetime.now()
        }
        
        if isinstance(tracks, wavelink.Playlist):
            # ? added: int = await self.vc.queue.put_wait(tracks)
            added: int = await vc.queue.put_wait(tracks)
            link = f'[{tracks.name}]({tracks.url})'
            # This codes adds the user object to the user_list multiple times
            # ? self.user_list.extend([user_object] * added) # the below code is the same as this one
            user_list.extend([user_object] * added)
            # self.user_list.extend(user_object for _ in range(added))
            await ctx.send(embed=music_embed_generator(f'Playlist {link} (**{added}** songs) ha sido agregada a la cola'))
        else:
            track: wavelink.Playable = tracks[0]
            # ? await self.vc.queue.put_wait(track)
            await vc.queue.put_wait(track)
            duration = format_time(track.length) if not track.is_stream else '🎙 live'
            description = f'Se ha agregado [{track.title}]({track.uri}) **[{duration}]** de `{track.author}`'
            # ? self.user_list.append(user_object)
            user_list.append(user_object)
            await ctx.send(embed=music_embed_generator(description))
        
        if not vc.playing:
            # ? self.vc = cast(wavelink.Player, ctx.voice_client)
            # ? await self.vc.play(self.vc.queue.get(), volume=100)
            vc = cast(wavelink.Player, ctx.voice_client)
            await vc.play(vc.queue.get(), volume=100)

            
    @commands.command(name='pause')
    async def pause(self, ctx):
        await ctx.message.delete(delay=5)
        if await check_voice_channel(ctx, self.players, paused=True):
            return

        player = self.players[str(ctx.guild.id)]

        if player['vc'].paused:
            await ctx.send(embed=music_embed_generator('La canción ya está pausada'))
            return

        await player['vc'].pause(True)
        player['view'].children[2].label = 'Resumir'
        player['view'].children[2].emoji = '<:mb_resume:1244545666982744119>'
        player['view'].paused = True
        await player['view_message'].edit(view=player['view'])

    @commands.command(name='resume')
    async def resume(self, ctx):
        await ctx.message.delete(delay=5)
        if await check_voice_channel(ctx, self.players, paused=True):
            return

        player = self.players[str(ctx.guild.id)]

        if not player['vc'].paused:
            await ctx.send(embed=music_embed_generator('La canción ya está sonando'))
            return

        await player['vc'].pause(False)
        player['view'].children[2].label = 'Pausar'
        player['view'].children[2].emoji = '<:mb_pause:1244545668563861625>'
        player['view'].paused = False
        await player['view_message'].edit(view=player['view'])

    @commands.command(name='current')
    async def current(self, ctx):
        if await check_voice_channel(ctx, self.players):
            return
        
        vc = self.players[str(ctx.guild.id)]['vc']
        user_list = self.players[str(ctx.guild.id)]['user_list']
        track = vc.current
        current_position = format_time(int(vc.position))

        embed = now_playing(track, user=user_list[0] if user_list else None, current=True, position=current_position)

        await ctx.send(embed=embed)

    @commands.command(name='playlist')
    async def playlist(self, ctx):
        if await check_voice_channel(ctx, self.players):
            return
        
        view = PlaylistView(timeout=None)
        view.vc = self.vc
        view.music_channel = self.music_channel
        await view.send()
    
    @commands.command(name='skip')
    async def skip(self, ctx):
        if await check_voice_channel(ctx, self.players):
            return
        
        if self.vc.queue.is_empty:
            channel = self.vc.channel.mention
            remove_all_items(self.view)
            await self.view_message.edit(view=self.view)            
            self.vc.queue.clear()
            await self.vc.stop()
            await ctx.send(embed=music_embed_generator(f'🎼 La playlist termino.'))
            return

        await self.vc.play(self.vc.queue.get())

    @commands.command(name='stop')
    async def stop(self, ctx):
        if await check_voice_channel(ctx, self.players):
            return
        
        self.vc.queue.clear()
        remove_all_items(self.view)
        await self.view_message.edit(view=self.view)
        await self.vc.stop()
        await ctx.send(embed=music_embed_generator('Playlist detenida'))

    @commands.command(name='disconnect')
    async def disconnect(self, ctx):
        if await check_voice_channel(ctx, self.players):
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