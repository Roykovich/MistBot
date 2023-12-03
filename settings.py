import pathlib, sys, os.path, json
import discord

BASE_DIR = pathlib.Path(__file__).parent

COMMANDS_DIR = BASE_DIR / 'commands'
COGS_DIR = BASE_DIR / 'cogs'

TOKEN = None
MUSIC_PASS = None
SPOTIFY_ID = None
SPOTIFY_SECRET = None

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

    # we extract the password of lavalink server
    MUSIC_PASS = json_dict['lavalink']

    if not MUSIC_PASS:
        print('Theres no lavalink password in config.json')
        sys.exit(1)

    SPOTIFY_ID = json_dict['spotify_id']

    if not SPOTIFY_ID:
        print('Theres no spotfy id in config.json')
        sys.exit(1)

    SPOTIFY_SECRET = json_dict['spotify_secret']

    if not SPOTIFY_SECRET:
        print('Theres no spotify secret in config.json')
        sys.exit(1)
    
    GUILD_ID = discord.Object(id=int(json_dict['guild_id']))

    if not SPOTIFY_SECRET:
        print('Theres no guild id in config.json')
        sys.exit(1)
    
    
    json_file.close()