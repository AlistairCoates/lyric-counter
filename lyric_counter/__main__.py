import aiohttp
import asyncio
import argparse
import json
import logging
import urllib.parse

import matplotlib.pyplot as plt
import numpy as np


async def get_artist_details(session, artist):
    """
    Function that finds the nearest matching artist to user input.

    Args:
        session (aiohttp.ClientSession): An object for creating client sessions and making requests.
        artist (str): User input string used to query api.

    Returns:
        dict: A dictionary of artist information.
    """

    artist = urllib.parse.quote(artist, safe='')
    async with session.get('http://musicbrainz.org/ws/2/artist/?query={}&limit=1&fmt=json'.format(artist)) as response:
        try:
            result = await response.json()
            artist_details = result['artists'][0]
        except Exception:
            logging.warning('Cannot get artist details: {}'.format(artist))
            return
    return artist_details


async def get_song_list(session, artistid):
    """
    Function for finding all the songs associated with an artist.

    Args:
        session (aiohttp.ClientSession): An object for creating client sessions and making requests.
        artistid (str): The stored artist uid.

    Returns:
        list: A list of song names.

    """
    titles = []
    offset = 0
    while True:
        async with session.get('https://musicbrainz.org/ws/2/work/?artist={}&limit=100&offset={}&fmt=json'.format(
                                artistid, offset)) as response:
            try:
                result = await response.read()
                result = json.loads(result)
                works = result.get('works')
                if not works:
                    break
                offset += 100
                titles += [song.get('title') for song in works]
            except Exception:
                logging.warning('Cannot get song list: {}'.format(artistid))
                return
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

    title = urllib.parse.quote(title, safe='')

    async with session.get('https://api.lyrics.ovh/v1/{}/{}'.format(artistname, title)) as response:
        try:
            result = await response.read()
            result = json.loads(result)
            lyrics = result.get('lyrics')
            if lyrics:
                return len(lyrics.replace('\n', ' ').split())
        except Exception:
            logging.warning('Error reading lyrics: {} - {}'.format(artistname, title))
            return


async def get_lyrics_count(session, artist):
    """
    Function for caluculating the lyric statistics of a music artist.

    Args:
        session (aiohttp.ClientSession):  An object for creating client sessions and making requests.
        artist (str): User input string used to query api.

    Returns:
        list: A list of the number of words in each song.
    """

    artist_details = await get_artist_details(session, artist)
    if not artist_details:
        return
    artist_id = artist_details.get('id')
    artist_name = artist_details.get('name')

    titles = await get_song_list(session, artist_id)
    if not titles:
        return

    lyric_count = await asyncio.gather(*[count_lyrics(session, artist_name, title) for title in titles])
    if not lyric_count:
        return

    lyric_count = np.array(lyric_count)
    lyric_count = lyric_count[lyric_count != np.array(None)]

    return lyric_count


async def evaluate_artists(artists):
    """
    Function to calculate and report on the stats of the lyrics.

    Args:
        artists (list): A list of artist names to be queried.
    """

    async with aiohttp.ClientSession() as session:
        artists_lyrics = await asyncio.gather(*[get_lyrics_count(session, artist) for artist in artists])

    for index, lyrics in enumerate(artists_lyrics):
        if lyrics is not None:
            print(artists[index])
            print('mean: {}'.format(np.mean(lyrics)))
            print('std: {}'.format(np.std(lyrics)))
            print('var: {}'.format(np.var(lyrics)))
            print('min: {}'.format(np.amin(lyrics)))
            print('max: {}'.format(np.amax(lyrics)))
            plt.figure(artists[index])
            plt.hist(lyrics, bins=36, facecolor='blue', alpha=0.5)
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artists', type=str, nargs='+', help='The artist name')
    args = parser.parse_args()
    artists = " ".join(args.artists).split(',')
    asyncio.run(evaluate_artists(artists))


if __name__ == '__main__':
    main()
