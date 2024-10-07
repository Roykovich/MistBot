import discord
from discord.ext import commands
from utils.EmbedGenerator import music_embed_generator

async def check_voice_channel(ctx, players)-> bool:
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

def check_voice_channel_v2(players):
    async def predicate(ctx):
        guild_id = str(ctx.guild.id)
        player = players.get(guild_id)
        if not ctx.author.voice:
            await ctx.send(embed=music_embed_generator('No estás conectado a ningún canal de voz.'), delete_after=5)
            return False

        if player is None:
            await ctx.send(embed=music_embed_generator('No hay ninguna canción sonando en este momento.'), delete_after=5)
            return False

        if ctx.author.voice.channel != player['vc'].channel:
            await ctx.send(embed=music_embed_generator('No estás conectado al mismo canal de voz que el bot.'), delete_after=5)
            return False
        
        return True
    
    return commands.check(predicate)