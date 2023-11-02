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
        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'🎲 {ctx.message.author.mention} rolls `{random.randint(1, 100)}`!'
        )
        await ctx.send(embed=embed)


    # choose command
    # picks randomly a given item
    @commands.command(name='choose') 
    async def choose(self, ctx, *choices: str):
        if not choices or len(choices) < 2:
            return await ctx.send('Give me two or more things to pick')
        
        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'You should pick `{random.choice(choices)}` ☝🏻'
        )

        await ctx.send(embed=embed)

    # rate command
    # rates something you give to the bot
    @commands.command(name='rate')
    async def rate(self, ctx, *choices: str):
        if not choices or len(choices) == 1 and choices[0] == 'chileanway':
            return await ctx.send('Give me something to rate')
        
        random_int = None

        if choices[0] == 'chileanway':
            random_int = f'{random.randint(1, 7)}/7'
        else:
            random_int = f'{random.randint(1, 10)}/10'

        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'Hmmm I give it a `{random_int}`'
        )

        return await ctx.send(embed=embed)
    

    # avatar command
    # it returns the avatar of a mentioned user, if no mention returns the author's avatar
    @commands.command(name='avatar')
    async def info(self, ctx):
        user = None
        avatar = None

        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = ''
        )

        # if the user does not mention anyone, return its own info
        if not ctx.message.mentions:
            user = await self.bot.fetch_user(ctx.author.id)
            avatar = user.display_avatar.url
            embed.set_image(url=avatar)
            await ctx.send(embed=embed)
            await ctx.send('If you wanted to see other people profile picture try: f!avatar @username. Add more mentions if u want to see more pictures at once.')
        
        else:
            mentions = [user_mentioned.id for user_mentioned in ctx.message.mentions]
            for mention in mentions:
                user = await self.bot.fetch_user(mention)
                avatar = user.display_avatar.url
                embed.set_image(url=avatar)
                await ctx.send(embed=embed)
    
    # poll command
    # creates a command with a max number of 12 options
    @commands.command(name='poll')
    async def poll(self, ctx, *args):
        options = args
        letters = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯'];

        if len(args) <= 2: return ctx.send('Add more choices please! (maximun 10)')
        if len(args) > 11: return ctx.send('You added to much choices, please use the maximun: **10**')

        await ctx.message.delete(delay=1)

        poll = {
            'question': options[0],
            'options': options[1:]
        }
        
        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = ''
        )

        embed.set_author(name=poll['question'])

        for index, option in enumerate(poll['options']):
            embed.description += f'{letters[index]}** - {option}**\n'

        embed_sent = await ctx.send(content=f'@everyone heeeey!\n<@!{ctx.author.id}> has started a poll: **{poll["question"]}**', embed=embed)

        for index in range(len(poll['options'])):
            await embed_sent.add_reaction(letters[index])
        

async def setup(bot):
    await bot.add_cog(Basic(bot))