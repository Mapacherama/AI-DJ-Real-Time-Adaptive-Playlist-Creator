# AI-DJ-Real-Time-Adaptive-Playlist-Creator
# An AI DJ that dynamically curates and mixes songs based on the mood of the room, user preferences, or even live feedback.
# Think of it as a personalized DJ that always plays the right vibe.

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import librosa
import numpy as np
import soundfile as sf
import json

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
def fetch_songs(mood, genre="pop"):
    # Define mood ranges
    mood_filters = {
        "chill": {"energy": (0.2, 0.5), "danceability": (0.2, 0.5), "valence": (0.2, 0.5)},
        "party": {"energy": (0.7, 1.0), "danceability": (0.7, 1.0), "valence": (0.6, 1.0)},
        "romantic": {"energy": (0.2, 0.5), "danceability": (0.2, 0.6), "valence": (0.5, 1.0)},
    }

    filters = mood_filters.get(mood, mood_filters["chill"])
    
    try:
        results = sp.search(q=f"genre:{genre}", type="track", limit=50)
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")
        return []

    if not results['tracks']['items']:
        print("No tracks found.")
        return []

    # Filter tracks dynamically
    filtered_tracks = []
    for track in results['tracks']['items']:
        audio_features = sp.audio_features(track['uri'])[0]
        if all(filters[key][0] <= audio_features[key] <= filters[key][1] for key in filters):
            filtered_tracks.append(track['uri'])

    return filtered_tracks

# Create a new Spotify playlist
def create_playlist(name, track_uris):
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, name, public=True)
    sp.playlist_add_items(playlist['id'], track_uris)
    return playlist['id']

# Save playlist locally
def save_playlist_locally(name, track_uris):
    with open(f"{name}_playlist.json", "w") as file:
        json.dump({"playlist_name": name, "tracks": track_uris}, file)
    print(f"Playlist saved locally as {name}_playlist.json")

# Generate seamless transitions using Librosa
def create_transition(track1_path, track2_path, output_path):
    # Load audio
    y1, sr1 = librosa.load(track1_path, sr=None)
    y2, sr2 = librosa.load(track2_path, sr=None)

    # Match tempo
    tempo1, _ = librosa.beat.beat_track(y=y1, sr=sr1)
    tempo2, _ = librosa.beat.beat_track(y=y2, sr=sr2)
    y2_resampled = librosa.effects.time_stretch(y2, tempo1 / tempo2)

    # Extract the last 5 seconds of track 1 and the first 5 seconds of track 2
    transition_length = int(5 * sr1)
    y1_fade = y1[-transition_length:]
    y2_fade = y2_resampled[:transition_length]

    # Crossfade logic
    fade = np.linspace(0, 1, transition_length)
    y1_fade_out = y1_fade * (1 - fade)
    y2_fade_in = y2_fade * fade
    transition = y1_fade_out + y2_fade_in

    # Combine tracks
    combined = np.concatenate((y1[:-transition_length], transition, y2_resampled[transition_length:]))

    sf.write(output_path, combined, sr1)

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
    save_playlist_locally(f"{mood.capitalize()} Vibes", track_uris)
    print(f"Your playlist is ready: https://open.spotify.com/playlist/{playlist_id}")

# Start the application
if __name__ == "__main__":
    run_ai_dj()
