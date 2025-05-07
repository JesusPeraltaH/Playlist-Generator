# En spotify_api.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv, find_dotenv
import random
import webbrowser

# Load environment variables
load_dotenv(find_dotenv())

def connect_to_spotify(app):
    try:
        auth_manager = SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri='SPOTIFY_REDIRECT_URI',
            scope='playlist-modify-public playlist-modify-private user-read-private user-top-read'
        )
        app.sp = spotipy.Spotify(auth_manager=auth_manager)
        app.log("Conectado exitosamente a Spotify")
    except Exception as e:
        app.log(f"Error al conectar a Spotify: {e}")

def reconnect_spotify_api(app):
    try:
        if app.sp:
            # If the token has expired, SpotifyOAuth should handle refreshing it
            user = app.sp.me()
            app.log(f"Reconectado exitosamente a Spotify como {user['display_name']}")
        else:
            connect_to_spotify(app)
    except Exception as e:
        app.log(f"Error al reconectar a Spotify: {e}")

def search_spotify_artist(app, artist_name):
    if not app.sp:
        app.log("No conectado a Spotify para buscar artista.")
        return None
    try:
        results = app.sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
        if results['artists']['items']:
            return results['artists']['items'][0]
    except Exception as e:
        app.log(f"Error al buscar artista en Spotify: {e}")
    return None

def clean_track_data(track):
    """Función auxiliar para limpiar los datos del track."""
    def clean_value(value):
        if not value:
            return ''
        # Eliminar llaves y espacios extra
        value = str(value).strip('{}').strip()
        # Si el valor está vacío después de limpiar, retornar cadena vacía
        return value if value else ''

    track_data = {
        'name': clean_value(track.get('name', '')),
        'artist': clean_value(track['artists'][0].get('name', '')) if track.get('artists') else '',
        'album': clean_value(track.get('album', {}).get('name', '')),
        'uri': clean_value(track.get('uri', '')),
        'image_url': None
    }

    if track.get('album') and track['album'].get('images'):
        track_data['image_url'] = track['album']['images'][-1]['url']

    return track_data

def get_suggestions_from_api(app, artists, callback):
    if not app.sp:
        app.log("No conectado a Spotify para obtener sugerencias.")
        return
    if not artists:
        app.log("No hay artistas para obtener sugerencias.")
        return

    suggested_tracks_data = []
    try:
        for artist_name in artists:
            try:
                artist_results = app.sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
                if not artist_results['artists']['items']:
                    app.log(f"No se encontró el artista: {artist_name}")
                    continue
                
                artist_id = artist_results['artists']['items'][0]['id']
                app.log(f"Obteniendo sugerencias para: {artist_name}")
                
                # Conjunto para evitar duplicados
                seen_uris = set()
                
                # 1. Obtener top tracks del artista
                try:
                    top_tracks = app.sp.artist_top_tracks(artist_id=artist_id, country='US')
                    if top_tracks and 'tracks' in top_tracks:
                        for track in top_tracks['tracks']:
                            if track['uri'] not in seen_uris:
                                seen_uris.add(track['uri'])
                                try:
                                    track_data = clean_track_data(track)
                                    if track_data['name'] and track_data['uri']:
                                        suggested_tracks_data.append(track_data)
                                except Exception as e:
                                    app.log(f"Error al procesar track: {e}")
                                    continue
                except Exception as e:
                    app.log(f"Error al obtener top tracks para {artist_name}: {e}")

                # 2. Obtener álbumes recientes (limitado a 2)
                try:
                    albums = app.sp.artist_albums(artist_id=artist_id, album_type='album', limit=2)
                    if albums and 'items' in albums:
                        for album in albums['items']:
                            try:
                                album_tracks = app.sp.album_tracks(album['id'])
                                if album_tracks and 'items' in album_tracks:
                                    for track in album_tracks['items']:
                                        if track['uri'] not in seen_uris:
                                            seen_uris.add(track['uri'])
                                            try:
                                                track_data = clean_track_data(track)
                                                if track_data['name'] and track_data['uri']:
                                                    suggested_tracks_data.append(track_data)
                                            except Exception as e:
                                                continue
                            except Exception as e:
                                continue
                except Exception as e:
                    app.log(f"Error al obtener álbumes para {artist_name}: {e}")

                # 3. Obtener singles recientes (limitado a 2)
                try:
                    singles = app.sp.artist_albums(artist_id=artist_id, album_type='single', limit=2)
                    if singles and 'items' in singles:
                        for single in singles['items']:
                            try:
                                single_tracks = app.sp.album_tracks(single['id'])
                                if single_tracks and 'items' in single_tracks:
                                    for track in single_tracks['items']:
                                        if track['uri'] not in seen_uris:
                                            seen_uris.add(track['uri'])
                                            try:
                                                track_data = clean_track_data(track)
                                                if track_data['name'] and track_data['uri']:
                                                    suggested_tracks_data.append(track_data)
                                            except Exception as e:
                                                continue
                            except Exception as e:
                                continue
                except Exception as e:
                    app.log(f"Error al obtener singles para {artist_name}: {e}")

            except Exception as e:
                app.log(f"Error al procesar el artista {artist_name}: {e}")
                continue

        # Limitar a 30 sugerencias
        suggested_tracks_data = suggested_tracks_data[:30]

        if suggested_tracks_data:
            app.log(f"Se encontraron {len(suggested_tracks_data)} sugerencias en total.")
        else:
            app.log("No se encontraron sugerencias para ningún artista.")
        
        callback(suggested_tracks_data)

    except Exception as e:
        app.log(f"Error general al obtener sugerencias de Spotify: {e}")
        callback([])
    

def create_spotify_playlist(app, playlist_name, track_uris):
    if not app.sp:
        app.log("No conectado a Spotify para crear playlist.")
        return

    try:
        user = app.sp.current_user()
        playlist = app.sp.user_playlist_create(user['id'], playlist_name, public=False, description=f"Playlist creada con base en las sugerencias.")

        if track_uris:
            app.sp.playlist_add_items(playlist['id'], track_uris)
            app.log(f"Se añadieron {len(track_uris)} canciones a la playlist '{playlist_name}'.")
        else:
            app.log(f"Playlist '{playlist_name}' creada sin canciones.")

        webbrowser.open(playlist['external_urls']['spotify'])

    except Exception as e:
        app.log(f"Error al crear la playlist en Spotify: {e}")

def get_playlist_tracks_from_api(app, playlist_id, callback):
    if not app.sp:
        app.log("No conectado a Spotify para obtener las pistas de la playlist.")
        return

    tracks_data = []
    try:
        results = app.sp.playlist_items(playlist_id)
        tracks = results['items']
        while results['next']:
            results = app.sp.next(results) 
            tracks.extend(results['items'])

        for item in tracks:
            if item['track']:
                tracks_data.append({
                    'name': item['track']['name'],
                    'artist': item['track']['artists'][0]['name'],
                    'album': item['track']['album']['name'],
                    'uri': item['track']['uri']
                })

        app.log(f"Se encontraron {len(tracks_data)} pistas en la playlist con ID: {playlist_id}")
        callback(tracks_data)

    except spotipy.exceptions.SpotifyException as e:
        app.log(f"Error al obtener las pistas de la playlist: {e}")
        callback([])
    except Exception as e:
        app.log(f"Error inesperado al obtener las pistas de la playlist: {e}")
        callback([])