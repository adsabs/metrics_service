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
import glob
from datetime import datetime
from math import sqrt
import itertools
import unittest
import requests
import time
from metrics_service import app
import json
import httpretty
import mock
from metrics_service.models import MetricsModel

current_year = datetime.now().year

# Special cases to be tested:
#
# 1. All records have more citations than the number of records: h and g index
#    should equal the number of records
# 2. None of the records have citations: h and g index should equal 0
# 3. All citations are self-citations: Tori index should equal 0
# 4. None of the records have usage: usage histograms should still be returned
#    with all zero entries
# 5. None of the records have citations: citation histograms should still be
#    returned with all zero entries
# 6. None of the records have refereed citations: citation histograms for
#    refereed citations should be returned with all zero entries
# 7. None of the records have usage or citations: times series should still be
#    returned with all zero entries
# 8. Single bibcode without citations and reads
#
testset = ['1997ZGlGl..33..173H', '1997BoLMe..85..475M',
           '1997BoLMe..85...81M', '2014bbmb.book..243K', '2012opsa.book..253H']

# Import the JSON document with expected results
results_file = "%s/metrics_service/tests/testdata/expected_results" % PROJECT_HOME
with open(results_file) as data_file:
    expected_results = json.load(data_file)


def get_test_data(bibcodes=None, htest=False, no_cits=False, no_refcits=False,
                  no_usage=False, single=False, tori_test=False):
    # 'bibcode'   : if a list with bibcodes is specified, only retrieve data
    #               for these bibcodes
    # 'htest'     : flag for a specific test for the h index: assign very high
    #               artificial number of citations to each paper to test that
    #               the h index will equal the number of records in this case
    # 'no_cits'   : flag for a specific test for the h/g index: make number of
    #               citations equal 0 for each record (h and g should equal 0)
    # 'no_refcits': flag for the special case with no refereed citations
    # 'no_usage'  : flag for specific test of usage histograms: no usage should
    #               result in histograms with zeros
    # 'single'    : flag for special case of single bibcode without reads
    #               and citations
    # 'tori_test' : flag the special case where all citations will be
    #               self-citations
    # We have to keep track of the current year, to get the
    # correct number of entries in the reads and downloads lists
    year = datetime.now().year
    # We will generate 'reads' and 'downloads' of 1 read/download
    # per year, so that we always have Nentries reads/downloads total
    # This is done because the code actually checks if a reads/downloads
    # has the correct length, given the current year (however, the reads
    # /downloads in the stub data never change
    Nentries = year - 1996 + 1
    datafiles = glob.glob("%s/metrics_service//tests/testdata/*.json" % PROJECT_HOME)
    records = []
    if single:
        no_cits = True
        no_usage = True
    for dfile in datafiles:
        with open(dfile) as data_file:
            data = json.load(data_file)
        if bibcodes and data['bibcode'] not in bibcodes:
            continue
        if htest:
            data['citation_num'] = len(datafiles) * 1000
        elif no_cits:
            data['citation_num'] = 0
            data['citations'] = []
            data['refereed_citation_num'] = 0
            data['refereed_citations'] = []
        elif no_refcits:
            data['refereed_citation_num'] = 0
            data['refereed_citations'] = []
        elif tori_test:
            data['citations'] = [data['bibcode']]
            data['refereed_citations'] = [data['bibcode']]
            data['rn_citation_data'] = [
                {'bibcode': data['bibcode'], 'auth_norm':1, 'ref_norm':1}]
        if not no_usage:
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
        else:
            r = MetricsModel(
                id=data['id'],
                bibcode=data['bibcode'],
                refereed=data['refereed'],
                rn_citation_data=data['rn_citation_data'],
                refereed_citation_num=data['refereed_citation_num'],
                citation_num=data['citation_num'],
                citations=data['citations'],
                refereed_citations=data['refereed_citations'],
                author_num=data['author_num'],
            )
        if single and data['bibcode'] == '1997BoLMe..85..475M':
            records.append(r)
        else:
            records.append(r)

    records = sorted(records, key=lambda a: a.citation_num, reverse=True)
    return records

class TestHirschExtreme(TestCase):

    '''Check if h index is the number of records when for all records:
       Ncits > Nrecs'''

    mockdata = get_test_data(bibcodes=testset, htest=True)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_
    
    @mock.patch('metrics_service.models.execute_SQL_query', return_value=mockdata)
    def test_get_h_extreme(self, mock_execute_SQL_query):
        '''Test h index for only records where Ncits > Nrecs:
           h should equal Nrecs'''
        import metrics_service.metrics as m
        indic, indic_ref = m.get_indicators(testset)
        self.assertEqual(indic['h'], len(testset))
        self.assertEqual(indic['g'], len(testset))


class TestHirschNoCits(TestCase):

    '''Check if h index is zero if there are no citations'''

    mockdata = get_test_data(bibcodes=testset, no_cits=True)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=mockdata)
    def test_get_h_nocits(self, mock_execute_SQL_query):
        '''Test h index for only records where Ncits > Nrecs:
           h should equal Nrecs'''
        from metrics_service.metrics import get_indicators
        indic, indic_ref = get_indicators(testset)
        self.assertEqual(indic['h'], 0)
        self.assertEqual(indic['g'], 0)


class TestToriExtreme(TestCase):

    '''Check if the Tori is zero if all citations are self-citations'''

    mockdata = get_test_data(bibcodes=testset, tori_test=True)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_
    
    @mock.patch('metrics_service.models.execute_SQL_query', return_value=mockdata)
    def test_get_tori(self, mock_execute_SQL_query):
        '''Test getting Tori when all citations are self-citations'''
        from metrics_service.metrics import get_tori
        tori, tori_ref, riq, riq_ref, d = get_tori(testset, testset)
        self.assertEqual(tori, 0)


