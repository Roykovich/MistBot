import pathlib, sys, os.path, json

BASE_DIR = pathlib.Path(__file__).parent

COMMANDS_DIR = BASE_DIR / 'commands'

TOKEN = None

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