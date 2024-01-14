import discord
import random
import sqlite3
import uuid
import re
from discord.ext import commands
from discord import app_commands

# Adapters and converters
# Turns the uuid into a byte array
sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)
# Turns the byte array into a uuid
sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))

connection = sqlite3.connect('custom_reactions.db', isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
db = connection.cursor()

# Create a table in custom_reactions.db if it doesn't exist
db.execute('CREATE TABLE IF NOT EXISTS reactions (trigger text, response text, cr_id GUID)')

class CustomReactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        parsed = message.content.lower()

        if message.author.bot or message.author == self.bot.user:
            return
        
        if message.content.startswith(self.bot.command_prefix):
            return

        if re.search(r"([rg](ubén|uben|euben|uben|unerd|oy),? (arregla|repara|fixea|bichea|acomoda) [ts]u (maldit[ao]|put[ao]|verga?|estupid[ao])?\s?(mierda|vaina|verga|bot|perol|robot))", parsed):
            await message.add_reaction('😡')
            await message.channel.send('Esta ocupado.')
            return

        link = re.search(r"(?:^http(?:s)?://)?(?:\w+\.)?(\w*)\.(?:\w*)/.*", parsed)
        if link:
            domain = link.group(1)
            if re.search(r"^(instagram|twitter|tiktok|reddit)$", domain):
                await message.add_reaction('😦')
                await message.channel.send(f'deberias probar el comando `{self.bot.command_prefix}ef` para arreglar ese link y que sea más accesible')


        # la coma en (parsed,) es para que sea una tupla, si no, no funciona, no se porque
        cr = db.execute('SELECT response FROM reactions WHERE trigger = ?', (parsed,)).fetchall()
        if len(cr) > 0:
            await message.channel.send(random.choice(cr)[0])
            return
        
        return
        

    #####################################
    #             Commands              #
    #####################################
            
    @commands.command('acr', help='Adds a custom reaction to the database')
    async def addcr(self, ctx, *args):
        if not args or (len(args) < 2):
            await ctx.send(f'Faltan argumentos. Intenta `{self.bot.command_prefix}acr <trigger> <response>`')
            return
        
        if (len(args) > 2):
            await ctx.send(f'sobran argumentos. Intenta `{self.bot.command_prefix}acr <trigger> <response>`')
            return
        
        trigger = args[0].lower()
        response = args[1]
        cr_id = uuid.uuid4()

        db.execute('INSERT INTO reactions (trigger, response, cr_id) VALUES (?, ?, ?)', (trigger, response, cr_id))

        embed = discord.Embed(title='Reacción agregada', description=f'`{cr_id}`', color=discord.Colour.dark_purple())
        embed.add_field(name='Trigger', value=trigger, inline=False)
        embed.add_field(name='Response', value=response, inline=False)

        await ctx.send(embed=embed)

        return
    
    @commands.command('dcr', help='Deletes a custom reaction from the database')
    async def delcr(self, ctx, *args):
        if not args:
            await ctx.send(f'Faltan argumentos. Intenta `{self.bot.command_prefix}dcr <id>. Para revisar los ids usa `{self.bot.command_prefix}lcr`')
            return
        
        try:
            cr_uuid = uuid.UUID(args[0])
            parsed_uuid = cr_uuid.bytes_le
            
            db.execute('DELETE FROM reactions WHERE cr_id = ?', (parsed_uuid,))
            
            embed = discord.Embed(title='Reacción eliminada', description=f'`{cr_uuid}`', color=discord.Colour.dark_purple())
            
            await ctx.send(embed=embed)

            return
        except ValueError:
            await ctx.send(f'El id no es válido. Para revisar los ids usa `{self.bot.command_prefix}lcr`')
            return
    
    @commands.command('lcr', help='Lists all the custom reactions')
    async def listcr(self, ctx, *args):
        rows = db.execute('SELECT trigger, cr_id FROM reactions')
        
        for row in rows:
            print(row[1], row[0])
        return
                

async def setup(bot):
    await bot.add_cog(CustomReactions(bot))