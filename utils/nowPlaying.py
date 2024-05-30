import discord
import wavelink
from utils.formatTime import format_time

def now_playing(track: wavelink.Playable, user = None, current: bool = False, position: int = 0, peek: bool = False):
    duration = format_time(track.length) if not track.is_stream else '🎙 live'
    thumbnail = track.artwork

    embed = discord.Embed(
        colour = discord.Colour.blurple(),
        description = f'[{track.title}]({track.uri})',
        timestamp = user["timestamp"] if user else None
    )

    author = f'🎵 | Va a sonar' if peek else f'🎵 | Ahora suena'

    if user:
        embed.set_author(name=author, icon_url=user["pic"])
        embed.set_footer(text=f'Solicitado por {user["name"]}')
    else:
        embed.set_author(name='🎵 | Ahora suena')

    if current:
        embed.add_field(name='Duración', value=f'`{position}/{duration}`', inline=True)
    else:
        embed.add_field(name='Duración', value=f'`{duration}`', inline=True)

    embed.add_field(name='Autor:', value=f'`{track.author}`', inline=True)
    embed.set_thumbnail(url=thumbnail)

    return embed
