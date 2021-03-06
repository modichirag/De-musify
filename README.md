## See your music
The project aims to allow users to get their own, or other public playlists on spotify, get [audio features](https://developer.spotify.com/web-api/get-audio-features/ "List of features") for the songs in those playlists and make a scatter plot for those features to be able to **see** music. <br>
<br>
The module *get_spotify_music/spotifyuser.py* has the main class. Before starting, you need to do a class instantiation and authorize through your spotify account. Then, the user can use functions like get_playlist_details and get_features_playlist to get the required features for their playlists. <br>
<br>
The module *get_spotify_music/plotting.py* provides functions to:
 - make a scatter plot between multiple features of a given playlist 
 - make a scatter plot between any two features for multiple playlists. 

Refer to get_started.ipynb for an example run. 
<br>

### Planned extensions:
 - Extend to get categories and their playlist and songs.
 - Extend to get artists and their top songs.
 - A small ML setup that can recommend new songs based on features given.
 - Provide more plotting functionalities. 
