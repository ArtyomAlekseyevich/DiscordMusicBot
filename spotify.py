import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "YOUR_SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "YOUR_SPOTIFY_CLIENT_SECRET")

spotify = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    sp_credentials = SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
    spotify = spotipy.Spotify(client_credentials_manager=sp_credentials)

def is_spotify_link(url: str) -> bool:
    return "open.spotify.com" in url

def process_spotify_link(url: str) -> str:
    if spotify is None:
        return None
    try:
        track = spotify.track(url)
        track_name = track['name']
        artists = ", ".join(artist['name'] for artist in track['artists'])
        return f"{track_name} {artists}"
    except Exception as e:
        return None