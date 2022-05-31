from __future__ import print_function
from builtins import map
from builtins import range
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
from datetime import date, datetime
from math import sqrt
import numpy as np
import itertools
import unittest
import requests
import time
from metrics_service import app
import json
import httpretty
import mock
from metrics_service.models import MetricsModel

testset = ['1997ZGlGl..33..173H', '1997BoLMe..85..475M',
           '1997BoLMe..85...81M', '2014bbmb.book..243K', '2012opsa.book..253H']

# Import the JSON document with expected results
results_file = "%s/metrics_service/tests/testdata/expected_results" % PROJECT_HOME
with open(results_file) as data_file:
    expected_results = json.load(data_file)

# The mockdata to be returned by the Solr mock, which is supposed to return
# just the bibcodes for our test set
mockdata = [
    {'id': '1', 'bibcode': '1997ZGlGl..33..173H'},
    {'id': '2', 'bibcode': '1997BoLMe..85..475M'},
    {'id': '3', 'bibcode': '1997BoLMe..85...81M'},
    {'id': '4', 'bibcode': '2014bbmb.book..243K'},
    {'id': '5', 'bibcode': '2012opsa.book..253H', }
]


def get_test_data(bibcodes=None):
    # 'bibcode': if a list with bibcodes is specified, only retrieve data
    #            for these bibcodes
    # We have to keep track of the current year, to get the
    # correct number of entries in the reads and downloads lists
    year = datetime.now().year
    # We will generate 'reads' and 'downloads' of 1 read/download
    # per year, so that we always have Nentries reads/downloads total
    # This is done because the code actually checks if a reads/downloads
    # has the correct length, given the current year (however, the reads
    # /downloads in the stub data never change
    Nentries = year - 1996 + 1
    datafiles = glob.glob("%s/metrics_service/tests/testdata/*.json" % PROJECT_HOME)
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


