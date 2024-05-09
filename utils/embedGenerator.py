import discord

def music_embed_generator(description):
    embed = discord.Embed(
        colour = discord.Colour.blurple(),
        description = description
    )

    return embed