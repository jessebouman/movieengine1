# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 12:17:52 2020

Script to handle actor search

@author: Spencer Ferguson-Dryden
"""
import os
import requests
import aiohttp
import asyncio

from fuzzywuzzy import fuzz
from aiohttp import ClientSession

IMDB_KEY = os.environ.get('IMDB_KEY')

def handle_search(*actors):
    """
    Parameters
    ----------
    actors : list
        A list of actors to lookup

    Returns
    -------
    movies : list, None
        A list of dictionaries with the details of movie credits shared by the two actors
        None if one of the actors couldn't be found or they actors have no movies in common
    actor_details : list
        A list of dictionaries with the actor details
    """

    # Search and get profile details for each actor
    actor_details = list(map(lambda actor : get_actor_details(actor), actors))
    actor_ids = [actor['id'] for actor in actor_details]

    # Get acting roles for each actor
    actor_credits = list(map(lambda a_id : get_actor_credits(a_id), actor_ids))

    # If either actor_id is None or either actor_credits is None, then return (no result, but display names/photos)
    if None in actor_ids or None in actor_credits:
        return None, actor_details

    # If both actors are the same, return None
    if len(list(dict.fromkeys(actor_ids))) < 2:
        return None, actor_details

    # Find any matches between the sets of movies
    actor_movie_sets = [set(list(ids['movies'])) for ids in actor_credits]
    shared_movies = set.intersection(*actor_movie_sets)

    # Find any matches between the sets of TV shows
    actor_tv_sets = [set(list(ids['tv'])) for ids in  actor_credits]
    shared_tv = set.intersection(*actor_tv_sets)

    # If there are no shared movies and no shared TV shows, return None and actor details
    if not shared_movies and not shared_tv:
        return None, actor_details

    if shared_movies:
        # Async IMDB ID retrieval
        movie_links = dict(asyncio.run(get_links(shared_movies, media_type='movie')))

        # Build movie list
        movies = [{
                    'title': actor_credits[0]['movies'][m_id]['title'],
                    'year': actor_credits[0]['movies'][m_id]['year'],
                    'characters': [a['movies'][m_id]['character'] for a in actor_credits],
                    'link': movie_links[m_id]
                } for m_id in shared_movies]
    else:
        movies = []

    if shared_tv:
        # Async IMDB ID retrieval
        tv_links = dict(asyncio.run(get_links(shared_tv, media_type='tv')))

        tv_shows = [{
                    'title': actor_credits[0]['tv'][m_id]['title'],
                    'year': actor_credits[0]['tv'][m_id]['year'],
                    'characters': [a['tv'][m_id]['character'] for a in actor_credits],
                    'episodes': [a['tv'][m_id]['episodes'] for a in actor_credits],
                    'link': tv_links[m_id]
                } for m_id in shared_tv]
    else:
        tv_shows = []

    media = movies + tv_shows
    media = sorted(media, key = lambda m : m['year'], reverse=True) # sort by newest -> oldest

    return media, actor_details

def get_actor_details(actor):
    """
    Returns the ID, name, and profile picture of the requested actor.
    If multiple actors with the same name exist, choose the most popular actor

    Parameters
    ----------
    actor : str
        An search query for an actor's name

    Returns
    -------
    details : dict, None
        The IMDB API ID, name, and photo of the actor
        Defaults to returns None as the id and actor as the name if the search query yields no result
    """

    # Default result
    details = {'id': None, 'name': actor}

    # Construct and execute API query
    url = 'https://api.themoviedb.org/3/search/person'
    params = {
            'api_key': IMDB_KEY,
            'query': actor,
            'include_adult': 'false'
            }
    response = requests.get(url, params=params)

    # Convert to dictionary
    try:
        data = response.json()
    except:
        return details # Invalid IMDB response

    # Check if the actor exists
    if not data['results']:
        return details
    else:
        # Fetch multiple pages and append if multiple pages exist in results
        if data.get('total_pages', 1) > 1:
            extra_data = asyncio.run(fetch_more_pages(actor, data.get('total_pages')))
            data = data['results']
            for d in extra_data:
                data.extend(d)
        else:
            data = data['results']

    # Filter for actors loosely matching string query
    data = list(filter(lambda d : d.get('known_for_department') == 'Acting', data))
    data = list(filter(lambda d : match_name(actor, d.get('name', '')) > 175, data))
    if not data:
        return details # No actors in result list

    # Sort by popularity and choose the most popular actor
    exact_match = list(filter(lambda d : d.get('name', '').lower() == actor.lower(), data))
    data = sorted(data, key = lambda a : a.get('popularity', 0), reverse=True)

    # Give preference to exact name match if at least a first and last name is provided
    entry = exact_match[0] if exact_match and len(actor.split()) > 1 else data[0]
    details = {
            'id': entry['id'],
            'name': entry['name'],
            'img': 'https://image.tmdb.org/t/p/w185' + entry['profile_path'] if entry['profile_path'] else ''
            }

    return details

async def fetch_more_pages(query, pages):
    """
    Wrapper to return more search result pages
    """
    # Max ten page limit
    if pages > 12:
        pages = 12

    async with ClientSession() as session:
        res = await asyncio.gather(*[get_another_page(query, page, session) for page in range(2, pages)])
        return res

async def get_another_page(query, page, session):
    """
    Returns a page (> 1) from the specified search results
    """

    url = f'https://api.themoviedb.org/3/search/person?api_key={IMDB_KEY}&query={query}&page={page}&include_adult=false'
    response = await session.request(method='GET', url=url)

    try:
        data = await response.json()
    except:
        return []

    return data['results']

def get_actor_credits(actor_id):
    """
    Finds a list of movies and TV shows the requested actor has acted in

    Parameters
    ----------
    actor_id : int, None
        The IMDB ID of an actor

    Returns
    -------
    movies, tv : dict, None
        A list of dictionaries with the details of each movie/show the actor acted in
        None if the actor has no movies/shows listed
    """

    # Return None if the actor could not be found
    if actor_id is None:
        return None

    # Construct and execute API query
    url = f'https://api.themoviedb.org/3/person/{actor_id}/combined_credits'
    response = requests.get(url, params={'api_key': IMDB_KEY})

    # Convert to dictionary
    try:
        data = response.json()
    except:
        return None # Invalid IMDB response

    # Return None if actor has no movies
    if 'cast' not in data.keys():
        return None
    else:
        data = data['cast']

    # Filter out "Making of" entries for movies
    def character_filter(character):
        if not character:
            return False

        for c in ['himself', 'herself', 'self']:
            if c in character.lower():
                return False

        return True

    data = list(filter(lambda d : character_filter(d.get('character', '')), data))

    # Build movie result list
    movie_data = list(filter(lambda d : d.get('media_type') == 'movie', data))
    movies = {
            movie.get('id'): {
                    'title': movie.get('title'),
                    'year': movie.get('release_date', 'n.d.')[:4],
                    'character': movie.get('character', '')
                    } for movie in movie_data
            }

    # Build TV result list
    tv_data = list(filter(lambda d : d.get('media_type') == 'tv', data))
    tv_shows = {}
    for tv in tv_data: # prevent secondary characters from listing
        tv_shows.setdefault(tv.get('id'),
                            {
                                    'title': tv.get('name'),
                                    'year': tv.get('first_air_date', 'n.d.')[:4],
                                    'character': tv.get('character', ''),
                                    'episodes': tv.get('episode_count', 0)
                            })

    return {'movies': movies, 'tv': tv_shows}

async def get_links(media, media_type):
    """
    Wrapper for async IMDB link retrieval
    """
    async with ClientSession() as session:
        res = await asyncio.gather(*[get_imdb_link(tmdb_id, media_type, session) for tmdb_id in media])
        return res

async def get_imdb_link(tmbd_id, media_type, session):
    """
    Returns the IMDB page link for the requested movie/show.

    Parameters
    ----------
    movie_id : int
        A TMDB movie/TV ID

    Returns
    -------
    link : str
        The IMDB page url of the requested movie/show
        Empty string if the movie/show does not have an IMDB page
    """

    # Sanity check - make sure an int is passed
    if not isinstance(tmbd_id, int):
        return tmbd_id, ''

    # Construct and execute API query
    url = f'https://api.themoviedb.org/3/{media_type}/{tmbd_id}/external_ids?api_key={IMDB_KEY}'
    response = await session.request(method='GET', url=url)

    # Convert to dictionary
    try:
        data = await response.json()
    except:
        return tmbd_id, '' # Invalid IMDB response

    return tmbd_id, data.get('imdb_id', '')

def match_name(actor, entry):
    """
    Returns a score (0-200) signifying the alikeness between the actor name and the entry

    Parameters
    ----------
    actor : str
        The search string
    entry : str
        A potential result

    Returns
    -------
    score : int
        A score between 0 and 200
    """

    # Split and normalize strings
    search_string = actor.strip().lower().split(' ')
    entry_names = entry.lower().split(' ')

    if len(search_string) == 1: # If only one name is entered, choose the best match
        first_name_score = fuzz.partial_ratio(search_string[0], entry_names[0])
        last_name_score = fuzz.partial_ratio(search_string[0], entry_names[-1])
        if first_name_score > last_name_score:
            return first_name_score * 2
        else:
            return last_name_score *2
    else: # If two names are entered return the composite score
        first_name_score = fuzz.partial_ratio(search_string[0], entry_names[0])
        last_name_score = fuzz.partial_ratio(search_string[-1], entry_names[-1])
        return first_name_score + last_name_score