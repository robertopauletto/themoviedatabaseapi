# tmdbapi.py

from abc import ABC
from dotenv import load_dotenv
import enum
import json
import os
from pprint import pprint
import requests
import shutil
from typing import Type, ClassVar, Union, Any, Optional, List, Tuple, Generic

import entities as ent

load_dotenv()


__doc__ = """Wrapper to 'The Movie Database APIs"""
__version__ = "0.3"

MOVIE_SESSION_SYNONYM = 'movie film cinema picture'
TVSERIES_SESSION_SYNONYM = 'tv television t.v. tube tele series show'


class Media(enum.Enum):
    """Represents a media"""
    unknown = 0
    movie = 1
    tv = 2


class SearchType(enum.Enum):
    """Various search types"""
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
    if value.lower() in MOVIE_SESSION_SYNONYM:
        return Media.movie
    elif value.lower() in TVSERIES_SESSION_SYNONYM:
        return Media.tv
    return Media.unknown


API_ENDPOINTS = {
    'root': r'https://api.themoviedb.org/3',
    'config': r'/configuration',
    'new_session': r'/authentication/session/new',
    'find': r'/search/{}',  # Generic
    'genres': r'/genre/{}/list',  # Movies or TV
    'person': r'/person/{}',  # Generic
    'item': r'/{}/{}',  # Generic item by id
    'episode': r'/tv/{}/season/{}/episode/{}',  # Tv episode details
    'season': r'/tv/{}/season/{}',  # Tv season
    'airing_today': r'/tv/airing_today'  # Programs of the day
}


def get_endpoint(action: str, params: Union[tuple, Any]) -> Union[str, None]:
    """
    Build the api call endpoint, depending on `media`.

    :param action: action to perform
    :param params: route parameters
    :return: the api endpoint to call
    """
    if action not in API_ENDPOINTS:
        return None
    if not isinstance(params, tuple):
        params = params,  # Make it a tuple
    return f"{API_ENDPOINTS['root']}{API_ENDPOINTS[action].format(*params)}"


# todo: Further implementations needed for sizes


class TmdbImageSizes(ABC):
    """Represents a tmdbapi defined key for image sizing"""
    original: ClassVar['str'] = "original"


class PosterTmdbImageSizes(TmdbImageSizes):
    """Poster images size specs allowed"""
    w92: ClassVar['str'] = "w92"
    w154: ClassVar['str'] = "w154"
    w185: ClassVar['str'] = "w185"
    w342: ClassVar['str'] = "w342"
    w500: ClassVar['str'] = "w500"
    w780: ClassVar['str'] = "w780"


class TmDBSessionException(Exception):
    """Generic custom app execption"""
    pass


class TmDBSession(ABC):
    """Manage info via themoviedb API"""
    def __init__(self, api_key: str, language=None, media=Media.unknown):
        """
        :param api_key: the secret key
        :param language: language used (may lack some translations, depending
                         on language - defaults to en-US)
        :param media: the actual media will be set in the subclasses
        """
        self._api_key = api_key
        self._lang = language or 'en-US'
        self._media = media
        self._genres = []  # todo: makeit a class method or an esternal ref

    @property
    def genres(self) -> list:
        """Get genres"""
        if not self._genres:
            self._get_genres()
        return self._genres

    @property
    def language(self) -> str:
        """Get the language"""
        return self._lang

    @language.setter
    def language(self, value) -> None:
        """Set the language.

        :param value:
        """
        self._lang = value

    def get_payload(self) -> dict:
        """Gets the payload with the api key and language.

        The caller will extend the dict with the parameters required
        by the specific api call
        """
        payload = {'api_key': self._api_key, 'language': self._lang}
        return payload

    @classmethod
    def _call_endpoint(cls, endpoint: str, payload: dict) -> dict:
        response = requests.get(endpoint, payload)
        if response.status_code == 200:
            return {
                "status": "ok",
                **response.json(),
            }
        return {
            "status": "ko",
            "error": f"{response.status_code} - {response.reason}",
        }

    def search(self, query: str, search_type: SearchType) -> dict:
        """ Generic search.

        :param query:
        :param search_type:
        :return: the results as json
        """
        route = get_endpoint('find', search_type.name)
        payload = self.get_payload()
        payload['query'] = query
        return TmDBTvSession._call_endpoint(route, payload)

    def get_item(self, id, search_type: SearchType):
        route = get_endpoint('item', (search_type.name, id))
        payload = self.get_payload()
        return TmDBTvSession._call_endpoint(route, payload)

    def _get_genres(self):
        """Get a list of genres in the form of id, name"""
        route = get_endpoint('genres', self._media.name)
        payload = self.get_payload()
        result = TmDBTvSession._call_endpoint(route, payload)
        # self._genres = []
        if result["status"] != "ok":
            return
        for genre in result['genres']:
            self._genres.append((genre['id'], genre['name']))


class TmDBMovieSession(TmDBSession):
    """Session for movies"""
    # todo: To implement
    def __init__(self, api_key, language=None):
        TmDBSession.__init__(self, api_key, language, Media.movie)


