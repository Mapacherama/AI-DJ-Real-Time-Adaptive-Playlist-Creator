# AI-DJ-Real-Time-Adaptive-Playlist-Creator
# An AI DJ that dynamically curates and mixes songs based on the mood of the room, user preferences, or even live feedback.
# Think of it as a personalized DJ that always plays the right vibe.

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import librosa
import numpy as np
import soundfile as sf

# Spotify API Authentication Setup
SPOTIFY_CLIENT_ID = "your_client_id"
SPOTIFY_CLIENT_SECRET = "your_client_secret"
SPOTIFY_REDIRECT_URI = "http://localhost:8080"

# Initialize Spotify Client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public user-library-read"
))

print("Connected to Spotify successfully!")

# Fetch songs based on mood
def fetch_songs(mood):
    # Define mood ranges
    mood_filters = {
        "chill": {"energy": (0.2, 0.5), "danceability": (0.2, 0.5), "valence": (0.2, 0.5)},
        "party": {"energy": (0.7, 1.0), "danceability": (0.7, 1.0), "valence": (0.6, 1.0)},
        "romantic": {"energy": (0.2, 0.5), "danceability": (0.2, 0.6), "valence": (0.5, 1.0)},
    }

    filters = mood_filters[mood]
    results = sp.search(q="genre:pop", type="track", limit=50)

    # Filter tracks
    filtered_tracks = []
    for track in results['tracks']['items']:
        audio_features = sp.audio_features(track['uri'])[0]
        if (filters['energy'][0] <= audio_features['energy'] <= filters['energy'][1] and
            filters['danceability'][0] <= audio_features['danceability'] <= filters['danceability'][1] and
            filters['valence'][0] <= audio_features['valence'] <= filters['valence'][1]):
            filtered_tracks.append(track['uri'])

    return filtered_tracks

# Create a new Spotify playlist
def create_playlist(name, track_uris):
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, name, public=True)
    sp.playlist_add_items(playlist['id'], track_uris)
    return playlist['id']

# Generate seamless transitions using Librosa
def create_transition(track1_path, track2_path, output_path):
    # Load tracks
    y1, sr1 = librosa.load(track1_path, sr=None)
    y2, sr2 = librosa.load(track2_path, sr=None)

    # Extract the last 5 seconds of track 1 and the first 5 seconds of track 2
    transition_length = 5 * sr1
    y1_fade = y1[-transition_length:]
    y2_fade = y2[:transition_length]

    # Crossfade
    fade = np.linspace(0, 1, transition_length)
    y1_fade_out = y1_fade * (1 - fade)
    y2_fade_in = y2_fade * fade
    transition = y1_fade_out + y2_fade_in

    # Combine tracks
    combined = np.concatenate((y1[:-transition_length], transition, y2[transition_length:]))

    # Save the final track
    sf.write(output_path, combined, sr1)

    try:
    results = sp.search(q="genre:pop", type="track", limit=50)
except spotipy.exceptions.SpotifyException as e:
    print(f"Spotify API error: {e}")
    return []


# Run the AI DJ
def run_ai_dj():
    print("Welcome to the AI DJ!")
    mood = input("Choose your mood (chill, party, romantic): ").strip().lower()

    if mood not in ["chill", "party", "romantic"]:
        print("Invalid mood. Please choose chill, party, or romantic.")
        return

    # Fetch songs and create playlist
    track_uris = fetch_songs(mood)
    if not track_uris:
        print("No songs found matching the mood. Try again.")
        return

    playlist_id = create_playlist(f"{mood.capitalize()} Vibes", track_uris)
    print(f"Your playlist is ready: https://open.spotify.com/playlist/{playlist_id}")

# Start the application
if __name__ == "__main__":
    run_ai_dj()
