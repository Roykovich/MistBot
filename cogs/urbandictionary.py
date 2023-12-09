import discord
import requests

from datetime import datetime
from discord.ext import commands
from discord import app_commands

URL = "https://api.urbandictionary.com/v0/define?term="

class Urban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="urban", description="Searches Urban Dictionary for a word or phrase")
    @app_commands.describe(search="Search term")
    async def urban(self, interaction: discord.Interaction, search: str):
        response = requests.get(URL + search.replace(" ", "+")).json()

        if response["list"]:
            first = response["list"][0]
            date = datetime.fromisoformat(first["written_on"][:-1])
            definition = first['definition'].replace("[", "**").replace("]", "**")
            example = first['example'].replace("[", "**").replace("]", "**")
            thumbs = f"👍 {first['thumbs_up']} | 👎 {first['thumbs_down']}"

            embed = discord.Embed(
                colour = discord.Colour.dark_purple(),
                title = search,
                url= first["permalink"],
                description = f"**Definition:**\n{definition}\n\n**Example:**\n{example}\n\nby **{first['author']}** on **{date.strftime('%B %d, %Y')}**\n\n{thumbs}"
            )

            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/731987400863252502/1183089907493769387/2560px-Urban_Dictionary_logo.png?ex=65871156&is=65749c56&hm=fb60f6a852eef6f809318052d941560c0f58a729d5ef6963533d126c406476b6&')
            embed.set_author(name='Urban Dictionary', url='https://www.urbandictionary.com')
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                colour = discord.Colour.dark_purple(),
                title = search,
                description = f"No results found"
            )

            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/731987400863252502/1183089907493769387/2560px-Urban_Dictionary_logo.png?ex=65871156&is=65749c56&hm=fb60f6a852eef6f809318052d941560c0f58a729d5ef6963533d126c406476b6&')
            embed.set_author(name='Urban Dictionary', url='https://www.urbandictionary.com')
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Urban(bot))
