import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask_testing import TestCase
from flask import request
from flask import url_for, Flask
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects import postgresql
from datetime import datetime
import glob
import unittest
import requests
import time
import app
import json
import httpretty
import mock
from models import db, Bind, MetricsModel

testset = ['1997ZGlGl..33..173H', '1997BoLMe..85..475M',
           '1997BoLMe..85...81M', '2014bbmb.book..243K', '2012opsa.book..253H']


def get_test_data(bibcodes=None):
    # We have to keep track of the current year, to get the
    # correct number of entries in the reads and downloads lists
    year = datetime.now().year
    # We will generate 'reads' and 'downloads' of 1 read/download
    # per year, so that we always have Nentries reads/downloads total
    Nentries = year - 1996 + 1
    datafiles = glob.glob("%s/tests/unittests/testdata/*.json" % PROJECT_HOME)
    records = []
    for dfile in datafiles:
        with open(dfile) as data_file:
            data = json.load(data_file)
        if bibcodes and data['bibcode'] not in bibcodes:
            continue
        r = MetricsModel(
            id=data['id'],
            bibcode=data['bibcode'],
            refereed=data['refereed'],
            rn_citation_data=data['rn_citation_data'],
            downloads=[1] * Nentries,
            reads=[1] * Nentries,
            refereed_citation_num=data['refereed_citation_num'],
            citation_num=data['citation_num'],
            citations=data['citations'],
            refereed_citations=data['refereed_citations'],
            author_num=data['author_num'],
        )
        records.append(r)
    return records


class TestConfig(TestCase):

    '''Check if config has necessary entries'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    def test_config_values(self):
        '''Check if all required config variables are there'''
        required = ["METRICS_MAX_SUBMITTED", "METRICS_SOLRQUERY_URL",
                    "SQLALCHEMY_BINDS", "DISCOVERER_PUBLISH_ENDPOINT",
                    "DISCOVERER_SELF_PUBLISH", "METRICS_MAX_SIMPLE"]

        missing = [x for x in required if x not in self.app.config.keys()]
        self.assertTrue(len(missing) == 0)
        # Check if API has an actual value if we have a 'local_config.py'
        # (not available when testing with Travis)
        if os.path.exists("%s/local_config.py" % PROJECT_HOME):
            self.assertTrue(
                self.app.config.get('METRICS_API_TOKEN', None) != None)


class TestMetricsModel(TestCase):

    '''Check if the MetricsModel is what we expect it to be'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    def test_metrics_model(self):
        '''Test the guts of the metrics model'''
        mc = [Column(Integer), # id
              Column(String),  # bibcode
              Column(postgresql.REAL), # an_citations
              Column(postgresql.REAL), # an_refereed_citations
              Column(Integer), # author_num
              Column(postgresql.ARRAY(String)), # citations
              Column(Integer), # citation_num
              Column(postgresql.ARRAY(Integer)), # downloads
              Column(postgresql.ARRAY(Integer)), # reads
              Column(Boolean), # refereed
              Column(postgresql.ARRAY(String)), # refereed_citations
              Column(Integer), # refereed_citation_num
              Column(Integer), # reference_num
              Column(postgresql.REAL), # rn_citations
              Column(postgresql.JSON), # rn_citation_data
              Column(DateTime)] # modtime

        expected = map(type, [x.type for x in mc])
        self.assertEqual([type(c.type)
                          for c in MetricsModel.__table__.columns], expected)


