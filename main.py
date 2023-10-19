import discord, random
from discord.ext import commands

# Settings
import settings

# My cogs
from cogs.basic import Basic

def main():
    intents = discord.Intents.default()
    intents.message_content = True

    # create the bot instance with prefix and intenst so far
    bot = commands.Bot(command_prefix='f!', intents=intents)

    """Events"""
    @bot.event
    async def on_ready():
        print(f'We have logged in as {bot.user}')

        await bot.load_extension("cogs.basic")

    @bot.event
    async def on_member_join(member: discord.member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome aboard {member.mention}')
        

    bot.run(settings.TOKEN)


if __name__ == '__main__':
    main()