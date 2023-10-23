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

    @commands.command(name='rate')
    async def rate(self, ctx, *choices: str):
        if not choices or len(choices) == 1 and choices[0] == 'chileanway':
            return await ctx.send('Give me something to rate')

        if choices[0] == 'chileanway':
            return await ctx.send(f'{random.randint(1, 7)}/7')

        return await ctx.send(f'{random.randint(1, 10)}/10')
    
    
    @commands.command(name='avatar')
    async def info(self, ctx):
        user = None
        avatar = None

        # if the user does not mention anyone, return its own info
        if not ctx.message.mentions:
            user = await self.bot.fetch_user(ctx.author.id)
            avatar = user.display_avatar.url
            await ctx.send(avatar)
            await ctx.send('If you wanted to see other people profile picture try: f!avatar @username. Add more mentions if u want to see more pictures at once.')
        
        else:
            mentions = [user_mentioned.id for user_mentioned in ctx.message.mentions]
            for mention in mentions:
                user = await self.bot.fetch_user(mention)
                avatar = user.display_avatar.url

                await ctx.send(avatar)      
    

async def setup(bot):
    await bot.add_cog(Basic(bot))