import discord, json, sys, random
import os.path

from discord.ext import commands

TOKEN = None
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# create the bot instance with prefix and intenst so far
bot = commands.Bot(command_prefix='f!', intents=intents)

# ensure that the config file exists
if os.path.exists('config.json'):

    # open and set the json file into a dict
    json_file = open('config.json')
    json_dict = json.load(json_file)
    
    # we extract the token from config
    TOKEN = json_dict['token']

    # Error
    if not TOKEN:
        print('Theres no token in config.json')
        sys.exit(1)
    
    json_file.close()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# roll command
# gives a random number from 1 to 1000
@bot.command(name='roll') 
async def roll(ctx):
    await ctx.send(random.randint(1, 100))

# choose command
# picks randomly a given item
@bot.command(name='choose') 
async def choose(ctx, *choices: str):
    await ctx.send(f'You should pick {random.choice(choices)}')
    

bot.run(TOKEN)