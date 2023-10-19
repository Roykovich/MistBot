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
        await ctx.send(f'🎲 {ctx.message.author.mention} rolls {random.randint(1, 100)}')

    # choose command
    # picks randomly a given item
    @commands.command(name='choose') 
    async def choose(self, ctx, *choices: str):
        if not choices or len(choices) < 2:
            return await ctx.send('Give me two or more things to pick')
        
        await ctx.send(f'You should pick `{random.choice(choices)}`')

    @commands.command()
    async def rate(self, ctx, *choices: str):
        if not choices or len(choices) == 1 and choices[0] == 'chileanway':
            return await ctx.send('Give me something to rate')

        if choices[0] == 'chileanway':
            return await ctx.send(f'{random.randint(1, 7)}/7')

        return await ctx.send(f'{random.randint(1, 10)}/10')
            


async def setup(bot):
    await bot.add_cog(Basic(bot))