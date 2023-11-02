import discord
from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    #
    #
    @commands.command(name='play')
    async def play(self, ctx):
        await ctx.send('play something!')


async def setup(bot):
    await bot.add_cog(Music(bot))