class TmDBTvSession(TmDBSession):
    """Session for tv series"""
    def __init__(self, api_key: str, language: Union[str, None] = None):
        TmDBSession.__init__(self, api_key, language, Media.tv)

    def get_season(self, show_id: int, season_no: int):
        route = get_endpoint('season', (show_id, season_no))
        payload = self.get_payload()
        return TmDBTvSession._call_endpoint(route, payload)

    def search_show(self, showname: str,
                    exact=False) -> List[ent.TvShowFromSearch]:
        """Search by name of the show.

        :param showname: the pattern to find
        :param exact: if `True` returns the show matching the pattern exactly
        :return: a list of `TvShowFromSearch` instances
        """
        resp = self.search(showname, SearchType.tv)
        if not resp['status'] == 'ok':
            raise TmDBSessionException(
                f"Operation failed:\n {resp['error']}"
            )
        shows = [ent.TvShowFromSearch(show) for show in resp['results']]
        if exact:
            return [show for show in shows
                    if show.name.lower() == showname.lower()]
        return shows

    def get_show(self, show_id: int) -> ent.TvShow:
        """Get info for a show by show ie
        :param show_id:
        :return: TvShow instance 
        """
        return ent.TvShow(self.get_item(show_id, SearchType.tv))

    def get_show_and_seasons(self, show_id: int) -> Tuple[ent.TvShow,
                                                          List[ent.Season]]:
        """Get info for a show by his id with all the seasons.

        Convenience method
        
        :param show_id:
        :return: A TvShow instance with list of Season instances
        """
        seasons = []
        show = self.get_show(show_id)
        for season_no in range(0, show.tot_seasons):
            season = self.get_season(show.id, season_no+1)
            seasons.append(ent.Season.parse_season(season))
        return show, seasons

    def get_show_seasons_and_episodes(self, show_id: int) -> tuple:
        """Gget info for a show by his id with all the seaason end episodes

        :param show_id:
        :return: A TvShow and a list of Season with a list of
                 Episodes insances
        """
        pass  # TODO:

    def airing_today(self) -> ent.DailyTvPrograms:
        route = get_endpoint('airing_today', None)
        payload = self.get_payload()
        payload['language'] = self.language
        resp = requests.get(route, payload)
        page_coll = ent.DailyTvProgramsCollection()
        at = ent.DailyTvPrograms(resp.json())
        page_coll.add_page(at)
        for i in range(2, at.total_pages + 1):
            if i > at.total_pages:  # unlikely but protects from 1 page results
                break
            payload['page'] = i
            resp = requests.get(route, payload)
            page_coll.add_page(ent.DailyTvPrograms(resp.json()))
        return page_coll


class Configuration:
    """Some generic info needed for image managing"""
    def __init__(self):
        self.img_base_url = None
        self.img_secure_base_url = None
        self.img_backdrop_sizes = []
        self.img_logo_sizes = []
        self.img_poster_sizes = []
        self.img_profile_sizes = []
        self.img_still_sizes = []
        self.change_keys = []

    @classmethod
    def getconfig(cls, session: TmDBSession) -> Any:
        """Get a configuration params for the api for a session"""
        conf = Configuration()
        route = get_endpoint('config', None)
        payload = session.get_payload()
        resp = get_endpoint(route, payload)
        if resp['status'] == 'ok':
            conf.img_base_url = resp['images']['base_url']
            conf.img_secure_base_url = resp['images']['secure_base_url']
            conf.img_backdrop_sizes = resp['images']['backdrop_sizes']
            conf.img_logo_sizes = resp['images']['logo_sizes']
            conf.img_poster_sizes = resp['images']['poster_sizes']
            conf.img_profile_sizes = resp['images']['profile_sizes']
            conf.img_still_sizes = resp['images']['still_sizes']
            conf.change_keys = resp['change_keys']
        return conf


def session_factory(media_type: str, apy_key: str,
                    lang=None) -> Union[TmDBTvSession, TmDBMovieSession]:
    """
    Get a TMDBSession, raises a `TmDBSessionException` if `media_type` is not
    a known key, you can pass  'movies, films, cinema' or
    'tv, television, t.v., tube, tele'

    :param media_type: media to query (tv or movie)
    :param apy_key: the secret TMDB api key
    :param lang: localization value (ed. it for Italian, fr for French ...
    :return: the approriate `TMDBSession` object
    """
    if _parse_media(media_type.lower()) == Media.movie:
        return TmDBMovieSession(apy_key, lang)
    elif _parse_media(media_type.lower()) == Media.tv:
        return TmDBTvSession(apy_key, lang)
    else:
        raise   TmDBSessionException(f'media {media_type} unknown')


def _get_image(conf: Configuration, img_name: str, size: str, local_path: str,
               local_filename: str, secure: bool = True) -> None:
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
    # todo: write the local file
    if r.status_code == 200:
        with open(os.path.join(local_path, local_filename), 'wb') as fh:
            for chunk in r.iter_content(1024):
                fh.write(chunk)


def get_image(apikey: str, show_id: int, local_folder: str,
              local_filename: str):
    """
    Download a series poster for the `show_id` into
    `local_folder\\local_filename`

    :param apikey:
    :param show_id:
    :param local_folder:
    :param local_filename:
    :return:
    """
    session = session_factory('tv', apikey)
    conf = Configuration.getconfig(session)
    show = session.get_show(show_id)
    _get_image(conf, show.poster, PosterTmdbImageSizes.original, local_folder,
               local_filename)
