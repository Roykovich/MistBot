import random
import discord
from discord.ext import commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # roll command
    # gives a random number from 1 to 1000
    @commands.command(name='roll') 
    async def roll(self, ctx):
        await ctx.send(random.randint(1, 100))

    # choose command
    # picks randomly a given item
    @commands.command(name='arepa') 
    async def choose(self, ctx, *choices: str):
        await ctx.send(f'You should pick {random.choice(choices)}')


async def setup(bot):
    await bot.add_cog(Basic(bot))