class TestHelperFunctions(TestCase):

    '''Check if the helper functions return expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        exe = db.session.execute
        exe.return_value = get_test_data()
        return app_

    def test_mock_query(self):
        '''Check that session mock behaves the way we set it up'''
        expected_attribs = ['_sa_instance_state', 'author_num', 'bibcode',
                            'citation_num', 'citations', 'downloads', 'id',
                            'reads', 'refereed', 'refereed_citation_num',
                            'refereed_citations', 'rn_citation_data']
        # Quering the mock should return a list of MetricsModel instances
        resp = db.session.execute()
        self.assertEqual(
            sorted(resp[0].__dict__.keys()), sorted(expected_attribs))
        self.assertEqual(
            list(set([x.__class__.__name__ for x in resp])), ['MetricsModel'])
        self.assertTrue(isinstance(resp, list))

    def test_bind_object(self):
        '''Check that the Bind object is what is expected'''
        b = Bind('metrics')
        self.assertEqual(b.__class__.__name__, 'Bind')
        self.assertEqual('bind' in b.__dict__, True)
        self.assertEqual(b.bind.__class__.__name__, 'Engine')


class TestIDRetrieval(TestCase):

    '''Check if the id retrieval function returns expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data()
        mtr.return_value = get_test_data()
        return app_

    def test_get_identifiers(self):
        '''Test getting the identifiers for a set of bibcodes'''
        from models import get_identifiers
        data = get_identifiers(testset)
        # We are expecting data to be a dictionary with bibcodes as keys
        # and integers as values (don't really care what the actual values are)
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(False not in [len(x) == 3 for x in data])
        self.assertTrue(False not in [isinstance(x[0], unicode) and
                        len(x[0]) == 19 for x in data])
        self.assertTrue(False not in [isinstance(x[1], int) for x in data])
        self.assertTrue(False not in [isinstance(x[2], bool) for x in data])


class TestBasicStatsDataRetrieval(TestCase):

    '''Check if the basic stats data retrieval function returns
       expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data()
        mtr.return_value = get_test_data()
        return app_

    def test_get_basic_stats_data(self):
        '''Test getting basic stats data'''
        from models import get_basic_stats_data
        data = get_basic_stats_data(testset)
        # The most important thing here is to test that it is a list
        # of MetricsModel instances
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])


class TestPublicationDataRetrieval(TestCase):

    '''Check if the publication data retrieval function returns
       expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data()
        mtr.return_value = get_test_data()
        return app_

    def test_get_publication_data(self):
        '''Test getting publication data'''
        from models import get_publication_data
        data = get_publication_data(testset)
        # The most important thing here is to test that it is a list
        # of MetricsModel instances
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])


class TestCitationDataRetrieval(TestCase):

    '''Check if the citation data retrieval function returns
       expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data()
        mtr.return_value = get_test_data()
        return app_

    def test_get_citation_data(self):
        '''Test getting citation data'''
        from models import get_citation_data
        data = get_citation_data(testset)
        # The most important thing here is to test that it is a list
        # of MetricsModel instances
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])


class TestCitationRetrieval(TestCase):

    '''Check if the citation retrieval function returns expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data()
        mtr.return_value = get_test_data()
        return app_

    def test_get_citations(self):
        '''Test getting citations'''
        from models import get_citations
        data = get_citations(testset)
        # The most important thing here is to test that it is a list
        # of MetricsModel instances
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])


class TestIndicatorDataRetrieval(TestCase):

    '''Check if the indicator data retrieval function returns
       expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data()
        mtr.return_value = get_test_data()
        return app_

    def test_get_indicator_data(self):
        '''Test getting indicator data'''
        from models import get_indicator_data
        data = get_indicator_data(testset)
        # The most important thing here is to test that it is a list
        # of MetricsModel instances
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])


class TestUsageDataRetrieval(TestCase):

    '''Check if the usage data retrieval function returns expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data()
        mtr.return_value = get_test_data()
        return app_

    def test_get_usage_data(self):
        '''Test getting usage data'''
        from models import get_usage_data
        data = get_usage_data(testset)
        # The most important thing here is to test that it is a list
        # of MetricsModel instances
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])


class TestToriDataRetrieval(TestCase):

    '''Check if the tori data retrieval function returns expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data()
        mtr.return_value = get_test_data()
        return app_

    def test_get_tori_data(self):
        '''Test getting tori data'''
        from models import get_tori_data
        data = get_tori_data(testset)
        # The most important thing here is to test that it is a list
        # of MetricsModel instances
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])

if __name__ == '__main__':
    unittest.main(verbosity=2)
