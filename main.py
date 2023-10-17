import discord, json, sys
import os.path

TOKEN = None
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

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


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(TOKEN)