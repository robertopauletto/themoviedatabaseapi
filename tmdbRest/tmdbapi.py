# tmdbapi.py

import enum
import json
from pprint import pprint
import requests
import tmdbRest.entities as ent
import tmdbRest.genres as generi

__doc__ = """tmdbapi.py"""
__version__ = "0.1"
__changelog__ = """

"""


class Media(enum.Enum):
    """Represent a media"""
    unknown = 0
    movie = 1
    tv = 2


class SearchType(enum.Enum):
    """Type of search"""
    company = 0
    collection = 1
    keyword = 2
    movie = 3
    multi = 4
    person = 5
    tv = 6


def _parse_media(value: str) -> Media:
    if value.lower() in 'movies films cinema':
        return Media.movie
    elif value.lower() in 'tv television t.v.':
        return Media.tv
    return Media.unknown


ROUTES = {
    'root': r'https://api.themoviedb.org/3/',
    'new_session': r'authentication/session/new',
    'find': r'search/{}',  # Generic
    'genres': r'genre/{}/list',  # Movies or TV
    'person': r'person/{}',  # Generic
    'item': r'{}/{}',  # Generic item by id
    'episode': r'tv/{}/season/{}/episode/{}',  # Tv
    'season': r'tv/{}/season/{}',
}


def _get_route_old(action: str,  subroute: SearchType):
    """
    Compose the api call, depending on `media`
    :param action: action to perform
    :param subroute: media type
    :return:the call to tmdb
    """
    if action not in ROUTES:
        return None
    return f"{ROUTES['root']}{ROUTES[action].format(subroute.name)}"


def _get_route(action: str,  params):
    """
    Compose the api call, depending on `media`
    :param action: action to perform
    :param subroute: media type
    :return:the call to tmdb
    """
    if action not in ROUTES:
        return None
    if not isinstance(params, tuple):
        params = params,
    print()
    return f"{ROUTES['root']}{ROUTES[action].format(*params)}"


class TmDBSessionException(Exception):
    pass


class TmDBSession:
    """Manage info via themoviedb API"""
    def __init__(self, api_key: str, language=None, media=Media.unknown):
        """
        Gets the private authentication key
        :param api_key: the secret key
        :param language: language used (may lack some translations, dependeing
                         on language (defaults to en-US)
        :param media: the actual media will be set in the subclasses
        """
        self._api_key = api_key
        self._lang = language or 'en-US'
        self._media = media

    @property
    def language(self) -> str:
        """Get the language"""
        return self._lang

    @language.setter
    def language(self, value):
        """
        Set the language
        :param value:
        :return:
        """
        self._lang = value

    def _get_payload(self) -> dict:
        """
        Gets the payload with the api key, the caller will extend the
        dict with the parameters required by the specific api
        """
        payload = {'api_key': self._api_key, 'language': self._lang}
        return payload

    def search(self, query, search_type: SearchType, **kwargs):
        """Generic search"""
        route = _get_route('find', search_type.name)
        payload = self._get_payload()
        payload['query'] = query
        resp = requests.get(route, payload)
        return resp.json()

    def get_item(self, id, search_type: SearchType):
        route = _get_route('item', (search_type.name, id))
        payload = self._get_payload()
        resp = requests.get(route, payload)
        return resp.json()

    def get_season(self, show_id: int, season_no: int):
        route = _get_route('season', (show_id, season_no))
        payload = self._get_payload()
        resp = requests.get(route, payload)
        return resp.json()

    def genres(self, search_type: SearchType) -> list:
        """Get a list of genres in the form of id, name"""
        route = _get_route('genres', search_type)
        payload = self._get_payload()
        resp = requests.get(route, payload)
        genres_ = list()
        for genre in resp.json()['genres']:
            genres_.append((genre['id'], genre['name']))
        return genres_


class TmDBMovieSession(TmDBSession):
    """Session for movies"""
    def __init__(self, api_key, language=None):
        TmDBSession.__init__(self, api_key, language, Media.movie)


class TmDBTvSession(TmDBSession):
    """Session for television"""
    def __init__(self, api_key: str, language=None):
        TmDBSession.__init__(self, api_key, language, Media.tv)

    def search_show(self, showname: str, exact=False):
        resp = self.search(showname, SearchType.tv)
        shows = [ent.TvShowFromSearch(show) for show in resp['results']]
        if exact:
            return [show for show in shows
                    if show.name.lower() == showname.lower()]
        return shows

    def get_show(self, show_id: int) -> ent.TvShow:
        """
        Get info for the show number `show_id`
        :param show_id:
        :return: a TvShow object
        """
        return ent.TvShow(self.get_item(show_id, SearchType.tv))

    def get_show_and_seasons(self, show_id: int) -> tuple:
        """
        Get info for the show number `show_id` and all the seaason
        :param show_id:
        :return: A TvShow object and a list of Season objects
        """
        seasons = list()
        show = self.get_show(show_id)
        for season_no in range(0, show.tot_seasons):
            seasons.append(self.get_season(show.id, season_no+1))
        return show, seasons

    def get_show_seasons_and_episodes(self, show_id: int) -> tuple:
        """
        Get info for the show number `show_id`, all the seaason end episodes
        :param show_id:
        :return: A TvShow object and a list of Season objects with a list of
                 Episodes
        """
        pass  # TODO:


def session_factory(media_type: str, apy_key: str, language=None):
    if _parse_media(media_type.lower()) == Media.movie:
        return TmDBMovieSession(apy_key, language)
    elif _parse_media(media_type.lower()) == Media.tv:
        return TmDBTvSession(apy_key, language)
    else:
        raise TmDBSessionException(f'media {media_type} unknown')


if __name__ == '__main__':
    k = '142b8d3c9048ff091ada7cd22ca6dff0'
    s = session_factory('tv', k)
    title = 'Girls'
    # shows = s.search_show(title, exact=True)
    #shows = s.search_show('swamp thing', exact=True)
    # print('\n'.join([str(show) for show in shows]))
    supergirl = 62688
    # show = s.get_show(supergirl)
    show, seasons = s.get_show_and_seasons(supergirl)
    print("Done")
