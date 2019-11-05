import argparse
import musicbrainzngs
import requests
from requests.exceptions import HTTPError
from json.decoder import JSONDecodeError
import numpy as np
import asyncio
import aiohttp
import re


def get_artist_details(artist):

    result = musicbrainzngs.search_artists(sortname=artist, limit=1)
    artistid = result['artist-list'][0].get('id')
    artistname = result['artist-list'][0].get('name')

    return artistid, artistname


def get_song_list(id):

    # Get list of song titles
    works = musicbrainzngs.search_works(arid=id, limit=100)
    work_count = works.get('work-count')
    pages = int(np.ceil(work_count / 100.0))
    songs = works.get('work-list')
    titles = [song.get('title') for song in songs]

    for page in range(1, pages):
        offset = page * 100
        works = musicbrainzngs.search_works(arid=id, limit=100, offset=offset)
        for song in works.get('work-list'):
            titles.append(song.get('title'))
    return titles


async def count_lyrics(session, title, artistname):

    # Count lyrics of each song

    title = re.sub('[^0-9a-zA-Z]+', ' ', title)

    try:
        async with session.get('https://api.lyrics.ovh/v1/{}/{}'.format(artistname, title)) as response:
            lyrics = await response.json()
            return len(lyrics.get('lyrics', '').replace('\n',' ').split())

    except (HTTPError, JSONDecodeError, aiohttp.client_exceptions.ContentTypeError):
        pass



async def calculate_statistics(artist):

    artistid, artistname = get_artist_details(artist)

    titles = get_song_list(artistid)

    async with aiohttp.ClientSession() as session:
        lyric_count = await asyncio.gather(*[count_lyrics(session, title, artistname) for title in titles])

    print(lyric_count)

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artists', type=str, nargs='+', help='The artist name')
    args = parser.parse_args()
    artists = " ".join(args.artists).split(',')
    musicbrainzngs.set_useragent('lyric-counter', '0.1.0')
    for artist in artists:
        asyncio.run(calculate_statistics(artist))

if __name__ == '__main__':
   main()
