import numpy as np
from time import time

import json
import requests
import urllib.parse as urlparse
from urllib.parse import urlencode
from requests_oauthlib import OAuth2Session
#becuase by default, OAUTH2 requires https but we are at http.
import os 
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

import pandas as pd

class spotifyuser():
    
    def __init__(self, scope = None, redirect_uri = None):
        if scope is None:
            self.scope = 'playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-follow-modify user-follow-read user-library-read user-top-read'
        else:
            self.scope = scope
        if redirect_uri is None:
            self.redirect_uri = 'http://127.0.0.1:8080/callback/q'
        else:
            self.redirect_uri  = redirect_uri

        #Details of you 
        self._client_id = "42b6ab36875d43128f6b750da5c0e987"
        self._client_secret = "8c1dcb159aee4d69962e0b357f048eec"
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.base_url = "https://api.spotify.com/v1/"
        self.oauth = OAuth2Session(self._client_id, redirect_uri=self.redirect_uri,
                          scope= self.scope, state = "34fFs29kd09")
        self.token = self._do_authorize()
        self.me = self._get_me()
        self.playlists = self._get_playlist() 
        self.playlists_names = self.playlists['name'] 
        print ("You have been authorized. \n \
        You should now be able to access your playlists to get their details. \n \
        You should be able to get features of songs in the playlists.")
            

    def _do_authorize(self):
        '''Do authorization when the user is instantiated. Return token
        '''

        authorization_url, state = self.oauth.authorization_url(self.auth_url)
        print ('Please go to %s and authorize access.' % authorization_url)

        authorization_response =  input('Enter (copy-paste) here the URL you were redirected to- URL: ')
        token = self.oauth.fetch_token(self.token_url, authorization_response=authorization_response,
                                        client_secret=self._client_secret)
        return token
        
    def _refresh_token(self):
        '''Refresh token when expired. Return token.
        '''
        if time() > self.token['expires_at'] - 100:
            response =requests.post(self.token_url, data={'client_id':self._client_id, \
                                            'client_secret':self._client_secret, \
                                            'grant_type':"refresh_token", 
                                            'refresh_token':self.token['refresh_token']})

            newtoken = json.loads(response.content.decode())
            for key in newtoken:
                self.token[key] = newtoken[key]
                self.oauth.token[key]= newtoken[key]
            print("Refreshed token")
            print(response, newtoken)

    def _get_me(self):
        '''get user info from endpoint /me upon instantiation.
        '''
        response = self.oauth.get(self.base_url + "me")
        meinfo = json.loads(response.content.decode())
        return meinfo

    def _get_playlist(self):
        '''Get all the playlists of the user upon instantiation.
        '''
        self._refresh_token()
        response = self.oauth.get(self.base_url + "users/%s/playlists?limit=50"%self.me["id"])
        
        playlists = json.loads(response.content.decode())
        user_playlists = pd.DataFrame(columns=playlists['items'][0].keys())
        while True:
            playlists = json.loads(response.content.decode())
            isnext = playlists['next']
            for play in playlists['items']:
                user_playlists = user_playlists.append(play, ignore_index=True)    
            if isnext:
                response = chirag.oauth.get(isnext)
            else:
                break

        
        return user_playlists

            
    def _findxfory_playlist(self, x, y, yval):
        '''For column 'y', return corresponding entry from column 'x'
        '''
        if x in self.playlists.keys() and y in self.playlists.keys():
            toret = self.playlists[x][self.playlists[y] == yval]
            return toret.values[0]
        else:
            print ("Key not found")
            return 0 

    def _get_artist(self, track):
        '''Get artist list from spotify track object
        '''
        toret  = []
        for foo in track['artists']:
            toret.append(foo['name'])
        return toret



    def _get_tracks(self, playlist_tracks): 
        '''Use track object of spotify to get all tracks.

        Returns: pandas array of tracks
        '''
        tracklist = playlist_tracks
        #The keys here need to correspond with trackitems in get playlist details.
        #TODO: Get rid of this hard-coding
        tracks = pd.DataFrame(columns = ['added_at', 'name', 'id', 'album', 'artist', 'popularity'])

        while True:
            isnext = tracklist['next']
            for song in tracklist['items']:
                track = song['track']
                temp = {'added_at':song['added_at'], \
                        'name':track['name'], 'id':track['id'], \
                        'album':track['album']['name'], \
                        'artist':self._get_artist(track), \
                        'popularity':track['popularity']}
                tracks = tracks.append(temp, ignore_index=True)

            if isnext:
                response = self.oauth.get(isnext)
                tracklist = json.loads(response.content.decode())
            else: break

        return tracks


    def get_playlist_details(self, name = None, ids = None):
        '''Take playlist name or playlist id and return playlist details. 

        Parameters
        ---------
        ids: The id of the playlist
        name: Name of the playlist can be given if user.playlist object exists.
        One of these 3 is required.

        
        Returns
        -------
        a dictionary giving details of playlist and tracks in it.
        '''
        self._refresh_token()
        #Get the name & id of the playlist
        if name is None and ids is None:
            print("Give either name or id")
            return None
        else:
            if name is not None:
                ids =  self._findxfory_playlist('id', "name", name)
                href = self._findxfory_playlist('href', "name", name)
            else:
                name = self._findxfory_playlist('name', "id", ids)
                href = self._findxfory_playlist('href', "name", name)
        
        #To create a URL to be queried.
        #TODO: To be able to take in field names as arguments
        trackitems = "items(added_at,track(name,id,album.name,artists.name,popularity))"
        tracksfield = 'tracks(total,previous,offset,limit,next,%s)'%trackitems
        fields = ["id", "name", tracksfield, "description"]

        #create_url = self.base_url + "users/%s/playlists/%s"%(self.me['id'], ids)
        create_url = href
        for foo in range(len(fields)):
            if not foo:
                create_url += "?fields="
            else:
                create_url += ","
            create_url += str(fields[foo])

        #Query API
        response = self.oauth.get(create_url)
        playlist = json.loads(response.content.decode())
        #Convert tracks to pandas array
        tracks = self._get_tracks(playlist['tracks'])
        playlist['tracks'] = tracks
        return playlist
    
    
    
    def get_features_playlist(self, playlist=None, ids= None, name = None):
        '''Take playlist name or id or playlist object and extract song features 

        Parameters
        ---------
        playlist: A spotify playlist object of the type user.playlist
        ids: The id of the playlist
        name: Name of the playlist can be given if user.playlist object exists.
        One of these 3 is required.

        
        Returns
        -------
        a pandas dataframe with the names of tracks and their features.
        '''

        self._refresh_token()
        #Get the playlist
        if name is None and ids is None and playlist is None:
            print("Give either playlist name or playlist id or playlist object")
            return None
        elif playlist is None:
            if name is not None:
                ids = self._findxfory_playlist('id', "name", name)
                playlist = self.get_playlist_details(ids =ids)
            elif id is not None:
                name = self._findxfory_playlist('name', "id", ids)
                playlist = self.get_playlist_details(ids =ids)

        song_ids = list(playlist['tracks']['id'])
        features = self.get_features_song(song_ids)
        features["name"] = playlist['tracks']['name']
        features["album"] = playlist['tracks']['album']
        features["artist"] = playlist['tracks']['artist']
        features["popularity"] = playlist['tracks']['popularity']
        features["added_at"] = playlist['tracks']['added_at']
        return features
       #Query API. You can only query 100 songs at a time.

    def get_features_song(self, song_ids):
        '''Take a song id or list of song ids and return song features 

        Parameters
        ---------
        song_ids: string or list of strings which are the ids of songs.
        
        Returns
        -------
        a pandas dataframe with the names of tracks and their features.
        '''

        self._refresh_token()
        if type(song_ids) is list:
            nsongs = len(song_ids)
            features = []
            startat = 0
            while True:
                if nsongs > 100:
                    response = self.oauth.get(self.base_url+ "audio-features/?ids=%s"%(",".join(song_ids[:100])))
                    features = features + json.loads(response.content.decode())['audio_features']
                    song_ids = song_ids[100:]
                    nsongs = len(song_ids)
                else:
                    response = self.oauth.get(self.base_url+ "audio-features/?ids=%s"%(",".join(song_ids[:]))) 
                    features = features + json.loads(response.content.decode())['audio_features']
                    break

            features = pd.DataFrame(features)
            return features

        elif type(song_ids) is str:
            response = self.oauth.get(self.base_url+ "audio-features/%s"%song_ids)
            features = json.loads(response.content.decode())['audio_features']
            features = pd.DataFrame(features)

            response = self.oauth.get(self.base_url+ "tracks/%s"%song_ids)
            track = json.loads(response.content.decode())
            features["name"] = track['name']
            features["album"] = track['album']
            features["artist"] = self.get_artist(track)
            features["popularity"] = track['popularity']
            return features

        else:
            print("Need either a string or list of strings of song ids")

        
