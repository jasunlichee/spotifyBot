import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, url_for, session, request, redirect
from dotenv import load_dotenv
from requests import post
import os
import random

app = Flask(__name__)
app.secret_key = '12l3kjfli2348'
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

TOKEN_INFO = "token_info"

@app.route('/')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('getTrack', _external=True))

@app.route('/getTrack')
def getTrack():
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    if(sp.current_user_playing_track()):
        return sp.current_user_playing_track()  
    else:
        return("No Song Playing")

@app.route('/getPlaylist')
def getPlaylist():
    track = getTrack()
    if(track == "No Song Playing"):
        return track
    playlist_uri = track["context"]["uri"]
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    id = sp.current_user()["id"]
    playlist = sp.playlist_tracks(playlist_id= playlist_uri)
    tracks = playlist['items']
    while playlist['next']:
        playlist = sp.next(playlist)
        tracks.extend(playlist['items'])

    playlist_dict = {}
    for i in range(len(tracks)):
        playlist_dict[i] = tracks[i]["track"]["id"]
    return playlist_dict

@app.route('/populate')
def populate():
    playlist_dict = getPlaylist()
    if(playlist_dict == "No Song Playing"):
        return playlist_dict 
    size = len(playlist_dict)
    iter = list(range(0, size-1))
    random.shuffle(iter)
    token_info = get_token()
    new_dict = {}
    sp = spotipy.Spotify(auth = token_info['access_token'])
    for i in range(82):
        sp.add_to_queue(playlist_dict[iter[i]])
        song_name = sp.track(playlist_dict[iter[i]])
        new_dict[iter[i]] = song_name["name"]

    return new_dict

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    sp_oauth = create_spotify_oauth()
    token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id= client_id,
        client_secret= client_secret,
        redirect_uri=url_for('redirectPage', _external=True),
        scope="user-read-currently-playing user-read-playback-state user-modify-playback-state")


