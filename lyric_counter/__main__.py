import argparse
import numpy as np
import asyncio
import aiohttp
import urllib.parse
import json
import logging


async def get_artist_details(session, artist):

    artist = urllib.parse.quote(artist, safe='')
    async with session.get('http://musicbrainz.org/ws/2/artist/?query={}&limit=1&fmt=json'.format(artist)) as response:
        result = await response.json()
        artistid = result['artists'][0].get('id')
        artistname = result['artists'][0].get('name')
    return artistid, artistname

async def get_song_list(session, id):

    titles = []
    offset = 0
    while True:
        async with session.get('https://musicbrainz.org/ws/2/work/?artist={}&limit=100&offset={}&fmt=json'.format(id, offset)) as response:
            result = await response.read()
            result = json.loads(result)
            works = result.get('works')
            if not works:
                break
            offset += 100
            for song in works:
                titles.append(song.get('title'))
    return titles


async def count_lyrics(session, title, artistname):

    # Count lyrics of each song

    title = urllib.parse.quote(title, safe='')

    try:
        async with session.get('https://api.lyrics.ovh/v1/{}/{}'.format(artistname, title)) as response:
            result = await response.read()
            result = json.loads(lyrics)
            lyrics = lyrics.get('lyrics')
            if lyrics:
                return lyrics.replace('\n',' ').split())
            else:
                return

    except:
        pass


async def calculate_statistics(artist):

    async with aiohttp.ClientSession() as session:
        artistid, artistname = await get_artist_details(session, artist)
        titles = await get_song_list(session, artistid)
        lyric_count = await asyncio.gather(*[count_lyrics(session, title, artistname) for title in titles])

    if lyric_count:
        lyric_count = np.array(lyric_count)
        lyric_count = lyric_count[lyric_count != np.array(None)]

    # Caluculate statistics

        mean = np.mean(lyric_count)
        std = np.std(lyric_count)
        var = np.var(lyric_count)
        min = np.amin(lyric_count)
        max = np.amax(lyric_count)
        print(artistname)
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
    for artist in artists:
        asyncio.run(calculate_statistics(artist))

if __name__ == '__main__':
   main()
