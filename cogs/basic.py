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

async def setup(bot):
    await bot.add_cog(Basic(bot))