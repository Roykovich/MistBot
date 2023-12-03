import discord
import random
import typing
from discord.ext import commands
from discord import app_commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # roll command
    # gives a random number from 1 to 1000
    @app_commands.command(name='roll', description='Rolls a random number from 1 to 100') 
    async def roll(self, interaction: discord.Interaction):
        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'🎲 {interaction.user.mention} rolls `{random.randint(1, 100)}`!'
        )
        await interaction.response.send_message(embed=embed)

    # choose command
    # picks randomly a given item
    @app_commands.command(name='choose', description='Picks randomly a given item. Use / to separate the items')
    @app_commands.describe(choices='choices')
    async def choose(self, interaction: discord.Interaction, choices: str):
        choices = choices.split(' / ')
        
        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'Deberias escoger `{random.choice(choices)}` ☝🏻'
        )

        await interaction.response.send_message(embed=embed)

    # rate command
    # rates something you give to the bot
    @app_commands.command(name='rate', description='Rates something')
    @app_commands.choices(modo=[
        app_commands.Choice(name='normal', value=10),
        app_commands.Choice(name='chileno', value=7),
    ])
    @app_commands.describe(cosa='choice')
    async def rate(self, interaction: discord.Interaction, modo: app_commands.Choice[int], cosa: str):
        embed = discord.Embed(
            colour = discord.Colour.dark_purple(),
            description = f'Hmmmm {cosa} es como `{random.randint(1, modo.value)}/{modo.value}`'
        )

        await interaction.response.send_message(embed=embed)
    
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