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


class TriggersView(discord.ui.View):
    # The current page of the playlist
    current_page: int = 1
    # The separator of the playlist, in this case is 10 tracks per page
    separator: int = 10
    triggers = db.execute('SELECT trigger, cr_id FROM reactions')

    # Sends the playlist to the channel where the command was invoked from 
    async def send(self, ctx):
        self.message = await ctx.send(view=self)
        await self.update_message(list(self.triggers)[:self.separator])

    # Creates the embed of the playlist
    async def create_embed(self, triggers):
        embed = discord.Embed(title='Triggers', color=discord.Colour.dark_purple())
        embed.description = ''

        print(triggers)
        for trigger in triggers:
            embed.description += f'`{trigger[1]}` | {trigger[0]}\n'

        return embed

    # Updates the message of the playlist
    async def update_message(self, data):
        self.update_buttons()
        embed = await self.create_embed(data)
        await self.message.edit(embed=embed, view=self)

    # Updates the buttons of the playlist
    def update_buttons(self):
        if self.current_page == 1:
            self.previous.disabled = True
            self.previous.style = discord.ButtonStyle.grey
        else:
            self.previous.disabled = False
            self.previous.style = discord.ButtonStyle.primary
        
        if self.current_page == int(len(list(self.triggers)) / self.separator) + 1:
            self.next.disabled = True
            self.next.style = discord.ButtonStyle.grey
        else:
            self.next.disabled = False
            self.next.style = discord.ButtonStyle.primary

    # Gets the current page of the playlist
    def get_current_page(self):
        until_page = self.current_page * self.separator
        from_page = until_page - self.separator

        if self.current_page == 1:
            from_page = 0
            until_page = self.separator
        
        if self.current_page == int(len(list(self.triggers)) / self.separator) + 1:
            from_page = self.current_page - 1 * self.separator - self.separator
            until_page = len(self.triggers)

        return list(self.triggers)[from_page:until_page]


    @discord.ui.button(label='Anterior', emoji='⬅️', style=discord.ButtonStyle.gray, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.get_current_page())

    @discord.ui.button(label='Siguiente', emoji='➡️', style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.get_current_page())

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

        if re.search(r"([rg](ubén|uben|euben|uben|unerd|oy),? (arregla|repara|fixea|bichea|acomoda|mejora|upgradea|optimiza|soluciona|resuelve) [ts]u (maldit[ao]|put[ao]|verga?|estupid[ao])?\s?(mierda|vaina|verga|bot|perol|robot))", parsed):
            await message.add_reaction('😡')
            await message.channel.send('Está ocupado.')
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
        view = TriggersView(timeout=15)
        await view.send(ctx)
        return
                

async def setup(bot):
    await bot.add_cog(CustomReactions(bot))