class TestNoUsage(TestCase):

    '''Check if we get empty histograms for no usage'''

    mockdata = get_test_data(bibcodes=testset, no_usage=True)    

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_
    
    @mock.patch('metrics_service.models.execute_SQL_query', return_value=mockdata)
    def test_no_usage(self, mock_execute_SQL_query):
        '''Test getting usage histograms when there is no usage'''
        from metrics_service.metrics import get_usage_histograms
        # Expected histogram (for all)
        expected = {year: 0 for year in range(1996, current_year + 1)}
        # Get the reads histograms
        hist = get_usage_histograms(testset)
        # and check the results
        histograms = ['all reads', 'refereed reads',
                      'all reads normalized', 'refereed reads normalized']
        for histogram in histograms:
            self.assertEqual(hist[histogram], expected)
        # and do the same for downloads
        hist = get_usage_histograms(testset, usage_type='downloads')
        histograms = ['all downloads',
                      'refereed downloads',
                      'all downloads normalized',
                      'refereed downloads normalized']
        for histogram in histograms:
            self.assertEqual(hist[histogram], expected)


class TestNoCitations(TestCase):

    '''Check if we get empty histograms for no citations'''

    mockdata = get_test_data(bibcodes=testset, no_cits=True)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_
    
    @mock.patch('metrics_service.models.execute_SQL_query', return_value=mockdata)
    def test_no_citations(self, mock_execute_SQL_query):
        '''Test getting citation histograms when there are no citations'''
        from metrics_service.metrics import get_citation_histograms
        years = [int(b[:4]) for b in testset]
        # Expected histogram (for all)
        expected = {year: 0 for year in range(min(years), current_year + 1)}
        # Get the reads histograms
        hist = get_citation_histograms(testset)
        histograms = ['refereed to refereed',
                      'refereed to nonrefereed',
                      'nonrefereed to refereed',
                      'nonrefereed to nonrefereed',
                      'refereed to refereed normalized',
                      'refereed to nonrefereed normalized',
                      'nonrefereed to refereed normalized',
                      'nonrefereed to nonrefereed normalized']
        for histogram in histograms:
            self.assertEqual(hist[histogram], expected)


class TestNoRefereedCitations(TestCase):

    '''Check if we get empty refereed histograms for no refereed citations'''

    mockdata = get_test_data(bibcodes=testset, no_refcits=True)
    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=mockdata)
    def test_no_refereed_citations(self, mock_execute_SQL_query):
        '''Test getting citation histograms when no refereed citations'''
        from metrics_service.metrics import get_citation_histograms
        years = [int(b[:4]) for b in testset]
        # Expected histogram (for all)
        expected = {year: 0 for year in range(min(years), current_year + 1)}
        # Get the reads histograms
        hist = get_citation_histograms(testset)
        histograms = ['refereed to refereed',
                      'refereed to nonrefereed',
                      'refereed to refereed normalized',
                      'refereed to nonrefereed normalized']
        for histogram in histograms:
            self.assertEqual(hist[histogram], expected)


class TestNoTimeSeries(TestCase):

    '''Check if we get empty time series for no usage and citations'''

    mockdata = get_test_data(bibcodes=testset, no_cits=True, no_usage=True)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=mockdata)
    def test_no_refereed_citations(self, mock_execute_SQL_query):
        '''Test getting time series when there is no usage and no citations'''
        from metrics_service.metrics import get_time_series
        years = [int(b[:4]) for b in testset]
        # Expected histogram (for all)
        expected = {year: 0 for year in range(min(years), current_year + 1)}
        # Get the reads histograms
        ts = get_time_series(testset, testset)
        print "XXX"
        print ts
        indicators = ['h', 'g', 'i10', 'i100', 'read10']
        for indicator in indicators:
            self.assertEqual(ts[indicator], expected)


class TestMetricsSingleBibcodeNoUsageCitations(TestCase):

    '''Check single bibcode without usage and citations'''

    mockdata = get_test_data(bibcodes=testset, single=True)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=mockdata)
    def test_get_metrics_single_invalid_bibcode(self, mock_execute_SQL_query):
        '''Test getting data for a single bibcode without
           usage and citations'''
        url = url_for('pubmetrics', bibcode='1997BoLMe..85..475M')
        r = self.client.get(url)
        # The response should have a status code 200
        self.assertTrue(r.status_code == 200)
        # Expected histogram (for all)
        expected = {str(year): 0 for year in range(1997, current_year + 1)}
        # Get the citations histograms
        hist = r.json['histograms']['citations']
        histograms = ['refereed to refereed',
                      'refereed to nonrefereed',
                      'nonrefereed to refereed',
                      'nonrefereed to nonrefereed',
                      'refereed to refereed normalized',
                      'refereed to nonrefereed normalized',
                      'nonrefereed to refereed normalized',
                      'nonrefereed to nonrefereed normalized']
        for histogram in histograms:
            self.assertEqual(hist[histogram], expected)
        # Now check the reads histogram
        expected = {str(year): 0 for year in range(1996, current_year + 1)}
        hist = r.json['histograms']['reads']
        histograms = ['all reads', 'refereed reads',
                      'all reads normalized', 'refereed reads normalized']
        for histogram in histograms:
            self.assertEqual(hist[histogram], expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
