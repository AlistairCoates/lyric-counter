import argparse
import musicbrainzngs
import requests
from requests.exceptions import HTTPError
from json.decoder import JSONDecodeError
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artist', type=str, nargs='+', help='The artist name')
    args = parser.parse_args()
    musicbrainzngs.set_useragent('lyric-counter', '0.1.0')

    # Get artist id
    print(musicbrainzngs.search_artists(query=args.artist, limit=1))
    result = musicbrainzngs.search_artists(sortname=args.artist, limit=1)

    artistid = result['artist-list'][0].get('id')
    print(artistid)
    artistname = result['artist-list'][0].get('name')

    # Get list of song titles
    titles = []
    works = musicbrainzngs.search_works(arid=artistid, limit=100)
    songs = works.get('work-list')
    if not songs:
        return
    for song in songs:
        titles.append(song.get('title'))
    work_count = works.get('work-count')
    pages = work_count//100
    for x in range(pages):
        offset = (x+1)*100
        works = musicbrainzngs.search_works(arid=artistid, limit=100, offset=offset)
        for song in works.get('work-list'):
            titles.append(song.get('title'))

    # Count lyrics of each song
    lyric_count = []
    for title in titles:
        try:
            result = requests.get('https://api.lyrics.ovh/v1/{}/{}'.format(artistname, title))
            lyrics = len(result.json().get('lyrics', '').replace('\n',' ').split())
            if lyrics > 0:
                lyric_count.append(lyrics)
        except (HTTPError, JSONDecodeError):
            pass

    # Caluculate statistics
    if lyric_count:
        mean = np.mean(lyric_count)
        std = np.std(lyric_count)
        var = np.var(lyric_count)
        min = np.amin(lyric_count)
        max = np.amax(lyric_count)
        print('mean: {}'.format(mean))
        print('standard deviation: {}'.format(std))
        print('variance: {}'.format(var))
        print('min: {}'.format(min))
        print('max: {}'.format(max))

    #print(works)
if __name__ == '__main__':
   main()
