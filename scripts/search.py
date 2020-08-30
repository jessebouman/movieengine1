# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 12:17:52 2020

Script to handle actor search

@author: Spencer Ferguson-Dryden
"""
import os
import requests
from fuzzywuzzy import fuzz

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
        None if one of the actors couldn't be found
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
    actor_movie_sets = [set(list(movie_ids)) for movie_ids in actor_credits]
    shared_movies = set.intersection(*actor_movie_sets)

    # If there are no shared movies, return None and actor details
    if not shared_movies:
        return None, actor_details

    # Build result list
    movies = [{
            'title': actor_credits[0][m_id]['title'],
            'year': actor_credits[0][m_id]['year'],
            'characters': [a[m_id]['character'] for a in actor_credits],
            'link': get_movie_link(m_id),
            } for m_id in shared_movies]
    movies = sorted(movies, key = lambda m : m['year'], reverse=True) # sort by oldest -> newest

    return movies, actor_details

def get_actor_details(actor):
    """
    Returns the ID, name, and profile picture of the requested actor.
    If multiple actors with the same name exist, choose the most popular actor
    If no actor exists, return None

    Parameters
    ----------
    actor : str
        An actor's name

    Returns
    -------
    details : dict, None
        The IMDB API ID, name, and photo of the actor
        None if the actor does not exist in the IMDB API
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
        data = data['results']

    # Filter for actors loosely matching string query
    data = list(filter(lambda d : d['known_for_department'] == 'Acting', data))
    data = list(filter(lambda d : match_name(actor, d['name']) > 175, data))
    if not data:
        return details # No actors in result list

    # Sort by popularity and choose the most popular actor
    exact_match = list(filter(lambda d : d['name'].lower() == actor.lower(), data))
    data = sorted(data, key = lambda a : a['popularity'], reverse=True)
    entry = exact_match[0] if exact_match else data[0] # give preference to exact name match
    details = {
            'id': entry['id'],
            'name': entry['name'],
            'img': 'https://image.tmdb.org/t/p/w185' + entry['profile_path'] if entry['profile_path'] else ''
            }

    return details

def get_actor_credits(actor_id):
    """
    Finds a list of movies the requested actor has acted in

    Parameters
    ----------
    actor_id : int, None
        The IMDB ID of an actor

    Returns
    -------
    movies : list, None
        A list of dictionaries with the details of each movie the actor acted in
        None if the actor has no movies listed
    """

    # Return None if the actor could not be found
    if actor_id is None:
        return None

    # Construct and execute API query
    url = f'https://api.themoviedb.org/3/person/{actor_id}/movie_credits'
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

    # Filter out "Making of" entries
    def character_filter(character):
        if not character:
            return False

        for c in ['himself', 'herself', 'self']:
            if c in character.lower():
                return False

        return True

    data = list(filter(lambda d : character_filter(d['character']), data))

    # Build result list
    movies = {
            movie.get('id'): {
                    'title': movie.get('title'),
                    'year': movie.get('release_date', 'n.d.')[:4],
                    'character': movie.get('character', '')
                    } for movie in data
            }

    return movies

def get_movie_link(movie_id):
    """
    Returns the IMDB page link for the requested movie.

    Parameters
    ----------
    movie_id : int
        A TMDB movie ID

    Returns
    -------
    link : str
        The IMDB page url of the requested movie
        Empty string if the movie does not have an IMDB page
    """

    # Sanity check - make sure an int is passed
    if not isinstance(movie_id, int):
        return ''

    # Construct and execute API query
    url = f'https://api.themoviedb.org/3/movie/{movie_id}'
    response = requests.get(url, params={'api_key': IMDB_KEY})

    # Convert to dictionary
    try:
        data = response.json()
    except:
        return '' # Invalid IMDB response

    return data.get('imdb_id', '')

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