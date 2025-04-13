from flask import Flask, request, jsonify, redirect
from flask_cors import CORS 
from dotenv import load_dotenv
import webbrowser
import requests
import os
import base64
import numpy as np
import cv2
from cnn_utils import EmotionDetector
from flask_cors import cross_origin

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:8000/"], supports_credentials=True)
load_dotenv()

emotion_detector = EmotionDetector()

client_id = 'SPOTIFY_CLIENT_ID'
client_secret = 'SPOTIFY_CLIENT_SECRET'
redirect_uri = 'SPOTIFY_REDIRECT_URI'


@app.route("/login")
def login():
    scope = "user-library-read playlist-read-private"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?response_type=code&client_id={client_id}"
        f"&redirect_uri={redirect_uri}&scope={scope}"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Missing code"}), 400

    token = get_access_token(code)
    profile = get_user_profile(token)
    playlists = get_user_playlists(token)

    frontend_url = f"http://localhost:3000/profile?profile={profile}&playlists={playlists}"
    return redirect(frontend_url)


def get_access_token(code):
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Failed to get access token")


def get_user_profile(token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to get user profile")


def get_user_playlists(token):
    url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch playlists", "details": response.json()}
    
def print_all_playlist_tracks(token):
    playlists_url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {token}"}
    playlists_response = requests.get(playlists_url, headers=headers)

    if playlists_response.status_code != 200:
        print("Failed to fetch playlists")
        return

    playlists = playlists_response.json().get("items", [])

    for playlist in playlists:
        playlist_name = playlist["name"]
        playlist_id = playlist["id"]
        print(f"\nPlaylist: {playlist_name}")

        tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        while tracks_url:
            tracks_response = requests.get(tracks_url, headers=headers)
            if tracks_response.status_code != 200:
                print(f"Failed to fetch tracks for {playlist_name}")
                break

            track_items = tracks_response.json().get("items", [])
            for item in track_items:
                track = item.get("track")
                if track:
                    track_name = track.get("name")
                    artist_name = track["artists"][0]["name"] if track["artists"] else "Unknown Artist"
                    print(f" - {track_name} by {artist_name}")

            # For playlists with more than 100 tracks (Spotify paginates), follow `next` URL:
            tracks_url = tracks_response.json().get("next")
    
def classify_emotion_from_genres(genres):
    genre_to_emotion = {
        "happy": ["pop", "dance", "edm"],
        "sad": ["acoustic", "piano", "singer-songwriter"],
        "angry": ["rock", "metal", "hardcore"],
        "relaxed": ["ambient", "chill", "lo-fi"]
    }

    for emotion, genre_list in genre_to_emotion.items():
        if set(genre_list) & set(genres):
            return emotion
    return None

@app.route("/detect-emotion", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://127.0.0.1:8000"], supports_credentials=True)
def detect_emotion():
    if request.method == "OPTIONS":
        return '', 200  

    try:
        data = request.get_json()
        image_data = data.get("image")

        if not image_data:
            return jsonify({"error": "No image provided"}), 400

        if image_data.startswith("data:image/jpeg;base64,"):
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = emotion_detector.detect_emotion(frame)
        print("Detected emotions:", results)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/find-matching-song", methods=["POST"])
def find_matching_song():
    try:
        data = request.get_json()
        emotion = data.get("emotion")
        playlists = data.get("playlists")
        target_genres = data.get("genres", [])

        if not emotion or not playlists or not target_genres:
            return jsonify({"error": "Missing required data"}), 400

        token_url = "https://accounts.spotify.com/api/token"
        auth_string = f"{client_id}:{client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        token_data = {"grant_type": "client_credentials"}
        token_response = requests.post(token_url, headers=headers, data=token_data)

        if token_response.status_code != 200:
            return jsonify({"error": "Failed to get access token"}), 500

        access_token = token_response.json()["access_token"]

        for playlist in playlists.get("items", []):
            playlist_id = playlist["id"]
            tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            track_headers = {"Authorization": f"Bearer {access_token}"}
            tracks_response = requests.get(tracks_url, headers=track_headers)

            if tracks_response.status_code == 200:
                for track in tracks_response.json().get("items", []):
                    track_data = track.get("track")
                    if not track_data or not track_data.get("artists"):
                        continue

                    artist_id = track_data["artists"][0]["id"]
                    artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
                    artist_response = requests.get(artist_url, headers=track_headers)

                    if artist_response.status_code == 200:
                        artist_data = artist_response.json()
                        artist_genres = artist_data.get("genres", [])
                        matching_genres = set(artist_genres) & set(target_genres)

                        if matching_genres:
                            return jsonify({
                                "name": track_data["name"],
                                "artist": track_data["artists"][0]["name"],
                                "genres": list(matching_genres),
                                "preview_url": track_data.get("preview_url"),
                                "external_url": track_data["external_urls"]["spotify"]
                            })

        return jsonify({"message": "No matching song found"})

    except Exception as e:
        print("Error in find_matching_song:", e)
        return jsonify({"error": str(e)}), 500
    
@app.route("/categorize-playlists-by-emotion", methods=["POST"])
def categorize_playlists():
    try:
        data = request.get_json()
        playlists = data.get("playlists")
        user_token = data.get("access_token")

        if not playlists or not user_token:
            return jsonify({"error": "Missing playlists or token"}), 400

        headers = {"Authorization": f"Bearer {user_token}"}
        emotion_buckets = {
            "happy": [], "sad": [], "angry": [], "relaxed": [], "unknown": []
        }

        for playlist in playlists.get("items", []):
            playlist_id = playlist["id"]
            tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

            while tracks_url:
                response = requests.get(tracks_url, headers=headers)
                tracks_data = response.json()
                tracks = tracks_data.get("items", [])

                for item in tracks:
                    track = item.get("track")
                    if not track:
                        continue

                    track_id = track["id"]
                    features_url = f"https://api.spotify.com/v1/audio-features/{track_id}"
                    features_response = requests.get(features_url, headers=headers)

                    if features_response.status_code != 200:
                        continue

                    features = features_response.json()
                    emotion = map_emotion(features)

                    emotion_buckets[emotion].append({
                        "name": track["name"],
                        "artist": track["artists"][0]["name"],
                        "id": track_id,
                        "preview_url": track.get("preview_url"),
                        "external_url": track["external_urls"]["spotify"]
                    })

                tracks_url = tracks_data.get("next")

        return jsonify(emotion_buckets)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def map_emotion(features):
    valence = features["valence"]
    energy = features["energy"]
    danceability = features["danceability"]
    acousticness = features["acousticness"]

    if valence > 0.6 and energy > 0.5:
        return "happy"
    elif valence < 0.4 and acousticness > 0.5:
        return "sad"
    elif energy > 0.7 and valence < 0.4:
        return "angry"
    elif energy < 0.5 and acousticness > 0.6:
        return "neutral"
    else:
        return "surprised"
    
@app.route("/debug-categorize", methods=["POST"])
def debug_categorize():
    try:
        data = request.get_json()
        playlists = data.get("playlists")
        user_token = data.get("access_token")

        if not playlists or not user_token:
            return jsonify({"error": "Missing playlists or access token"}), 400

        headers = {"Authorization": f"Bearer {user_token}"}
        emotion_buckets = {
            "happy": [], "sad": [], "angry": [], "relaxed": [], "unknown": []
        }

        for playlist in playlists.get("items", []):
            playlist_name = playlist["name"]
            playlist_id = playlist["id"]
            tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

            while tracks_url:
                response = requests.get(tracks_url, headers=headers)
                if response.status_code != 200:
                    break

                tracks_data = response.json()
                tracks = tracks_data.get("items", [])

                for item in tracks:
                    track = item.get("track")
                    if not track or not track.get("id"):
                        continue

                    track_id = track["id"]
                    features_url = f"https://api.spotify.com/v1/audio-features/{track_id}"
                    features_response = requests.get(features_url, headers=headers)

                    if features_response.status_code != 200:
                        continue

                    features = features_response.json()
                    emotion = map_emotion(features)

                    song_info = f"{track['name']} by {track['artists'][0]['name']} (from '{playlist_name}')"
                    emotion_buckets[emotion].append(song_info)

                tracks_url = tracks_data.get("next")

        # Print songs categorized by emotion
        for emotion, songs in emotion_buckets.items():
            print(f"\n--- {emotion.upper()} ---")
            for song in songs:
                print(song)

        return jsonify({"message": "Printed categorized songs to console!"})

    except Exception as e:
        print("Error in debug_categorize:", e)
        return jsonify({"error": str(e)}), 500

print("Registered Routes:")
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == "__main__":
    app.run(debug=True, port=5000)