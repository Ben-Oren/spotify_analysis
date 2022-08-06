### Imports

import pandas as pd
import numpy as np
import requests


### Variables

BASE_URL = 'https://api.spotify.com/v1/'


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
    single_playlist_request
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