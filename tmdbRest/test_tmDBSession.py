# test_tmDBSession
from configparser import ConfigParser
from unittest import TestCase
import tmdbRest.tmdbapi as api


__doc__ = """test_tmDBSession"""
__version__ = "0.1"
__changelog__ = """

"""

ini = ConfigParser()
ini.read('config_test.py')
API_KEY = ini.get('Misc', 'api_key')


class TestTmDBSession(TestCase):
    def setUp(self):
        self.session = api.TmDBSession(API_KEY)



if __name__ == '__main__':
    pass


