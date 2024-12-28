import pathlib, sys, os, json
import discord
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = pathlib.Path(__file__).parent

COMMANDS_DIR = BASE_DIR / 'commands'
COGS_DIR = BASE_DIR / 'cogs'

TOKEN = os.getenv("TOKEN")
MUSIC_PASS = os.getenv('LAVALINK')
SPOTIFY_ID = os.getenv('SPOTIFY_ID')
SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
GUILD_ID = discord.Object(id=int(os.getenv('GUILD_ID')))
ZOLOK_ID = int(os.getenv("ZOLOK_ID"))
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
