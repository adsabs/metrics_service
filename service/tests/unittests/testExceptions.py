import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask.ext.testing import TestCase
from flask import request
from flask import url_for, Flask
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects import postgresql
import glob
from datetime import datetime
from math import sqrt
import itertools
import unittest
import requests
import time
import app
import json
import httpretty
import mock
from utils.database import db, Bind, MetricsModel

testset = ['1997ZGlGl..33..173H', '1997BoLMe..85..475M',
           '1997BoLMe..85...81M', '2014bbmb.book..243K', '2012opsa.book..253H']

# Import the JSON document with expected results
results_file = "%s/tests/unittests/testdata/expected_results" % PROJECT_HOME
with open(results_file) as data_file:
    expected_results = json.load(data_file)

# The mockdata to be returned by the Solr mock, which is supposed
# to return just the bibcodes for our test set
mockdata = [
    {'id': '1', 'bibcode': '1997ZGlGl..33..173H'},
    {'id': '2', 'bibcode': '1997BoLMe..85..475M'},
    {'id': '3', 'bibcode': '1997BoLMe..85...81M'},
    {'id': '4', 'bibcode': '2014bbmb.book..243K'},
    {'id': '5', 'bibcode': '2012opsa.book..253H', }
]


def get_test_data(bibcodes=None):
    # We have to keep track of the current year, to get the
    # correct number of entries in the reads and downloads lists
    year = datetime.now().year
    # We will generate 'reads' and 'downloads' of 1 read/download
    # per year, so that we always have Nentries reads/downloads total
    # This is done because the code actually checks if a reads/downloads
    # has the correct length, given the current year (however, the reads
    # /downloads in the stub data never change
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
    records = sorted(records, key=lambda a: a.citation_num, reverse=True)
    return records

# INTERNAL EXCEPTIONS
#
# exceptions generated by calling method with conflicting data
#


class TestUnknownMetricsType(TestCase):

    '''Check exception when requesting unknown metrics type'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = get_test_data(bibcodes=testset)
        mtr.return_value = get_test_data(bibcodes=testset)
        return app_

    def test_get_unknown_metrics_type(self):
        '''When no metrics types are specified an exception is thrown'''
        from utils.metrics import generate_metrics

        res = generate_metrics(bibcodes=testset, metrics_types=[])
        # An unknown metrics type should return an empty dictionary
        self.assertEqual(res, {})


class TestNoIdentiersFound(TestCase):

    '''Check exception when no identifiers are found'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = []
        mtr.return_value = []
        return app_

    def test_no_identifiers_found(self):
        '''When no identifiers are found an exception is thrown'''
        from utils.metrics import generate_metrics

        res = generate_metrics(bibcodes=testset, metrics_types=[])
        # No identifiers (i.e. no records found in database) should return
        # an empty dictionary
        self.assertEqual(res, {})


class TestNoRecordInfoFound(TestCase):

    '''Check exception when no record info is found'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = []
        mtr.return_value = []
        return app_

    def test_illegal_retrieval_method(self):
        '''No record info is found when an unsupported retrieval method
           is specified'''
        from utils.metrics import get_record_info
        data = get_record_info(other="foo")
        expected = {'Status Code': 200,
                    'Error Info': 'Unsupported metrics request',
                    'Error': 'Unable to get results!'}
        self.assertEqual(data, expected)

    @httpretty.activate
    def test_solr_failure(self):
        '''No record info is found because Solr failed to return results'''
        from utils.metrics import get_record_info
        httpretty.register_uri(
            httpretty.GET, self.app.config.get('METRICS_SOLRQUERY_URL'),
            content_type='application/json',
            status=500,
            body="""{
            "responseHeader":{
            "status":0, "QTime":0,
            "params":{ "fl":"bibcode", "indent":"true", "wt":"json", "q":"*"}},
            "response":{"numFound":0,"start":0,"docs":[]
            }}""")
        data = get_record_info(bibcodes=None, query="foo")
        self.assertTrue(data['Status Code'] == 500)
        self.assertTrue('Error' in data)

# EXTERNAL EXCEPTIONS
#
# exceptions generated by calling the endpoint with problematic data
#


class TestBadRequests(TestCase):

    '''Tests that no or too many submitted bibcodes result in the
       proper responses'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    def testEmptyBibcodeListSubmitted(self):
        '''When an empty list of bibcodes is submitted an error should
           be returned'''
        r = self.client.post(
            url_for('metrics.metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': []}))
        self.assertTrue(r.status_code == 200)
        self.assertTrue('Error' in r.json)
        self.assertTrue(r.json.get('Error') == 'Unable to get results!')

    def testTooManyBibcodes(self):
        '''When more than the maximum input bibcodes are submitted an error
           should be returned'''
        bibcodes = ["bibcode"] * \
            (self.app.config.get('METRICS_MAX_SUBMITTED') + 1)
        r = self.client.post(
            url_for('metrics.metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': bibcodes}))
        self.assertTrue(r.status_code == 200)
        self.assertTrue('Error' in r.json)
        self.assertTrue(r.json.get('Error') == 'Unable to get results!')

    def testNothingSubmitted(self):
        '''When no bibcodes nor a query is submitted an error should
           be returned'''
        r = self.client.post(
            url_for('metrics.metrics'),
            content_type='application/json',
            data=json.dumps({}))
        self.assertTrue(r.status_code == 200)
        self.assertTrue('Error' in r.json)
        self.assertTrue(r.json.get('Error') == 'Unable to get results!')


class TestMetricsSingleInvalidBibcode(TestCase):

    '''Check getting exception for a single bibcode'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        db.session = mock.Mock()
        db.metrics = mock.Mock()
        exe = db.session.execute
        mtr = db.metrics.execute
        exe.return_value = []
        mtr.return_value = []
        return app_

    def test_get_metrics_single_invalid_bibcode(self):
        '''Test getting exception for a single bibcode'''
        url = url_for('metrics.pubmetrics', bibcode='foo')
        r = self.client.get(url)
        # The response should have a status code 200
        self.assertTrue(r.status_code == 200)
        self.assertTrue('Error' in r.json)
        self.assertTrue(r.json.get('Error') == 'Unable to get results!')

if __name__ == '__main__':
    unittest.main(verbosity=2)
