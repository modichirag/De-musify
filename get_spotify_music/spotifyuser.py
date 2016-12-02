import numpy as np
from time import time

import re, json
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



    def _parse_uri(self, uri):
        '''Parse uri to return a dictionary of its contents.
        Can only parse uri of tracks, artists, albums, user, playlists
        '''

        values = re.split(":", uri)
        if values[0] != 'spotify':
            print ("Can only parse uri starting with spotify. Check uri")
            return None
        else:
            values = values[1:]
            toret = {}
            if len(values) == 2:
                toret["type"] = values[0]
                toret["id"] = values[1]
                return toret
            elif len(values) == 4:
                toret["user"] = values[1]
                toret["type"] = values[2]
                toret["id"] = values[3]
                return toret
            else:
                return "Uri type not understood"

    def _read_tracks(self, playlist_tracks): 
        '''Use track object of spotify to get all tracks.

        Returns: pandas array of tracks
        '''
        tracklist = playlist_tracks
        #The keys here need to correspond with trackitems in get playlist details.
        #TODO: Get rid of this hard-coding
        tracks = pd.DataFrame(columns = ['name', 'album', 'artist', 'popularity', 'id', 'added_at', 'uri'])

        while True:
            isnext = tracklist['next']
            for song in tracklist['items']:
                track = song['track']
                temp = {
                    'name':track['name'], \
                    'album':track['album']['name'], \
                    'artist':self._get_artist(track), \
                    'popularity':track['popularity'],\
                    'id':track['id'], \
                    'added_at':song['added_at'],\
                    'uri':track['uri']
                }
                tracks = tracks.append(temp, ignore_index=True)

            if isnext:
                response = self.oauth.get(isnext)
                tracklist = json.loads(response.content.decode())
            else: break

        return tracks


    def get_playlist_details(self, name = None, uri = None):
        '''Take playlist name or playlist uri and return playlist details. 

        Parameters
        ---------
        uri: String, uri of the playlists
        name: Name of the playlist can be given if it is your playlist.

        
        Returns
        -------
        a dictionary giving details of playlist and tracks in it.
        '''
        self._refresh_token()
        #Get the name & id of the playlist
        if uri is None:
            if (self.playlists['name'] == name).sum():
                uri = self._findxfory_playlist('uri', "name", name)
            else:
                print ("The playlist name is not in your playlists. Give playlist uri instead")
                return None
        uridict = self._parse_uri(uri)
        if uridict['type'] != 'playlist':
            print ("This uri does not seem to be of a playlist. Give a playlist uri.")
            return None

        #To create a URL to be queried.
        #TODO: To be able to take in field names as arguments
        trackitems = "items(added_at, track(name,id,uri,album.name,artists.name,popularity))"
        tracksfield = 'tracks(total,previous,offset,limit,next,%s)'%trackitems
        fields = ["id", "name", tracksfield, "description"]

        create_url = self.base_url + "users/%s/playlists/%s"%(uridict['user'], uridict['id'])
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
        tracks = self._read_tracks(playlist['tracks'])
        playlist['tracks'] = tracks
        return playlist
        
    
    def get_features_playlist(self, uri = None, name = None):
        '''Take playlist uri (or name if its in your playlists) and extract song features 

        Parameters
        ---------
        uri: String, uri of the playlists
        name: Name of the playlist can be given if it is your playlist.
        
        Returns
        -------
        a pandas dataframe with the names of tracks and their features.
        '''

        self._refresh_token()
        #Get the playlist
        playlist = self.get_playlist_details(uri = uri, name = name)
        if playlist is None:
            print ('Features could not be found')
            return None

        song_uri = list(playlist['tracks']['uri'])
        features = self.get_features_song(song_uri)
        for key in features.keys():
            playlist['tracks'][key] = features[key]
        return playlist['tracks']



    def get_features_song(self, uri_list, get_song_names = False):
        '''Take a list of uri (strings) and return song features 

        Parameters
        ---------
        song_ids: list of strings that are uri of type songs.
        
        Returns
        -------
        a pandas dataframe with the names of tracks and their features.
        '''

        self._refresh_token()
        song_ids = []
        for uri in uri_list:
            uridict = self._parse_uri(uri)
            if uridict['type'] != 'track':
                print ("Skipped uri that are not tracks")
            else:
                song_ids.append(uridict['id'])
        nsongs = len(song_ids)
        features = []
        tracks = []
        startat = 0
        #Query API. You can only query 100 songs at a time.
        while True:
            if nsongs > 100:
                response = self.oauth.get(self.base_url+ "audio-features/?ids=%s"%(",".join(song_ids[:100])))
                features = features + json.loads(response.content.decode())['audio_features']
                if get_song_names:
                    response = self.oauth.get(self.base_url+ "tracks/?ids=%s"%(",".join(song_ids[:100])))
                    tracks = tracks + json.loads(response.content.decode())['tracks']
                song_ids = song_ids[100:]
                nsongs = len(song_ids)
            else:
                response = self.oauth.get(self.base_url+ "audio-features/?ids=%s"%(",".join(song_ids[:]))) 
                features = features + json.loads(response.content.decode())['audio_features']
                if get_song_names:
                    response = self.oauth.get(self.base_url+ "tracks/?ids=%s"%(",".join(song_ids[:])))
                    tracks = tracks + json.loads(response.content.decode())['tracks']
                break

        features =  pd.DataFrame(features)
        if get_song_names:
            tracks = pd.DataFrame(tracks)
            features.insert(0, 'name', tracks['name'])
        return features

