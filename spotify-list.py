# Takes a list of artist and album names and saves the albums to Spotify as
# well as creates a playlist with all the tracks on those albums.
#
# Author: Eli Tucker
#
# Steps to use:
# 1) Create a text file in the format `Artist Name - Album Name`, with one
#    album per line. I used the Decluttr app to scan all my albums, created an
#    order, and then copy/pasted the list of artists and albums they emailed me.
# 2) Make sure you have installed spotipy.
#    TODO: put the steps I did here.
# 3) Set yourself up as an app developer and create an app on Spotify:
# 4) Setup your environment variables with info about your Spotify App:
#       export SPOTIPY_CLIENT_ID='1111f0ac549d4e829dda9d8ba444d2eb'
#       export SPOTIPY_CLIENT_SECRET='11111110bb13bb7d02eaed16b'
#       export SPOTIPY_REDIRECT_URI='http://localhost:8888/callback'
# 3) Run this script with the text file coming into stdin:
#       cat my-cds.txt | python spotify-list.py spotify_user_name playlist_name

import spotipy
import sys
import pprint
import spotipy.util as util
from datetime import datetime

if len(sys.argv) > 2:
    user_name = sys.argv[1]
    playlist_name = sys.argv[2]
else:
    print("Usage: %s spotify_user_name playlist_name" % (sys.argv[0],))
    sys.exit()

scope = 'user-library-read user-library-modify playlist-modify-public playlist-modify-private'
token = util.prompt_for_user_token(user_name, scope)

if not token:
    print("Can't get token for", username)
    exit()

sp = spotipy.Spotify(auth=token)
sp.trace = False

album_ids = []
errors = []

print("\nFinding albums...\n")
for line in sys.stdin:
    line = line.strip()
    print("Looking up:         '%s'" % line)
    artist_name, album_name = line.split(' - ', 1)
    search_string = "artist:'%s' album:'%s'" % (artist_name, album_name)
    result = sp.search(search_string, limit=1, type='album')

    try:
        album = result['albums']['items'][0]
        # pprint.pprint(album)
        print("Found artist/album: '%s - %s'" % (album['artists'][0]['name'], album['name']))
        album_ids.append(album['uri'])
    except:
        print("###### ERROR looking up '%s'" % line)
        errors.append(line)

# add albums to library
print("\nAdding albums to library...")
# From https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]
# split the list into max size 50 buckets
for album_ids_sublist in chunks(album_ids, 50):
    results = sp.current_user_saved_albums_add(albums=album_ids_sublist)

# Creating a playlist
playlist_description = "Auto created at %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print("\nCreating playlist '%s'..." % playlist_name)
result = sp.user_playlist_create(user_name, playlist_name)
playlist_id = result['id']
playlist_url = result['external_urls']['spotify']

# Adding tracks
print("\nAdding tracks to playlist...\n")
for album_id in album_ids:
    print("adding tracks from %s" % album_id)
    # Find all tracks for an album
    result = sp.album_tracks(album_id)
    track_uris = list(map(lambda x: x['uri'], result['items']))
    #pprint.pprint(track_uris)

    # Add tracks from the album
    sp.user_playlist_add_tracks(user_name, playlist_id, track_uris)

# Final output
print(" ")

if(len(errors) > 0):
    print("\nThe following albums could not be found: ")
    for error in errors:
        print("\t%s" % error)

print("\nYour playlist '%s' has been created at \n%s" % (playlist_name, playlist_url))
