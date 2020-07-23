from flask import Flask, Response, jsonify, render_template
from base64 import b64encode

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import requests
import json
import os
import random

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET_ID = os.getenv("SPOTIFY_SECRET_ID")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

# scope user-read-currently-playing/user-read-recently-played
SPOTIFY_URL_REFRESH_TOKEN = "https://accounts.spotify.com/api/token"
SPOTIFY_URL_NOW_PLAYING = "https://api.spotify.com/v1/me/player/currently-playing"
SPOTIFY_URL_RECENTLY_PLAY = "https://api.spotify.com/v1/me/player/recently-played?limit=1"


app = Flask(__name__)


def getAuth():
    return b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_SECRET_ID}".encode()).decode("ascii")


def refreshToken():
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
    }

    headers = {"Authorization": "Basic {}".format(getAuth())}

    response = requests.post(SPOTIFY_URL_REFRESH_TOKEN, data=data, headers=headers)
    return response.json()["access_token"]

def recentlyPlayed():
    token = refreshToken()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(SPOTIFY_URL_RECENTLY_PLAY, headers=headers)

    if response.status_code == 204:
        return {}

    return response.json()

def nowPlaying():

    token = refreshToken()

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(SPOTIFY_URL_NOW_PLAYING, headers=headers)

    if response.status_code == 204:
        return {}

    return response.json()

def loadImageB64(url):
    response = requests.get(url)
    return b64encode(response.content).decode("ascii")

def makeSVG(data):

    playing = True

    if data == {}:
        recent_plays = recentlyPlayed()
        item = recent_plays["items"][0]["track"]
        playing = False
    else:
        item = data["item"]

    img = loadImageB64(item["album"]["images"][1]["url"])
    artistName = item["artists"][0]["name"].replace("&", "&amp;")
    songName = item["name"].replace("&", "&amp;")
    albumName = item["album"]["name"].replace("&", "&amp;")

    dataDict = {
        "artist_name": artistName,
        "song_name": songName,
        "album_name": albumName,
        "img": img,
        "playing": playing
    }

    return render_template("spotify.html.j2", **dataDict)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):

    data = nowPlaying()
    svg = makeSVG(data)

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp

if __name__ == "__main__":
    app.run(debug=True)
