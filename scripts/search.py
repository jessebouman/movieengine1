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

    # Get ID for each actor
    actor_ids = list(map(lambda a : get_actor_id(a), actors))

    # Get profile details for each actor
    actor_details = list(map(lambda a_id : get_actor_details(a_id), actor_ids))

    # Get acting roles for each actor
    actor_credits = list(map(lambda a_id : get_actor_credits(a_id), actor_ids))

    # If either actor_id is None or either actor_credits is None, then return (no result, but display names/photos)
    if None in actor_ids or None in actor_credits:
        return None, actor_details

    # Find any matches between the sets of movies
    actor_movie_sets = [set((m['title'], m['year']) for m in c) for c in actor_credits]
    shared_movies = set.intersection(*actor_movie_sets)

    # If there are no shared movies, return empty list and actor details
    if not shared_movies:
        return [], actor_details

    # Build result list
    movies = []
    for title, year in shared_movies:
        tmp = {
                'title': title,
                'year': year,
                }

        # find character names for the shared movie
        characters = [find_character(title, year, a_credits) for a_credits in actor_credits]
        tmp['characters'] = characters

        movies.append(tmp)

    return movies, actor_details

def get_actor_id(actor):
    """
    Returns the ID of the requested actor.
    If multiple actors with the same name exist, choose the first actor result # BUG
    If no actor exists, return None

    Parameters
    ----------
    actor : str
        A actor's name

    Returns
    -------
    actor_id : int, None
        The IMDB API ID of the actor or None if the actor does not exist in the IMDB API
    """

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
        return None # Invalid IMDB response

    # Check if the actor exists
    if not data['results']:
        return  None

    # Find first actor in results
    actor_id = None
    for entry in data['results']:
        if entry['known_for_department'] == 'Acting':
            actor_id = entry['id']
            break

    return actor_id

def get_actor_details(actor_id):
    """
    Returns the details of the requested actor.

    Parameters
    ----------
    actor_id : int, None
        The IMDB ID of an actor

    Returns
    -------
    details : dict, None
        the IMDB API ID of the actor or None if the actor_id is None
    """

    # Return None if the actor could not be found
    if actor_id is None:
        return None

    # Construct and execute API query
    url = f'https://api.themoviedb.org/3/person/{actor_id}'
    response = requests.get(url, params={'api_key': IMDB_KEY})

    # Convert to dictionary
    try:
        data = response.json()
    except:
        return None # Invalid IMDB response

    # Build result dictionary
    details = {
            'name': data['name'],
            'img': 'https://image.tmdb.org/t/p/w185' + data['profile_path']
            }

    return details

def get_actor_credits(actor_id):
    """
    Returns the details of the requested actor.

    Parameters
    ----------
    actor_id : int, None
        The IMDB ID of an actor

    Returns
    -------
    movies : list, None
        A list of dictionaries with the details of each move the actor acted in
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
            'character': movie.get('character')
            } for movie in data['cast']]

    return movies

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