class TestHelperFunctions(TestCase):

    '''Check if the helper functions return expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    def test_chunks(self):
        '''Test the function that split a list up in a list of lists'''
        from metrics_service.metrics import chunks
        list = ['a', 'b', 'c', 'd']
        expected = [['a'], ['b'], ['c'], ['d']]
        self.assertEqual([x for x in chunks(list, 1)], expected)

    def test_norm_histo(self):
        '''Test the function that converts a list of tuples to a histogram'''
        from metrics_service.metrics import get_norm_histo
        l = [(2000, 1.5), (2000, 1.5), (2001, 1.7)]
        expected = {2000: 3.0, 2001: 1.7}
        self.assertEqual(get_norm_histo(l), expected)

    def test_merge_dictionaries(self):
        '''Test the function that merges two dictionaries'''
        from metrics_service.metrics import merge_dictionaries
        d1 = {1991: 1, 1993: 3}
        d2 = {1990: 0, 1992: 2}
        expected = {1990: 0, 1991: 1, 1992: 2, 1993: 3}
        self.assertEqual(merge_dictionaries(d1, d2), expected)

    def test_encoder(self):
        '''Test if the encoder works properly'''
        from metrics_service.metrics import MyEncoder
        testdata = {'float':np.float64(1.2), 'int':np.int64(3)}
        res = json.loads(json.dumps(testdata, cls=MyEncoder))
        for t in testdata.keys():
            self.assertEqual(type(res[t]).__name__, t)


class TestRecordInfoFunction(TestCase):

    '''Check if the helper functions return expected results'''

    testdata = get_test_data(bibcodes=testset)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_get_record_info_from_bibcodes(self, mock_execute_SQL_query):
        '''Test getting record info when specifying bibcodes'''
        from metrics_service.metrics import get_record_info
        bibs, bibs_ref, IDs, missing = get_record_info(
            bibcodes=testset, query=None)
        # The list of bibcodes returned should be equal to the test set
        self.assertEqual(sorted(map(str, bibs)), sorted(testset))
        # The list IDs should be a list of integers
        self.assertEqual(isinstance(IDs, list), True)
        self.assertTrue(False not in [isinstance(x, int) for x in IDs])
        # The list of skipped bibcodes should be empty
        self.assertEqual(missing, [])
        # If we add a non-existing bibcode to the test set, it should get
        # returned in the 'missing' list
        bibs, bibs_ref, IDs, missing = get_record_info(
            bibcodes=testset + ['foo'], query=None)
        self.assertEqual(missing, ['foo'])

class TestSelfCitationFunction(TestCase):

    '''Check if the expected self-citations are returned'''

    testdata = get_test_data()

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_get_selfcitations(self, mock_execute_SQL_query):
        '''Test getting self-citations'''
        from metrics_service.metrics import get_selfcitations
        data, selfcits, Ns, Ns_r, Nc, Nc_r = get_selfcitations(
            [1, 2, 3], testset)
        # The 'data' returned is upposed to be a list of MetricsModel objects
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])
        # The 'selfcits' returned is supposed to be a list to determine
        # self-citation data it is a list of tuples with a 'set' as first
        # element and a boolean as second
        self.assertTrue(
            False not in [isinstance(x[0], set) and isinstance(x[1], bool) for
                          x in selfcits])
        # Get the actual self-citations
        selfs = list(itertools.chain(*[x[0]
                                       for x in selfcits if len(x[0]) > 0]))
        self.assertEqual(
            sorted(selfs), sorted(expected_results['self-citations']))
        # Now check the number of self-citations
        self.assertEqual(
            Ns, expected_results['citation stats']['number of self-citations'])
        # and the refereed number of self-citations
        er = expected_results['citation stats refereed'][
                              'number of self-citations']
        self.assertEqual(Ns_r, er)
        # Finally there is the number of citing papers
        # Note: this is higher than the actual number for the 'test set'
        # because of the nature of the mock data (the citations of the
        # citations are also in the data)
        self.assertEqual(
            Nc, expected_results['citation stats']['number of citing papers'])
        # and the refereed variant
        self.assertEqual(
            Nc_r, expected_results['citation stats refereed'][
                                   'number of citing papers'])

    @mock.patch('metrics_service.models.execute_SQL_query', return_value='foo')
    def test_get_selfcitations_invalid(self, mock_execute_SQL_query):
        '''Test getting self-citations'''
        from metrics_service.metrics import get_selfcitations
        data, selfcits, Ns, Ns_r, Nc, Nc_r = get_selfcitations(
            [1, 2, 3], testset)
        self.assertEqual(selfcits,[([], False)])

class TestBasicStatsFunction(TestCase):

    '''Check if the expected basic stats are returned'''

    testdata = get_test_data(bibcodes=testset)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_get_basic_stats(self, mock_execute_SQL_query):
        '''Test getting basic stats'''
        from metrics_service.metrics import get_basic_stats
        # We use mock data, so not important that we feed bibcodes instead of
        # IDs
        bs, bsr, data = get_basic_stats(testset)
        # Check the basic stats returned (total)
        # No papers should have been skipped from the test set
        self.assertEqual(bs['number of papers'], len(testset))
        # Check the normalized paper count with the expected value
        self.assertAlmostEqual(bs['normalized paper count'], expected_results[
                               'basic stats']['normalized paper count'])
        # With the reads set up as one per year, the total number of reads
        # should amount to the number of years since 1996 times the number
        # of papers
        Nentries = datetime.now().year - 1996 + 1
        self.assertEqual(bs['total number of reads'], Nentries * len(testset))
        # and for the same reason, the average should equal the number of years
        self.assertEqual(bs['average number of reads'], float(Nentries))
        # which also applies to the median
        self.assertEqual(bs['median number of reads'], float(Nentries))
        # and the same for the downloads statistics
        self.assertEqual(
            bs['total number of downloads'], Nentries * len(testset))
        self.assertEqual(bs['average number of downloads'], float(Nentries))
        self.assertEqual(bs['median number of downloads'], float(Nentries))
        # Check the basic stats for refereed papers
        # The number of refereed papers
        self.assertEqual(bsr['number of papers'], expected_results[
                         'basic stats refereed']['number of papers'])
        # The normalized paper count
        self.assertAlmostEqual(bsr['normalized paper count'], expected_results[
                               'basic stats refereed'][
                               'normalized paper count'])
        # For reads and downloads the same reasoning applies, but now with only
        # the number of refereed papers
        Npapers = expected_results['basic stats refereed']['number of papers']
        self.assertEqual(bsr['total number of reads'], Nentries * Npapers)
        # and for the same reason, the average should equal the number of years
        self.assertEqual(bsr['average number of reads'], float(Nentries))
        # which also applies to the median
        self.assertEqual(bsr['median number of reads'], float(Nentries))
        # and the same for the downloads statistics
        self.assertEqual(bsr['total number of downloads'], Nentries * Npapers)
        self.assertEqual(bsr['average number of downloads'], float(Nentries))
        self.assertEqual(bsr['median number of downloads'], float(Nentries))
        # 'data' is a list of MetricsModel instances for later use
        self.assertEqual(isinstance(data, list), True)
        self.assertTrue(
            False not in [x.__class__.__name__ == 'MetricsModel' for
                          x in data])


class TestCitationStatsFunction(TestCase):

    '''Check if the expected citation stats are returned'''

    testdata = get_test_data(bibcodes=testset)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_get_citation_stats(self, mock_execute_SQL_query):
        '''Test getting citation stats'''
        from metrics_service.metrics import get_citation_stats
        from metrics_service.metrics import get_record_info
        bibs, bibs_ref, IDs, missing = get_record_info(
            bibcodes=testset, query=None)
        # We use mock data, so not important that we feed bibcodes instead of
        # IDs
        cs, csr, data, selfcits, citdata = get_citation_stats(
            testset, testset, bibs_ref)
        # Check the citation stats with expected results
        citation_checks = ['number of citing papers',
                           'total number of citations',
                           'number of self-citations',
                           'total number of refereed citations',
                           'average number of citations',
                           'median number of citations',
                           'normalized number of citations',
                           'average number of refereed citations']
        for check in citation_checks:
            self.assertEqual(
                cs[check], expected_results['citation stats'][check])
        # and the same for the citation stats for refereed papers
        for check in citation_checks:
            self.assertEqual(
                csr[check], expected_results['citation stats refereed'][check])


class TestIndicatorsFunction(TestCase):

    '''Check if the expected indicator values are returned'''

    testdata = get_test_data(bibcodes=testset)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_get_indicators(self, mock_execute_SQL_query):
        '''Test getting indicators'''
        from metrics_service.metrics import get_indicators
        indic, indic_ref = get_indicators(testset)
        # Start comparing the results with computed values
        # Get the year range for comparison of 'm'
        yrange = datetime.now().year - min([int(p[:4]) for p in testset]) + 1
        # Test the indicators for all publications
        indicators = ['h', 'g', 'i10', 'i100']
        for indicator in indicators:
            self.assertEqual(
                indic[indicator], expected_results['indicators'][indicator])
        self.assertEqual(indic['m'], float(indic['h']) / float(yrange))
        # By contruction of the reads data, Read10 follows thusly:
        # there are only two papers published in previous 10 years
        # and their current reads are all 1; one has 3 authors, the other 2
        d0 = date(datetime.now().year, 1, 1)
        d1 = date(datetime.now().year, datetime.now().month, datetime.now().day)
        d2 = date(datetime.now().year, 12, 31)
        delta = (d1 - d0).days + 1
        ndays = (d2 - d0).days + 1
        try:
            r10_corr = float(ndays)/float(delta)
        except:
            r10_corr = 1.0

class TestToriFunction(TestCase):

    '''Check if the expected Tori and riq values are returned'''

    testdata = get_test_data()

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_get_tori(self, mock_execute_SQL_query):
        '''Test getting Tori and riq'''
        from metrics_service.metrics import get_tori
        tori, tori_ref, riq, riq_ref, d = get_tori(testset, testset)
        # First test the total Tori with the computed value
        self.assertAlmostEqual(tori, expected_results['indicators']['tori'])
        # The riq follows from normalizing by date range
        yrange = max([int(p[:4]) for p in testset]) - min([int(p[:4]) for p in testset]) + 1
        self.assertAlmostEqual(riq, int(1000.0 * sqrt(tori) / float(yrange)))
        # Now do the same for the refereed set
        self.assertAlmostEqual(
            tori_ref, expected_results['indicators refereed']['tori'])
        # The riq follows from normalizing by date range
        self.assertAlmostEqual(
            riq_ref, int(1000.0 * sqrt(tori_ref) / float(yrange)))


class TestPublicationHistogram(TestCase):

    '''Check if the expected publication histogram is returned'''

    testdata = get_test_data(bibcodes=testset)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_publication_histograms(self, mock_execute_SQL_query):
        '''Test getting the publication histograms'''
        from metrics_service.metrics import get_publication_histograms

        hist = get_publication_histograms(testset)
        # First the publication histogram for all publications
        # Only compare the non-zero entries (the returned dictionary will
        # differ from year to year, since next year there will be an
        # additional zero)
        histograms = ['all publications',
                      'all publications normalized',
                      'refereed publications',
                      'refereed publications normalized']
        for histogram in histograms:
            # Get the expected values
            expected = expected_results['histograms'][
                'publications'][histogram]
            # Make the key integer again, because JSON turned it into a string
            expected = {int(k): v for k, v in list(expected.items())}
            # Get the non-zero entries for the histogram we just generated
            nonzero = dict(
                [(year, freq) for year, freq in
                 list(hist[histogram].items()) if freq != 0])
            # and compare
            self.assertEqual(nonzero, expected)


class TestUsageHistogram(TestCase):

    '''Check if the expected publication histogram is returned'''

    testdata = get_test_data(bibcodes=testset)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_usage_histograms(self, mock_execute_SQL_query):
        '''Test getting the usage histograms'''
        from metrics_service.metrics import get_usage_histograms
        # First get the 'reads' histograms
        hist = get_usage_histograms(testset)
        # Every entry in the histogram for all papers should, by design,
        # equal the number of papers in the test set, from 1996 up to the
        # current year
        current_year = datetime.now().year
        expected = dict([(year, expected_results['basic stats'][
                        'number of papers']) for year in
                        range(1996, current_year + 1)])
        self.assertEqual(hist['all reads'], expected)
        # and for the same reason, every entry in the histogram for refereed
        # papers should equal the number of refereed papers
        expected = dict([(year, expected_results['basic stats refereed'][
                        'number of papers']) for year in
                        range(1996, current_year + 1)])
        self.assertEqual(hist['refereed reads'], expected)
        # For the normalized histograms, each entry should equal the normalized
        # paper count. Because we're dealing with a dictionary of floats, we do
        # things slightly differently:
        # Check that all entries are equal
        self.assertEqual(len(set(hist['all reads normalized'].values())), 1)
        # and then check that one entry has the expected value
        self.assertAlmostEqual(list(hist['all reads normalized'].values())[0],
                               expected_results['basic stats'][
                               'normalized paper count'])
        # Because the downloads have been constructed in the same way,
        # we only need to verify that the downloads histograms are the
        # same as the reads ones
        dhist = get_usage_histograms(testset, usage_type='downloads')
        self.assertEqual(hist['all reads'], dhist['all downloads'])
        self.assertEqual(hist['refereed reads'], dhist['refereed downloads'])
        self.assertEqual(
            hist['all reads normalized'],
            dhist['all downloads normalized'])
        self.assertEqual(
            hist['refereed reads normalized'],
            dhist['refereed downloads normalized'])


class TestCitationHistogram(TestCase):

    '''Check if the expected citation histogram is returned'''

    testdata = get_test_data(bibcodes=testset)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_citation_histograms(self, mock_execute_SQL_query):
        '''Test getting the citation histograms'''
        from metrics_service.metrics import get_citation_histograms

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
            # Get the expected values
            expected = expected_results['histograms']['citations'][histogram]
            # Make the key integer again, because JSON turned it into a string
            expected = {int(k): v for k, v in list(expected.items())}
            # Get the non-zero entries for the histogram we just generated
            nonzero = dict(
                [(year, freq) for year, freq in
                 list(hist[histogram].items()) if freq != 0])
            # and compare
            self.assertEqual(nonzero, expected)


class TestTimeSeries(TestCase):

    '''Check if the expected time series are returned'''

    testdata = get_test_data(bibcodes=testset)

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @mock.patch('metrics_service.models.execute_SQL_query', return_value=testdata)
    def test_time_series(self, mock_execute_SQL_query):
        '''Test getting the time series'''
        from metrics_service.metrics import get_time_series

        ts = get_time_series(testset, testset)

        # The time series get test over the range of publication years
        years = [int(b[:4]) for b in testset]
        yrange = list(range(min(years), max(years) + 1))
        indicators = ['h', 'g', 'i10', 'i100', 'read10']
        for indicator in indicators:
            print(indicator)
            serie = {y: ts[indicator][y] for y in yrange}
            expected = {
                int(k): v for k, v in
                list(expected_results['time series'][indicator].items())}
            self.assertEqual(serie, expected)
        serie = {y: ts['tori'][y] for y in yrange}
        expected = {
            int(k): v for k, v in
            list(expected_results['time series']['tori'].items())}
        self.assertTrue(
            'False' not in [np.allclose([serie[y]],
                            expected[y]) for y in yrange])

if __name__ == '__main__':
    unittest.main(verbosity=2)
