# entities.py

import datetime
import enum
from typing import List, Union, Any, ClassVar, Tuple


__doc__ = """Objects used by the TMDB API Wrapper"""
__version__ = "0.1"
__changelog__ = """

"""


class Gender(enum.Enum):
    """Performer gender"""
    male = 2
    female = 1
    undefined = 0
    unknown = -1

    @staticmethod
    def parse(value):
        value = int(value)
        if value == 1:
            return Gender.female
        elif value == 2:
            return Gender.male
        elif value == 0:
            return Gender.undefined
        else:
            return Gender.unknown


class Entity:
    """Represents a generic entity related to Movies, TV Shows, People etc."""
    date_fmt = '%Y-%m-%d'

    def __init__(self, results: dict):
        """Set the json from the api result"""
        self._results = results

    @property
    def id(self):
        """Unique identifier"""
        return self._results.get('id', None)

    @property
    def name(self) -> Union[str, None]:
        """Entity name"""
        return self._results.get('name', '')

    def _get_value(self, key: str) -> Union[str, None]:
        """
        Get the value of `key`
        :param key:
        :return: None if `key` does non exist
        """
        return self._results[key] if key in self._results else None

    def _vote_avg_cnt(self) -> tuple:
        """
        Get the vote average and the vote count for the entity
        :return:
        """
        if 'vote_average' in self._results and 'vote_count' in self._results:
            return self._results['vote_average'], self._results['vote_count']
        return None, None

    def __repr__(self) -> str:
        """String representation"""
        return f'{self.id} - {self.name}'


class Person(Entity):
    """Represent an individual involved in the show biz"""
    def __init__(self, results):
        Entity.__init__(self, results)

    @property
    def dob(self) -> datetime.datetime:
        """Get Date of birth"""
        return datetime.datetime.strptime(Entity.date_fmt)

    @property
    def bio(self) -> str:
        """Get biography"""
        return self._results['biography']

    @property
    def profile_pic(self) -> str:
        """Get the path of the profile image"""
        return self._results['profile_path']


class Character(Entity):
    """Represents a character"""
    def __init__(self, results):
        Entity.__init__(self, results)
        self._charname = results.get('character', '')
        self._gender = Gender.parse(results.get('gender', 0))

    @property
    def performer(self) -> str:
        return self.name

    @property
    def character(self) -> str:
        return self._charname

    @property
    def gender(self) -> str:
        return self._gender.name

    @staticmethod
    def parse(results):
        return [Character(result) for result in results]


class TvShowFromSearch(Entity):
    """Represents a TV Show as a result from a search"""
    def __init__(self, results):
        Entity.__init__(self, results)

    @property
    def popularity(self):
        """Get popularity value"""
        return self._get_value('popularity')

    @property
    def poster(self):
        """Get the poster image path (needs to be combined"""
        return self._get_value('poster_path')


class TvShow(TvShowFromSearch):
    """Represents a TV Show """
    def __init__(self, results):
        Entity.__init__(self, results)
        self.seasons = list()
        # self._characters = (Character.parse(results['guest_stars']))

    def is_in_production(self) -> str:
        """
        :return: `True` is the show is running
        """
        return self._get_value('in_production')

    @property
    def homepage(self) -> str:
        """Show homepage url"""
        return self._get_value('homepage')

    @property
    def tot_seasons(self) :
        """Get the number of seasons"""
        return self._get_value('number_of_seasons')

    @property
    def status(self):
        """Get the status of the show"""
        return self._get_value('status')

    @property
    def type(self):
        """Get the type of the show"""
        return self._get_value('type')

    def parse_seasons(self, seasons: list):
        """
        Parse and append season info for the show
        :param seasons:
        """
        for season in seasons:
            self.seasons.append(Season.parse_season(season))

    def __repr__(self):
        """String representation"""
        return f'{self.id} - {self.name} ({self.tot_seasons} '\
               f'season{"s" if self.tot_seasons > 1 else ""}), '\
               f'{self.status}'


class Season(Entity):
    """Represents a TV Show season"""
    def __init__(self, results: dict):
        Entity.__init__(self, results)
        self.episodes = list()

    @property
    def season_number(self) -> int:
        return self._results['season_number']

    @property
    def overview(self) -> str:
        return self._results['overview']

    @property
    def poster(self):
        return self._results['still_path']

    @staticmethod
    def parse_season(results: dict):
        season = Season(results)
        season.episodes = [Episode(result) for result in results['episodes']]
        return season


class Episode(Entity):
    """Represent a TV Show episode"""
    def __init__(self, results):
        Entity.__init__(self, results)
        self._crew = results['crew']
        self._characters = None
        self._guest_stars = results['guest_stars']

    @property
    def air_date(self):
        return self._results.get('air_date', None)

    @property
    def number(self) -> int:
        return self._results['episode_number']

    @property
    def season_number(self):
        return self._results['season_number']

    @property
    def vote_avg_cnt(self) -> tuple:
        return self._results['vote_average'], self._results['vote_count']

    @property
    def overview(self):
        return self._results.get('overview', '')


class DailyTvPrograms:
    """Represents a page of programs airing today """

    def __init__(self, resp_json: dict):
        self._resp = resp_json
        self.aired_shows = self._resp['results']
        self.page = self._resp['page']
        self._tot_pages = self._resp['total_pages']

    @property
    def total_pages(self):
        return int(self._tot_pages)

    @property
    def total_results(self) -> int:
        return int(self._resp['total_results']) or 0

    def get_shows(self) -> List[Tuple[int, str]]:
        """Return the shows on air today"""
        return [(show['id'], show['name']) for show in self.aired_shows]


class DailyTvProgramsCollection:
    """Collection of daily programs pages"""
    def __init__(self):
        self._programs_pages = list()

    def add_page(self, page):
        self._programs_pages.append(page)

    def get_shows(self):
        retval = list()
        for page in self._programs_pages:
            retval.extend(page.get_shows())
        return retval

if __name__ == '__main__':
    pass
