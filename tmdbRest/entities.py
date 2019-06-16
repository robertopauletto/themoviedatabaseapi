# entities.py

import datetime


__doc__ = """entities.py"""
__version__ = "0.1"
__changelog__ = """

"""


class Entity:
    """Represent a generic entity related to Movies, TV Shows, People etc."""
    date_fmt = '%Y-%m-%d'

    def __init__(self, results: dict):
        """Set the json from the api result"""
        self._results = results

    @property
    def id(self):
        """Generid unique identifier"""
        return self._results.get('id', None)

    @property
    def name(self):
        """Entity name"""
        return self._results.get('name', '')

    def _get_value(self, key: str):
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

    def __repr__(self):
        """String representation"""
        return f'{self.id} - {self.name}'


class Configuration(Entity):
    """Contains common support data for all entities"""
    def __init__(self, results):
        Entity.__init__(self, results)
        self.profile_sizes = self._results['images']['profile_sizes']
        self.poster_sizes = self._results['images']['poster_sizes']
        self.still_sizes = self._results['images']['still_sizes']

    @property
    def img_base_url(self):
        """Base url for an image"""
        return self._results['images']['base_url']

    def profile_img_path(self, size: str):
        """Get the profile image path

        :param size: a valid size contained in `profile_sizes`
        :return:
        """
        if not size or size not in self.profile_sizes:
            size = 'original'
        return f'{self.img_base_url}{size}/'

    def poster_img_path(self, size: str):
        """Get the poster image path

        :param size: a valid size contained in `profile_sizes`
        :return:
        """
        if not size or size not in self.poster_sizes:
            size = 'original'
        return f'{self.img_base_url}{size}/'

    def still_img_path(self, size: str):
        """Get the poster image path

        :param size: a valid size contained in `profile_sizes`
        :return:
        """
        if not size or size not in self.still_sizes:
            size = 'original'
        return f'{self.img_base_url}{size}/'


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


class TvShowFromSearch(Entity):
    """Represent a TV Show as a result from a search"""
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
    """Represent a TV Show """
    def __init__(self, results):
        Entity.__init__(self, results)
        self.seasons = list()

    def is_in_production(self):
        """
        :return: `True` is the show is running
        """
        return self._get_value('in_production')

    @property
    def homepage(self):
        """Show homepage url"""
        return self._get_value('homepage')

    @property
    def tot_seasons(self):
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
    """Represent a TV Show season"""
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


class Episode(Season):
    """Represent a TV Show episode"""
    def __init__(self, results):
        Entity.__init__(self, results)

    @property
    def number(self) -> int:
        return self._results['number']

    @property
    def vote_avg_cnt(self) -> tuple:
        return self._results['vote_average'], self._results['vote_count']


if __name__ == '__main__':
    pass