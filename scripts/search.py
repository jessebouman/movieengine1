# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 12:17:52 2020

Script to handle actor search

@author: Spencer Ferguson-Dryden
"""
import os
import requests

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
    actor_movie_sets = [set((m['title'], m['year'], m['id']) for m in c) for c in actor_credits]
    shared_movies = set.intersection(*actor_movie_sets)

    # If there are no shared movies, return None and actor details
    if not shared_movies:
        return None, actor_details

    # Build result list
    movies = []
    for title, year, imdb_id in shared_movies:
        tmp = {
                'title': title,
                'year': year,
                'link': get_movie_link(imdb_id)
                }

        # find character names for the shared movie
        characters = [find_character(title, year, a_credits) for a_credits in actor_credits]
        tmp['characters'] = characters

        movies.append(tmp)

    return movies, actor_details

def get_actor_details(actor):
    """
    Returns the ID, name, and profile picture of the requested actor.
    If multiple actors with the same name exist, choose the first actor result # BUG
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

    # Find first actor in results
    for entry in data['results']:
        if entry['known_for_department'] == 'Acting':
            details = {
                    'id': entry['id'],
                    'name': entry['name'],
                    'img': 'https://image.tmdb.org/t/p/w185' + entry['profile_path'] if entry['profile_path'] else ''
                    }
            break

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

    # Build result list
    movies = [{
            'title': movie.get('title'),
            'year': movie.get('release_date', 'n.d.')[:4],
            'id': movie.get('id'),
            'character': movie.get('character')
            } for movie in data['cast']]

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

def find_character(title, year, actor_credits):
    """
    Returns the character name of the movie matching the title and year

    Parameters
    ----------
    title : str
        The movie title
    year : str
        The release date (as a string, could be 'n.d.')
    actor_credits : list
        A list of the actor's credits

    Returns
    -------
    character : str
        The name of the actor's character of the movie matching the title and year
    """

    # Match the title/year to the movie
    for movie in actor_credits:
        if movie['title'] == title and movie['year'] == year:
            break

    return movie['character']