import discord
from utils.EmbedGenerator import music_embed_generator

async def check_voice_channel(ctx, players, paused=False)-> bool:
    guild_id = str(ctx.guild.id)
    player = players.get(guild_id)
    if not ctx.author.voice:
        await ctx.send(embed=music_embed_generator('No estás conectado a ningún canal de voz.'), delete_after=5)
        return True
    
    if player is None:
        await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento.'), delete_after=5)
        return True
    
    if ctx.author.voice.channel != player['vc'].channel:
        await ctx.send(embed=music_embed_generator('No estás conectado al mismo canal de voz que el bot.'), delete_after=5)
        return True

    return False