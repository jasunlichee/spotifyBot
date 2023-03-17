import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, url_for, session, request, redirect, render_template
from dotenv import load_dotenv
from requests import post
import os
import time
import random
import config
from html.parser import HTMLParser

#chrome://net-internals/#sockets

app = Flask(__name__)
app.secret_key = '12l3kjfli2348'
app.config['ENV'] = 'production'
app.config['DEBUG'] = 'false'
app.config['TESTING'] = 'false'
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
    return redirect(url_for('home', _external=True))

def getTrack():
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    if(sp.current_user_playing_track()):
        return sp.current_user_playing_track()  
    else:
        return("No Song Playing")

def getPlaylist():
    track = getTrack()
    if(track == "No Song Playing"):
        return track
    
    if(track["context"]["type"] != "playlist"):
        return "Not a playlist"
    
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
    if(playlist_dict == "No Song Playing" or playlist_dict == "Not a playlist"):
        return playlist_dict 
    size = len(playlist_dict)
    iter = list(range(0, size))
    random.shuffle(iter)
    token_info = get_token()
    new_dict = {}
    sp = spotipy.Spotify(auth = token_info['access_token'])
    new_dict[1] = "Current Song"

    for i in range(size):
        val = iter[i]
        sp.add_to_queue(playlist_dict[val])
        song = sp.track(playlist_dict[val])
        new_dict[i + 2] = song["name"]

    return new_dict

@app.route('/tempShuffle')
def tempShuffle():
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    playlist_dict = getPlaylist()
    if(playlist_dict == "No Song Playing" or playlist_dict == "Not a playlist"):
        return playlist_dict 
    size = len(playlist_dict)

    sp.pause_playback()
    
    list = []
    
    for key in playlist_dict:
        list.append(playlist_dict[key])

    random.shuffle(list)

    sp.user_playlist_create(sp.current_user()["id"], "tempShuffle", True, False, "Current playlist shuffled")
    id = sp.current_user_playlists(1, 0)["items"][0]["id"]
    link = sp.current_user_playlists(1, 0)["items"][0]["external_urls"]["spotify"]
    sp.playlist_add_items(id, list)

    device = sp.devices()["devices"][0]["id"]
    sp.shuffle(False)
    sp.start_playback(None, link, None, None, None)

    return redirect(url_for('background', _external=True))

@app.route('/background')
def background():
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])

    while(sp.current_user_playing_track()):
        time.sleep(5)
    
    return("No Song Playing")

@app.route('/home')
def home():
    return render_template("test.html", name="home")

@app.route('/test')
def test():
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    #id = sp.current_user_playlists(1, 0)["items"][0]["id"]
    link = sp.current_user_playlists(1, 0)["items"][0]["external_urls"]["spotify"]
    #device = sp.devices()["devices"][0]["id"]
    #sp.start_playback(None,link, None, None, None)


    return sp.current_user_playing_track()

def skip(amount):
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    for i in range(amount):
        sp.next_track()
    return
        

@app.route('/topShortTerm')
def topShortTerm():
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    return sp.current_user_top_tracks(100, 0, 'short_term')

@app.route('/topMediumTerm')
def topMediumTerm():
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    return sp.current_user_top_tracks(100, 0, 'medium_term')

@app.route('/topLongTerm')
def topLongTerm():
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    return sp.current_user_top_tracks(100, 0, 'long_term')

@app.route('/makeShort')
def makeShort():
    list = topShortTerm()["items"]
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
    sp.user_playlist_create(sp.current_user()["id"], "Top 50 Songs ST", True, False, "Your favorite songs in the last month")
    id = sp.current_user_playlists(1, 0)["items"][0]["id"]
    link = sp.current_user_playlists(1, 0)["items"][0]["external_urls"]["spotify"]

    new_list = []
    for i in range(len(list)):
        new_list.append(list[i]["id"])

    sp.playlist_add_items(id, new_list)

    return link

@app.route('/makeMedium')
def makeMedium():
    list = topMediumTerm()["items"]
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
 
    sp.user_playlist_create(sp.current_user()["id"], "Top 50 Songs MT", True, False, "Your favorite songs in the last year")
    id = sp.current_user_playlists(1, 0)["items"][0]["id"]
    link = sp.current_user_playlists(1, 0)["items"][0]["external_urls"]["spotify"]

    new_list = []
    for i in range(len(list)):
        new_list.append(list[i]["id"])

    sp.playlist_add_items(id, new_list)

    return link

@app.route('/makeLong')
def makeLong():
    list = topLongTerm()["items"]
    token_info = get_token()
    sp = spotipy.Spotify(auth = token_info['access_token'])
 
    sp.user_playlist_create(sp.current_user()["id"], "Top 50 Songs LT", True, False, "Your favorite songs of all time")
    id = sp.current_user_playlists(1, 0)["items"][0]["id"]
    link = sp.current_user_playlists(1, 0)["items"][0]["external_urls"]["spotify"]

    new_list = []
    for i in range(len(list)):
        new_list.append(list[i]["id"])

    sp.playlist_add_items(id, new_list)

    return link


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
        scope="user-read-currently-playing user-read-playback-state user-modify-playback-state user-top-read playlist-modify-public playlist-modify-private")


