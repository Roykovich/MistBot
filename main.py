import discord, random
from discord.ext import commands

# Settings
import settings

# My cogs
from cogs.basic import Basic
# from cogs.music import Music
from cogs.musicv2 import Music

def main():
    intents = discord.Intents.default()
    intents.message_content = True

    # create the bot instance with prefix and intenst so far
    bot = commands.Bot(command_prefix='m!', intents=intents)

    """Events"""
    @bot.event
    async def on_ready():
        print(f'\n[+] We have logged in as {bot.user}\n')

        for cog_file in settings.COGS_DIR.glob('*.py'):
            if cog_file != "__init__.py":
                await bot.load_extension(f'cogs.{cog_file.name[:-3]}')
                print('[+] Loaded cog: ' + cog_file.name[:-3])
                
        bot.tree.copy_global_to(guild=settings.GUILD_ID)
        await bot.tree.sync(guild=settings.GUILD_ID)


    @bot.event
    async def on_member_join(member: discord.member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome aboard {member.mention}')

    bot.run(settings.TOKEN)


if __name__ == '__main__':
    main()