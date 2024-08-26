import requests

    # Hacer request al servidor local donde esta lavalink (127.0.0.1:2333) y seguir el path de lavalyrics
        # GET /v4/sessions/{sessionId}/players/{guildId}/track/lyrics?skipTrackSource={skipTrackSource}
        # Para conseguir que el servidor de lavalink nos devuelva la letra de la cancion
        # skipTrackSource es un parametro opcional que si es true, no devuelve la fuente de la cancion
        # la sp_dc cookie esta en la web en applications > cookies > spotify.com > sp_dc

        # Hay que crear un sistema para que el bot detecte de donde es la fuente de las letras y asi poder
        # formatear las letras de manera correcta

def get_lyrics(session_id, guild_id, lavalink_password):
    # headers
    headers = {
        'Authorization': lavalink_password
    }
    url = f'http://localhost:2333/v4/sessions/{session_id}/players/{guild_id}/track/lyrics?skipTrackSource=true'
    # request hacia el servidor de lavalink para encontrar las letras con el plugin de lyrics
    lyrics = requests.get(url=url, headers=headers)
    # Si ninguna letra es encontrada, retornar None
    if lyrics.status_code != 200:
        return None
    
    lyrics = lyrics.json()
    # Si la fuente es YouTube la letra se encuentra en la llave 'text'
    if lyrics['sourceName'] == 'youtube':
        return lyrics['text']
    # Si la fuente es Spotify la letra se encuentra en un array de objetos con la llave 'line'    
    if lyrics['sourceName'] == 'spotify':
        lyrics_found = ''
        for line in lyrics['lines']:
            lyrics_found += line['line'] + '\n'

        return lyrics_found
