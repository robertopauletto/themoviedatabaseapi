# tmdbapi.py

import enum
import json
import os
from pprint import pprint
import requests
import shutil
from typing import Type, ClassVar
import tmdbRest.entities as ent
import tmdbRest.genres as generi

__doc__ = """tmdbapi.py"""
__version__ = "0.1"
__changelog__ = """

"""

k = '142b8d3c9048ff091ada7cd22ca6dff0'


class Media(enum.Enum):
    """Represent a media"""
    unknown = 0
    movie = 1
    tv = 2


class SearchType(enum.Enum):
    """Search types"""
    company = 0
    collection = 1
    keyword = 2
    movie = 3
    multi = 4
    person = 5
    tv = 6


def _parse_media(value: str) -> Media:
    """
    Detect media type by keywords
    :param value:
    :return:
    """
    if value.lower() in 'movies films cinema':
        return Media.movie
    elif value.lower() in 'tv television t.v. tube tele':
        return Media.tv
    return Media.unknown


ROUTES = {
    'root': r'https://api.themoviedb.org/3/',
    'config': r'configuration',
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
    :return:the call to tmdb
    """
    if action not in ROUTES:
        return None
    if not isinstance(params, tuple):
        params = params,
    # print()
    return f"{ROUTES['root']}{ROUTES[action].format(*params)}"



class _Sizes:
    original: ClassVar['str'] = "original"


class PosterSizes(_Sizes):
    w92: ClassVar['str'] = "w92"
    w154: ClassVar['str'] = "w154"
    w185: ClassVar['str'] = "w185"
    w342: ClassVar['str'] = "w342"
    w500: ClassVar['str'] = "w500"
    w780: ClassVar['str'] = "w780"


class Configuration:
    """Site wide infos"""
    def __init__(self):
        self.img_base_url = None
        self.img_secure_base_url = None
        self.img_backdrop_sizes = list()
        self.img_logo_sizes = list()
        self.img_poster_sizes = list()
        self.img_profile_sizes = list()
        self.img_still_sizes = list()
        self.change_keys = list()

    @staticmethod
    def getconfig(session):
        conf = Configuration()
        route = _get_route('config', None)
        payload = session._get_payload()
        resp = requests.get(route, payload).json()
        conf.img_base_url = resp['images']['base_url']
        conf.img_secure_base_url = resp['images']['secure_base_url']
        conf.img_backdrop_sizes = resp['images']['backdrop_sizes']
        conf.img_logo_sizes = resp['images']['logo_sizes']
        conf.img_poster_sizes = resp['images']['poster_sizes']
        conf.img_profile_sizes = resp['images']['profile_sizes']
        conf.img_still_sizes = resp['images']['still_sizes']
        conf.change_keys = resp['change_keys']
        return conf


class TmDBSessionException(Exception):
    """Generic custom app execption"""
    pass


class TmDBSession:
    """Manage info via themoviedb API"""
    def __init__(self, api_key: str, language=None, media=Media.unknown):
        """
        :param api_key: the secret key
        :param language: language used (may lack some translations, dependeing
                         on language - defaults to en-US)
        :param media: the actual media will be set in the subclasses
        """
        self._api_key = api_key
        self._lang = language or 'en-US'
        self._media = media
        self._genres = list()

    @property
    def genres(self):
        if not self._genres:
            return self._get_genres()
        return self._genres

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

    def search(self, query, search_type: SearchType) -> dict:
        """
        Generic search
        :param query:
        :param search_type:
        :return:
        """
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

    def _get_genres(self):
        """Get a list of genres in the form of id, name"""
        route = _get_route('genres', self._media.name)
        payload = self._get_payload()
        resp = requests.get(route, payload)
        self._genres = list()
        for genre in resp.json()['genres']:
            self._genres.append((genre['id'], genre['name']))


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
        if 'success' in resp and not resp['success']:
            raise TmDBSessionException(
                f"Operation failed:\n"
                f"{resp['status_code']} - {resp['status_message']}"
            )
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
            season = self.get_season(show.id, season_no+1)
            seasons.append(ent.Season.parse_season(season))
        return show, seasons

    def get_show_seasons_and_episodes(self, show_id: int) -> tuple:
        """
        Get info for the show number `show_id`, all the seaason end episodes
        :param show_id:
        :return: A TvShow object and a list of Season objects with a list of
                 Episodes
        """
        pass  # TODO:


def session_factory(media_type: str, apy_key: str,
                    language=None):
    if _parse_media(media_type.lower()) == Media.movie:
        return TmDBMovieSession(apy_key, language)
    elif _parse_media(media_type.lower()) == Media.tv:
        return TmDBTvSession(apy_key, language)
    else:
        raise TmDBSessionException(f'media {media_type} unknown')


def _get_image(conf: Configuration, img_name: str,
              size, local_path: str, local_filename: str, secure: bool = True):
    """
    Download a series poster with `image_name` to `local_path`, naming the file
    `local_filename`, if `local_filename` is `None` the filename will be the
    `img_name'.

    :param conf:
    :param size:
    :param local_path:
    :param local_filename:
    :param secure:
    :return:
    """

    url = f'{conf.img_secure_base_url if secure else conf.img_base_url}' \
          f'{size}/{img_name}'
    r = requests.get(url, stream=True)
    # todo: should be better to return the raw data, let another function
    # todo: write the file
    if r.status_code == 200:
        with open(os.path.join(local_path, local_filename), 'wb') as fh:
            for chunk in r.iter_content(1024):
                fh.write(chunk)


def get_image(show_id, local_folder, local_filename):
    s = session_factory('tv', k)
    c = Configuration.getconfig(s)
    show = s.get_show(show_id)
    _get_image(c, show.poster, PosterSizes.original, local_folder,
               local_filename)


if __name__ == '__main__':
    # k = os.environ.get('TMDB_API_KEY', 'secret')
    print(k)
    s = session_factory('tv', k)
    # title = 'Grimm'
    # shows = s.search_show(title, exact=True)
    # shows = s.search_show('swamp thing', exact=True)
    # print('\n'.join([str(show) for show in shows]))
    supergirl = 62688
    c = Configuration.getconfig(s)
    show = s.get_show(supergirl)
    get_image(c, show.poster, PosterSizes.original, '.', 'supergirl.jpg')
    print("")

    # show, seasons = s.get_show_and_seasons(supergirl)
    # for season in seasons:
    #     print(f'Season {season.season_number} '
    #           f'({len(season.episodes):02} episodes)')
    #     for episode in season.episodes:
    #         print(f'\t{episode.number:02} - {episode.name}')
