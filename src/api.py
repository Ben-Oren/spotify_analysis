### Imports

import pandas as pd
import numpy as np
import requests


### Objects

BASE_URL = 'https://api.spotify.com/v1/'

default_track_dictionary = {
    'meta': ['status_code'],
    'track': [
        'duration', 'end_of_fade_in',
        'start_of_fade_out', 'window_seconds'
    ],
    'bars': 'all',
    'beats': 'all',
    'sections': 'all',
    'segments': 'all', 
    'tatums': 'all'
}


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

## GET data

def get_playlist_urls(user_id):
    
    '''
    GETS playlist API urls from specific user
    
    input:
        user_id: unique user identifier from spotify API
        str
        
    output:
        list of zipped tuples (playlist name, playlist API url)
        list of tuples object
    '''
    
    user_profile = requests.get(BASE_URL + 'users/' + user_id + '/playlists', headers=headers)

    user_profile = user_profile.json()
    
    playlist_number = len(user_profile['items'])
    
    playlist_urls = [
        user_profile['items'][number]['href']
        for number 
        in range(0, playlist_number)
    ]
    
    playlist_names = [
        user_profile['items'][number]['name']
        for number 
        in range (0, playlist_number)
    ]
    
    return list(
        zip(
            playlist_names,
            playlist_urls
        )
    
    )
    
    
    


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
            len(playlist_url_response['tracks']['items'])
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
    BASE_URL + 'audio-analysis/' + song_id,
    headers=headers
    ) \
    .json()
    
    return data

## unpack data from RESPONSE

def unpack_selected_json(track_raw_json, track_raw_json_key, cols):
    '''
    unpack the nested dictionaries within specific key of track's low-level audio analysis data into df

    input:
        track_raw_json - JSON results from track audio analysis POST request
        json
        
        track_raw_json_key - specific key to unpack
        str
        
        cols - list of strings of columns to unpack eg ['key', 'tempo']
        
    output:
        df with one row (the track) and unpacked columns
    '''
    
    #individual data_groups are eg `section`, `beats` etc
    data_group = track_raw_json[track_raw_json_key]
    
    
    #syntax is eg
    # for every section in datagroup
    #    for every provided column
    #        create new dict entry section(int)_column:datagroup[section][column]
    unpacked_dict = {
        
        #create dict entry of eg `section10_tempo: '6.7'`
        '{}{}_{}'.format(track_raw_json_key, count, col):data_group[count][col] 
        
        #for every unit in the subgroup of data
        for count, _ in enumerate(data_group)
        
        #for every selected column in that unit
        for col in cols
    }
    
    #`pitch` and `timbre` in each `segment` are 12-dim vectors, need to unpack them
    #or else they won't fit onto one row of subsequent df
    
    key_list = list(unpacked_dict.keys())
    
    for key in key_list:
        update_dict = {}
        if 'pitch' in key:
            for count, item in enumerate(unpacked_dict[key]):
                update_dict.update({key+str(count):item})
            unpacked_dict.update(update_dict)
            del unpacked_dict[key]    
        if 'timbre' in key:
            for count, item in enumerate(unpacked_dict[key]):
                update_dict.update({key+str(count):item})
            unpacked_dict.update(update_dict)
            del unpacked_dict[key]  
    
    
    #index[0] to keep all the data on one row
    frame = pd.DataFrame(
        unpacked_dict, 
        index=[0]
    )
    
    return frame


def unpack_json(track_raw_json, id, columns_dictionary=default_track_dictionary):
    '''
    unpack the nested dictionaries from a result of a POST request for a specific track's low-level audio analysis data

    input:
        track_raw_json - JSON results from track audio analysis POST request
        json
        
        columns_dictionary - keys are subgroups of data eg 'beats', items are either:
            'all' (str): flag to unpack all columns in subunit 
            list (list): list of strings of columns in subunit to unpack
        
    output:
        df with one row (the track) and unpacked columns
    '''
    
    frame_list = []
    
    for subgroup in columns_dictionary.keys():
        cols = columns_dictionary[subgroup]
        
        #subgroups with deeper lists unpack with unpack_selected_json function above
        if cols == 'all':
            
            cols = list(
                track_raw_json[subgroup][0].keys()
            )
        
            frame = unpack_selected_json(track_raw_json, subgroup, cols)
        
            frame_list.append(frame)            
        
        
        
        #subgroups with just key value pairs are unpacked here with similar structure
        #but w/o that additional nested list
        else:
            for col in cols:
                frame = pd.DataFrame({
                    '{}_{}'.format(subgroup, col):track_raw_json[subgroup][col]
                    },
                    index=[0]
                )

                frame_list.append(frame)

    #concat all the frames together in one row
    
    track_frame = pd.concat(frame_list, axis=1)
    
    track_frame['id'] = id
    
    return track_frame

def unpack_playlist_metadata(playlist_response, track_number=0):
    '''
    put each track's metadata from playlist RESPONSE into dict and zip w/ track id from playlist
    
    input:
        playlist_response: RESPONSE from playlist GET
        json
        
        track_number: element in list corresponding to playlist track being unpacked
        
    output:
        df of track metadata, all one row
    '''
    
    base = playlist_response['tracks']['items'][track_number]['track']
    
    song_metadata_dict = {
    'id': base['id'],
    'popularity': base['popularity'],
    'artist': base['artists'][0]['name'],
    'artist_type': base['artists'][0]['type'],
    'album_type': base['album']['album_type'],
    'album_release_date': base['album']['release_date'],
    'release_precision': base['album']['release_date_precision'],
    'track_name': base['name'],
    'track_flag': base['track'],
    'track_type': base['type'],
    'episode': base['episode']
}
    
    frame = pd.DataFrame(
        song_metadata_dict, 
        index=[0]
    )
    
    return frame

def raw_data_from_playlist(playlist_url):
    '''
    GETS playlist info from playlist api url
    
    unpacks track IDs into list and metadata json into frames
    
    GETS low-level audio data
    
    unpacks data into json
    
    merges metadata and audio data on track id
    
    input:
        playlist_url: url of specific playlist through api 
        str
        
    output:
        df containing low-level audio data and metadata
        df object
        
        one track per row
        low-level audio data is flat and sparse
        
    '''
    
    # GET overall data from specific playlist data
    playlist_response = get_playlist_response(playlist_url)

    # parse song IDs in RESPONSE from sp. playlist 
    song_ids = parse_playlist_song_ids(playlist_response)

    # GET track info and unpack json into list
    track_frames = [
    unpack_json(
        get_raw_data_track(song_id),
        song_id
    )
    for song_id
    in song_ids
    ]

    # concat track info into one frame
    tracks_frame = pd.concat(track_frames)

    # create frames of track metadata in list
    metadata_list = [
        unpack_playlist_metadata(playlist_response, track_number)
        for track_number
        in range(0, len(playlist_response['tracks']['items'])
                )
    ] 

    # concat metadata frames into one
    metadata_frame = pd.concat(metadata_list)

    # merge track info and metatdata frames on track id
    frame = pd.merge(tracks_frame, metadata_frame, on='id')
    
    return frame