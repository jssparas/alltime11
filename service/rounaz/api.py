import requests
import time

from django.core.cache import cache
from django.conf import settings
from .constants import *
from .utils import parse_response


ROUNAZ_BASE_URL = settings.ROUNAZ_BASE_URL


def get_header():
    headers = {
        "rs-token": get_authentication_token()
    }
    return headers


def set_authentication_token():
    ''' Api provide authentication token to call other Rounaz rest Apis
        format type: data
    '''
    try:
        url = f'{ROUNAZ_BASE_URL}v5/core/{settings.ROUNAZ_PROJECT_KEY}/auth/'
        payload = {
                    "api_key": settings.ROUNAZ_API_KEY
                }
        try:
            resp = requests.post(url, json=payload, timeout=API_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception occurred during Rounaz Auth API')
            raise
        data, error = parse_response(resp.json())
        if error:
            raise ValueError(f'Rounaz Auth Api Error: {error.get("msg")}')
        return data.get("token"), data.get("expires")
    except Exception as ex:
        raise ex


def get_authentication_token():
    if cache.has_key(ROUNAZ_API_TOKEN):
        return cache.get(ROUNAZ_API_TOKEN)
    try:
        print('Generating new token for Rounaz')
        new_token, token_expiry = set_authentication_token()
        current_time_stamp = time.time()
        cache.set(ROUNAZ_API_TOKEN, new_token, timeout=int(token_expiry - current_time_stamp))
        return new_token
    except Exception as ex:
        raise ex


def get_featured_tournaments():
    ''' Api provide list of tournaments data including Official names, start dates, 
        venues, host countries, organising cricket associations and details about the competitions
    '''
    try:
        url = f'{ROUNAZ_BASE_URL}v5/cricket/{settings.ROUNAZ_PROJECT_KEY}/featured-tournaments/'
        try:
            resp = requests.get(url, headers=get_header(), timeout=API_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception occurred during Rounaz Featured Tournaments API')
            raise
        data, error = parse_response(resp.json())
        if error:
            raise ValueError(f'Rounaz Featured Tournaments Api Error: {error.get("msg")}')
        return data
    except Exception as ex:
        raise ex


def get_tournament_featured_matches(tournament_key):
    ''' Api provide list of featured matches of a tournament including
        Ongoing, completed and upcoming tournament data including 
        venues, start dates, match status, flags and match key etc
        upcoming, on
    '''
    try:
        url = f'{ROUNAZ_BASE_URL}v5/cricket/{settings.ROUNAZ_PROJECT_KEY}/tournament/{tournament_key}/featured-matches-2/'
        try:
            resp = requests.get(url, headers=get_header(), timeout=API_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception '
                      'occurred during Rounaz Featured Tournament Matches API')
            raise
        data, error = parse_response(resp.json())
        if error:
            raise ValueError(f'Rounaz Featured Tournament Matches Api Error: {error.get("msg")}')
        return data
    except Exception as ex:
        raise ex


def get_tournament_fixtures(tournament_key, page_key=None):
    ''' Api provide list of matches of a tournament including matches played 
        in the past, present and the ones to be played in the future with pagination
        data included venues, start dates, match status, flags and match key etc
    '''
    try:
        url = f'{ROUNAZ_BASE_URL}v5/cricket/{settings.ROUNAZ_PROJECT_KEY}/tournament/{tournament_key}/fixtures/'
        if page_key: # with pagination
            url = f'{url}{page_key}/'
        try:
            resp = requests.get(url, headers=get_header(), timeout=API_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception occurred during Rounaz Featured Tournament Fixtures API')
            raise
        data, error = parse_response(resp.json())
        if error:
            raise ValueError(f'Rounaz Featured Tournament Fixtures Api Error: {error.get("msg")}')
        return data
    except Exception as ex:
        raise ex


def get_featured_matches():
    ''' Api provide list of matches of a particular period data including 
        venues, start dates, match status, flags and match key etc
        Match list includes five upcoming, five completed and five live matches
    '''
    try:
        url = f'{ROUNAZ_BASE_URL}v5/cricket/{settings.ROUNAZ_PROJECT_KEY}/featured-matches-2/'
        try:
            resp = requests.get(url, headers=get_header(), timeout=API_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception '
                      'occurred during Rounaz Featured Matches API')
            raise
        data, error = parse_response(resp.json())
        if error:
            raise ValueError(f'Rounaz Featured Matches Api Error: {error.get("msg")}')
        return data
    except Exception as ex:
        raise ex


def get_match_data(match_key):
    ''' Api provide match data by match key inlcuded get real-time scorecard, match status,
        team lineups, player of the match, team scores, individual player scores, team squad etc
        can be called by webhook
    '''
    try:
        url = f'{ROUNAZ_BASE_URL}v5/cricket/{settings.ROUNAZ_PROJECT_KEY}/match/{match_key}/'
        try:
            resp = requests.get(url, headers=get_header(), timeout=API_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception occurred during Rounaz get Match API')
            raise
        data, error = parse_response(resp.json())
        if error:
            raise ValueError(f'Rounaz get Match Api Error: {error.get("msg")}')
        return data
    except Exception as ex:
        raise ex


def get_match_player_credits(match_key):
    ''' Api provide credits of all players in the squads of a match
    '''
    try:
        url = f'{ROUNAZ_BASE_URL}v5/cricket/{settings.ROUNAZ_PROJECT_KEY}/fantasy-match-credits/{match_key}/'
        try:
            resp = requests.get(url, headers=get_header(), timeout=API_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception occurred during Rounaz get Match Player Credit API')
            raise
        data, error = parse_response(resp.json())
        if error:
            raise ValueError(f'Rounaz get Match Player Credit Api Error: {error.get("msg")}')
        return data
    except Exception as ex:
        raise ex


def get_match_player_points(match_key):
    ''' Api provide Points awarded to the players based on their performances in a match
        can be called by webhook
    '''
    try:
        url = f'{ROUNAZ_BASE_URL}v5/cricket/{settings.ROUNAZ_PROJECT_KEY}/fantasy-match-points/{match_key}/'
        try:
            resp = requests.get(url, headers=get_header(), timeout=API_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            print('Timeout or ConnectionError exception occurred during Rounaz get Match Player Points API')
            raise
        data, error = parse_response(resp.json())
        if error:
            raise ValueError(f'Rounaz get Match Player Points Api Error: {error.get("msg")}')
        return data
    except Exception as ex:
        raise ex


def fetch_player_points(match_key):
    points = {}
    points_data = get_match_player_points(match_key).get("points", [])
    # print("points_data----------", points_data)
    for point in points_data:
        points[point.get("player_key")] = {
                                            "rank": point.get("rank"),
                                            "points": point.get("points"),
                                            "tournament_points": point.get("tournament_points")
                                        }
    return points
