# entities.py

from abc import ABC, abstractmethod, abstractclassmethod
import datetime
import enum
from typing import List, Union, Any, ClassVar, Tuple


__doc__ = """Objects used by the TMDB API Wrapper"""


class Gender(enum.Enum):
    """Performer gender"""
    male = 2
    female = 1
    undefined = 0
    unknown = -1

    @classmethod
    def parse(cls, value: Union[int, str]) -> "Gender":
        """Parse a number and return the corrispondent enumeration"""
        value = int(value)
        if value == 1:
            return Gender.female
        elif value == 2:
            return Gender.male
        elif value == 0:
            return Gender.undefined
        else:
            return Gender.unknown


class Entity(ABC):
    """Represents a generic entity related to Movies, TV Shows, People etc."""
    date_fmt = '%Y-%m-%d'

    def __init__(self, results: dict):
        """Set the json data from the api result"""
        self._results = results

    def _get_value(self, key: str,
                   default: Union[Any] = None) -> Any:
        """Get the value of `key` if in `self._results`.

        Convenience method to access the results.

        :param key: a key that has to be present in the data results from API
        :param default: returned value if `key` is not present (default None)
        """
        return self._results[key] if key in self._results else None

    @property
    def id(self):
        """Get unique identifier"""
        return self._get_value('id')

    @property
    def name(self) -> Union[str, None]:
        """Get entity name"""
        return self._get_value('name', '')

    def _vote_avg_cnt(self) -> tuple:
        """Get the vote average and the vote count for the entity.

        Both values **must be present** otherwise will return ~None, None`
        :return:
        """
        if 'vote_average' in self._results and 'vote_count' in self._results:
            return self._get_value('vote_average'), \
                   self._get_value('vote_count')
        return None, None

    def __repr__(self) -> str:
        """Raw representation"""
        return f'<Entity {self._results}>'

    def __str__(self) -> str:
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
        return self._get_value('biography', '')

    @property
    def profile_pic(self) -> str:
        """Get the profile image path"""
        return self._get_value('profile_path')


class Character(Entity):
    """Represents a character"""
    def __init__(self, results):
        Entity.__init__(self, results)
        self._charname = self._get_value('character', '')
        self._gender = Gender.parse(self._get_value('gender', '-1'))

    @property
    def performer(self) -> str:
        return self.name

    @property
    def character(self) -> str:
        return self._charname

    @property
    def gender(self) -> str:
        return self._gender.name

    @classmethod
    def parse(cls, results):
        """Return an instance of a `Character` from the API results"""
        return [Character(result) for result in results]


class TvShowFromSearch(Entity):
    """Represents a TV Show as a result from an API search"""
    def __init__(self, results):
        Entity.__init__(self, results)

    @property
    def popularity(self):
        """Get popularity value"""
        return self._get_value('popularity')

    @property
    def poster(self):
        """Get the poster image path"""
        return self._get_value('poster_path')


class TvShow(TvShowFromSearch):
    """Represents a TV Show """
    def __init__(self, results):
        Entity.__init__(self, results)
        self.seasons = []

    def is_running(self) -> bool:
        """
        :return: `True` is the show is running
        """
        return bool(self._get_value('in_production'))

    @property
    def homepage(self) -> str:
        """Get the show homepage url"""
        return self._get_value('homepage')

    @property
    def tot_seasons(self) -> int:
        """Get the number of seasons"""
        return int(self._get_value('number_of_seasons'))

    @property
    def status(self) -> str:
        """Get the status of the show"""
        return self._get_value('status')

    @property
    def type(self) -> str:
        """Get the type of the show"""
        return self._get_value('type')

    def parse_seasons(self, seasons: list) -> None:
        """
        Parse and append season info for the show
        :param seasons:
        """
        for season in seasons:
            self.seasons.append(Season.parse_season(season))

    def __repr__(self):
        """Raw representation"""
        return f'<TvShow {self.id} - {self.name} ({self.tot_seasons} '\
               f'season{"s" if self.tot_seasons > 1 else ""}), '\
               f'{self.status}>'

    def __str__(self):
        """String representation"""
        return f'{self.id} - {self.name} ({self.tot_seasons} '\
               f'season{"s" if self.tot_seasons > 1 else ""}), '\
               f'{self.status}'


class Season(Entity):
    """Represents a TV Show season"""
    def __init__(self, results: dict):
        Entity.__init__(self, results)
        self.episodes = []

    @property
    def season_number(self) -> int:
        return self._get_value('season_number')

    @property
    def overview(self) -> str:
        return self._get_value('overview')

    @property
    def poster(self) -> str:
        return self._get_value('poster_path')

    @classmethod
    def parse_season(cls, results: dict) -> "Season":
        """
        Return an istance of `Season` with `Episodes` from the API results
        :param results:
        :return: `Season`
        """
        season = Season(results)
        season.episodes = [Episode(result) for result in results['episodes']]
        return season


class Episode(Entity):
    """Represent a TV Show episode"""
    def __init__(self, results):
        Entity.__init__(self, results)
        self._crew = self._get_value('crew')
        self._characters = None
        self._guest_stars = self._get_value('guest_stars')

    @property
    def air_date(self):
        return self._get_value('air_date')

    @property
    def number(self) -> int:
        return self._get_value('episode_number')

    @property
    def season_number(self) -> int:
        return self._get_value('season_number')

    @property
    def vote_avg_cnt(self) -> Tuple[float, int]:
        return self._get_value('vote_average'), self._get_value('vote_count')

    @property
    def overview(self) -> str :
        return self._results.get('overview', '')


class DailyTvPrograms(Entity):
    """Represents a page of programs airing today """

    def __init__(self, results: dict):
        Entity.__init__(self, results)
        self._aired_shows = self._get_value('results', [])

    @property
    def page(self) -> int:
        return self._get_value('page')

    @property
    def total_pages(self) -> int:
        return self._get_value('total_pages')

    @property
    def total_results(self) -> int:
        return int(self._results['total_results']) or 0

    def get_shows(self) -> List[Tuple[int, str]]:
        """Return the shows on air today"""
        return [(show['id'], show['name']) for show in self._aired_shows]


class DailyTvProgramsCollection:
    """Collection of daily programs pages"""
    def __init__(self):
        self._programs_pages = []

    def add_page(self, page):
        self._programs_pages.append(page)

    def get_shows(self):
        retval = list()
        for page in self._programs_pages:
            retval.extend(page.get_shows())
        return retval
