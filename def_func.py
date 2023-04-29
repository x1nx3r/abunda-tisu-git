import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv('tokens.env')

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# create a Spotify client object with credentials
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

async def get_song_url(song_name):
    # search for the song using the Spotify API
    results = sp.search(q=f'track:{song_name}', type='track')

    # extract the first song result's URL
    song_url = results['tracks']['items'][0]['external_urls']['spotify']

    return song_url

async def get_playlist_songs(playlist_name):
    # search for the playlist using the Spotify API
    results = sp.search(q=f'playlist:{playlist_name}', type='playlist')

    # extract the first playlist result's ID
    playlist_id = results['playlists']['items'][0]['id']

    # get the tracks in the playlist using the Spotify API
    tracks = sp.playlist_tracks(playlist_id, fields='items(track(name))')

    # extract the names of the songs in the playlist, in order
    song_names = [track['track']['name'] for track in tracks['items']]

    # return the list of song names
    return song_names

async def convert_to_url(array):
    urllist = []
    for song_name in array:
        song_url = get_song_url(song_name)
        urllist.append(song_url)
    return urllist

async def get_track_info(song_name):
    results = sp.search(q=song_name, type='track')
    items = results['tracks']['items']
    if not items:
        print(f"No results found for '{song_name}'")
        return []

    track = items[0]
    track_info = [
        track['name'],
        track['artists'][0]['name'],
        track['album']['name']
    ]

    return track_info