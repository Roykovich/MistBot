import discord
import re
from discord.ext import commands
from discord import app_commands

class Media(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ef', help='fixear embeds de twitter, reddit e instagram')
    async def tfix(self, ctx, *url: str):
        if url: 
            domain = re.search(r"(?:^http(?:s)?://)?(?:\w+\.)?(twitter|reddit|instagram)\.(?:\w*)/.*", url[0])

            if not domain:
                await ctx.send('No se encontro ningun link.')
                return

            match domain.group(1):
                case 'twitter':
                    await ctx.send(url[0].replace('https://twitter.com/', 'https://fixvx.com/'))
                case 'x':
                    await ctx.send(url[0].replace('https://x.com/', 'https://fixvx.com/'))
                case 'reddit':
                    await ctx.send(url[0].replace('https://www.reddit.com/', 'https://rxddit.com/'))
                case 'instagram':
                    await ctx.send(url[0].replace('https://www.instagram.com/', 'https://ddinstagram.com/'))
                case _:
                    await ctx.send('No se puede arreglar ese link. Solo se pueden arreglar links de Twitter, Reddit e Instagram.')
                    return


        messages = [message async for message in ctx.channel.history(limit=10)]
        for message in messages[1:]:
            if message.author.bot:
                continue
            content = message.content
            domain = re.search(r"(?:^http(?:s)?://)?(?:\w+\.)?(\w*)\.(?:\w*)/.*", content)

            if not domain:
                continue

            match domain.group(1):
                case 'twitter':
                    await ctx.send(content.replace('https://twitter.com/', 'https://fixvx.com/'))
                    return
                case 'x':
                    await ctx.send(content.replace('https://x.com/', 'https://fixvx.com/'))
                    return
                case 'reddit':
                    await ctx.send(content.replace('https://www.reddit.com/', 'https://rxddit.com/'))
                    return
                case 'instagram':
                    await ctx.send(content.replace('https://www.instagram.com/', 'https://ddinstagram.com/'))
                    return
                case _:
                    continue
        
        await ctx.send('No se encontro ningun link en los ultimos 10 mensajes.')


async def setup(bot):
    await bot.add_cog(Media(bot))