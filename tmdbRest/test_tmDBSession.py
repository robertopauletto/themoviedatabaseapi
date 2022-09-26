# test_tmDBSession
import os
from unittest import TestCase

from dotenv import load_dotenv

import tmdbRest.tmdbapi as api
import entities as ent


__doc__ = """test_tmDBSession"""


API_KEY = os.environ.get("TMDB_API_KEY", "")


class TestTmDBSession(TestCase):
    def setUp(self):
        self.tv_session = api.TmDBTvSession(API_KEY)

    def testApiKeyFromEnvIsNotEmpty(self):
        self.assertNotEqual(API_KEY, "")

    def testSessionFactoryCallReturnTmDBTvSession(self):
        for word in api.TVSERIES_SESSION_SYNONYM.split():
            self.assertIsInstance(
                api.session_factory(word, API_KEY), api.TmDBTvSession
            )

    def testSessionFactoryCallReturnTmDBMovieSession(self):
        for word in api.MOVIE_SESSION_SYNONYM.split():
            self.assertIsInstance(
                api.session_factory(word, API_KEY), api.TmDBMovieSession
            )

    def testSessionFactoryCallNotRecognized(self):
        self.assertRaises(
            api.TmDBSessionException, api.session_factory, 'foo', API_KEY)

    def testTVSearchShowMany(self):
        shows = self.tv_session.search_show('grimm', False)
        self.assertTrue(len(shows) > 0)

    def testTVSearchShowExact(self):
        shows = self.tv_session.search_show('grimm', True)
        self.assertTrue(len(shows) == 1)

    def testTVSearchShowFailed(self):
        shows = self.tv_session.search_show('adsfasdfdsfddsfsad', True)
        self.assertTrue(len(shows) == 0)

    def testTVGetShowByID(self):
        grimm: ent.TvShowFromSearch = self.tv_session.search_show(
            'grimm', True
        )[0]
        show = self.tv_session.get_show(grimm.id)
        self.assertEqual(show.name, 'Grimm', 'Expected "Grimm"')
        self.assertEqual(show.status, 'Ended', "Expected 'Ended'")
        self.assertEqual(show.tot_seasons, 6, 'Expected 6')

    def testTVGetShowAndSeasonsByID(self):
        grimm: ent.TvShowFromSearch = self.tv_session.search_show(
            'grimm', True
        )[0]
        show, seasons = self.tv_session.get_show_and_seasons(grimm.id)
        self.assertEqual(len(seasons), 6, 'Expected 6')
