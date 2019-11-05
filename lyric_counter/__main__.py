import aiohttp
import asyncio
import argparse
import json
import logging
import urllib.parse

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


async def get_artist_details(session, artist):
    """
    Function that finds the nearest matching artist to user input.

    Args:
        session (aiohttp.ClientSession): An object for creating client sessions and making requests.
        artist (str): User input string used to query api.

    Returns:
        str x 2: The stored artist uid, the stored name of the artist.
    """

    artist = urllib.parse.quote(artist, safe='')
    async with session.get('http://musicbrainz.org/ws/2/artist/?query={}&limit=1&fmt=json'.format(artist)) as response:
        result = await response.json()
        artistid = result['artists'][0].get('id')
        artistname = result['artists'][0].get('name')
    return artistid, artistname


async def get_song_list(session, artistid):
    """
    Function for finding all the songs associated with an artist.

    Args:
        session (aiohttp.ClientSession): An object for creating client sessions and making requests.
        artistid (str): The stored artist uid

    Returns:
        list: A list of song names.

    """
    titles = []
    offset = 0
    while True:
        async with session.get('https://musicbrainz.org/ws/2/work/?artist={}&limit=100&offset={}&fmt=json'.format(artistid, offset)) as response:
            result = await response.read()
            result = json.loads(result)
            works = result.get('works')
            if not works:
                break
            offset += 100
            for song in works:
                titles.append(song.get('title'))
    return titles


async def count_lyrics(session, artistname, title):
    """
    Function for counting the lyrics in a specific song.

    Args:
        session (aiohttp.ClientSession):  An object for creating client sessions and making requests.
        artistname (str): The name of songs associated artist.
        title (str): A title of the required song.

    Returns:
        int: The number of words in the song.
    """
    # Count lyrics of each song

    title = urllib.parse.quote(title, safe='')

    async with session.get('https://api.lyrics.ovh/v1/{}/{}'.format(artistname, title)) as response:
        if response.status == 200:
            try:
                result = await response.read()
                result = json.loads(result)
                lyrics = result.get('lyrics')
                if lyrics:
                    return len(lyrics.replace('\n',' ').split())
            except Exception as e:
                logging.warning('Error reading lyrics: {}'.format(e))
        return


async def calculate_statistics(artist):
    """
    Function for caluculating the lyric statistics of a music artist.

    Args:
        artist (str): User input string used to query api.
    """

    async with aiohttp.ClientSession() as session:
        artistid, artistname = await get_artist_details(session, artist)
        titles = await get_song_list(session, artistid)
        lyric_count = await asyncio.gather(*[count_lyrics(session, artistname, title) for title in titles])

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
        #plt.plot(np.sort(lyric_count))
        sns.distplot(lyric_count, hist=True, kde=True, bins = int(180/5), color = 'darkblue',
                     hist_kws={'edgecolor':'black'}, kde_kws={'linewidth': 4})
        plt.show()



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artists', type=str, nargs='+', help='The artist name')
    args = parser.parse_args()
    artists = " ".join(args.artists).split(',')
    for artist in artists:
        asyncio.run(calculate_statistics(artist))


if __name__ == '__main__':
   main()
