import discord
import wavelink
from utils.formatTime import format_time

def now_playing(track: wavelink.Playable, current: bool = False, position: int = 0):
    duration = format_time(track.length) if not track.is_stream else '🎙 live'
    thumbnail = track.artwork

    embed = discord.Embed(
        colour = discord.Colour.blurple(),
        description = f'[{track.title}]({track.uri})'
    )
    embed.set_author(name='🎵 | Ahora suena')

    if current:
        embed.add_field(name='Duración', value=f'`{position}/{duration}`', inline=True)
    else:
        embed.add_field(name='Duración', value=f'`{duration}`', inline=True)

    embed.add_field(name='Autor:', value=f'`{track.author}`', inline=True)
    embed.set_thumbnail(url=thumbnail)

    return embed
