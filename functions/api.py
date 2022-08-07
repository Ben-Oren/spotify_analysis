### Imports

import pandas as pd
import numpy as np
import requests


### Variables

BASE_URL = 'https://api.spotify.com/v1/'


## Account-Specific

CLIENT_ID = '1c2e33a8bebd41fbbb8a1ecf0e8c4273'
CLIENT_SECRET = '4964098dcc7b41f99c4178e6403645c1'

AUTH_URL = 'https://accounts.spotify.com/api/token'

user_id = 'bothsidesdoit'

## Acquire access token and set authorization header

# POST
auth_response = requests.post(AUTH_URL, {
    'grant_type' : 'client_credentials', 
    'client_id' : CLIENT_ID,
    'client_secret' : CLIENT_SECRET,   
})

# convert response to json
auth_response_data = auth_response.json()

# save the access token
access_token = auth_response_data['access_token']

# save in header

headers = {
    'Authorization' : 
        'Bearer {token}'
        .format(
            token=access_token
        )
}




### Functions


def get_playlist_response(playlist_url):
    '''
    GET response for given playlist url from spotify api 
    
    input:
        playlist_url 
            - spotify API url for given playlist
            - string
        
    output:
        json of playlist_url RESPONSE from spotify api
    '''
    return requests.get(
        playlist_url,
        headers=headers
    ).json()
    

def parse_playlist_song_ids(playlist_url_response):
    '''
    parse playlist url RESPONSE for unique track IDs of songs in playlist 
    
    input:
        playlist_url_response
            - RESPONSE from spotify API for url for given playlist
            - json
        
    output:
        list of strings of unique track IDs 
    '''
    
    return [
    playlist_url_response
        ['tracks']
        ['items']
        [track]
        ['track']
        ['id']
    for
        track
    in
        range(
            0, 
            len(playlist_url_response['tracks'])
        )
    ]

def get_spotify_features_from_trackid(track_ids):
    '''
    GET response of spotify features for given list of track ids
    
    input:
        list of track ids
            - track id elements of list are strings
        
    output:
        df of spotify features for given track list 
    '''    
    spotify_features_url = BASE_URL + 'audio-features/'
    
    data = [
        requests.get(
            spotify_features_url + track_id,
            headers=headers
        )
        .json()
        for
            track_id
        in
            track_ids
    ]
    
    return pd.DataFrame(data)

def get_spotify_features(playlist_url):
    '''
    gather spotify features for each track in given playlist url
    
    input:
        playlist_url 
            - spotify API url for given playlist
            - string
        
    output:
        df of spotify features for that playlist
    '''
        
    playlist_response = get_playlist_response(
        playlist_url
    )
    
    playlist_track_ids = parse_playlist_song_ids(
        playlist_response
    )
    
    spotify_features = get_spotify_features_from_trackid(
        playlist_track_ids
    )
    
    return spotify_features


def get_raw_data_track(song_id):
    '''
    GET the low-level features of a single track through API call
    
    input:
        track_id - unique track ID in spotify api db
        str
        
    output:
        df of result of API call: low-level variables of single track
    '''
    
    data = requests.get(
    BASE_URL + 'audio-analysis/' + '6y0igZArWVi6Iz0rj35c1Y',
    headers=headers
    ) \
    .json()
    
    return data