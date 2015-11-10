import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask.ext.testing import TestCase
from flask import request
from flask import url_for, Flask
import unittest
import requests
import time
import app
import json
import glob
import httpretty
import mock
from datetime import date, datetime
from models import db, MetricsModel

testset = ['1997ZGlGl..33..173H', '1997BoLMe..85..475M',
           '1997BoLMe..85...81M', '2014bbmb.book..243K', '2012opsa.book..253H']

# Import the JSON document with expected results
results_file = "%s/tests/unittests/testdata/expected_results" % PROJECT_HOME
with open(results_file) as data_file:
    expected_results = json.load(data_file)

# Import the JSON document with expected results
results_file = "%s/tests/unittests/testdata/expected_results" % PROJECT_HOME
with open(results_file) as data_file:
    expected_results = json.load(data_file)

# The mockdata to be returned by the Solr mock, which is supposed to
# return just the bibcodes for our test set
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


class TestBasicStatsBibcodes(TestCase):

    '''Check if the basic stats are returned for valid bibcodes'''

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

    def test_get_basic_stats_bibcodes(self):
        '''Test getting just basic stats when valid bibcodes are submitted'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset, 'types': ['basic']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(r.json.keys(),
                        [u'basic stats', u'skipped bibcodes',
                         u'basic stats refereed'])
        # There should be no skipped bibcodes
        self.assertEqual(r.json['skipped bibcodes'], [])
        bs = r.json['basic stats']
        bsr = r.json['basic stats refereed']
        # Check that the basic stats have the right values
        self.assertEqual(bs['number of papers'], len(testset))
        # Check the normalized paper count with the expected value
        self.assertAlmostEqual(bs['normalized paper count'], expected_results[
                               'basic stats']['normalized paper count'])
        # With the reads set up as one per year, the total number of reads
        # should amount to the number of years since 1996 times the number ofi
        # papers
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
        er = expected_results['basic stats refereed']['normalized paper count']
        self.assertAlmostEqual(bsr['normalized paper count'], er)
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

    def test_get_basic_stats_bibcodes_with_invalid(self):
        '''Test getting just basic stats with an additional invalid bibcode'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset + ['foo'],
                             'types': ['basic']}))
        self.assertTrue(r.status_code == 200)
        # The invalid bibcode should be returned as 'skipped bibcode'
        self.assertEqual(r.json['skipped bibcodes'], ['foo'])


class TestBasicStatsQuery(TestCase):

    '''Check if the basic stats are returned for a valid query'''

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

    @httpretty.activate
    def test_get_basic_stats_query(self):
        '''Test getting just basic stats when a valid query is submitted'''
        httpretty.register_uri(
            httpretty.GET, self.app.config.get('METRICS_SOLRQUERY_URL'),
            content_type='application/json',
            status=200,
            body="""{
            "responseHeader":{
            "status":0, "QTime":0,
            "params":{ "fl":"bibcode", "indent":"true", "wt":"json", "q":"*"}},
            "response":{"numFound":10456930,"start":0,"docs":%s
            }}""" % json.dumps(mockdata))
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'query': 'foo', 'types': ['basic']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(
            r.json.keys(), [u'basic stats',
                            u'skipped bibcodes',
                            u'basic stats refereed'])
        # There should be no skipped bibcodes
        self.assertEqual(r.json['skipped bibcodes'], [])
        # We have already checked in testMetricsFunctions unittests that the
        # correct bibcodes are returned and given to the metrics framework, so
        # the results returned are by definition the same and need not be
        # tested


class TestCitationStatsBibcodes(TestCase):

    '''Check if the citation stats are returned for valid bibcodes'''

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

    def test_get_citation_stats_bibcodes(self):
        '''Test getting just citation stats when valid bibcodes
           are submitted'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset, 'types': ['citations']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(r.json.keys(), [
                        u'citation stats',
                        u'skipped bibcodes',
                        u'citation stats refereed'])
        # There should be no skipped bibcodes
        self.assertEqual(r.json['skipped bibcodes'], [])
        cs = r.json['citation stats']
        csr = r.json['citation stats refereed']
        # Check the data returned
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


class TestIndicatorsBibcodes(TestCase):

    '''Check if the citation stats are returned for valid bibcodes'''

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

    def test_get_indicators_bibcodes(self):
        '''Test getting just the indicators when valid bibcodes
           are submitted'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset, 'types': ['indicators']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(
            r.json.keys(), [u'indicators',
                            u'skipped bibcodes',
                            u'indicators refereed'])
        # There should be no skipped bibcodes
        self.assertEqual(r.json['skipped bibcodes'], [])
        indic = r.json['indicators']
        indic_ref = r.json['indicators refereed']
        # Compare the indicators for all papers
        indicators = ['h', 'g', 'i10', 'i100']
        for indicator in indicators:
            self.assertEqual(
                indic[indicator], expected_results['indicators'][indicator])
        self.assertAlmostEqual(
            indic['tori'], expected_results['indicators']['tori'])
        yrange = datetime.now().year - min([int(p[:4]) for p in testset]) + 1
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
        self.assertAlmostEqual(indic['read10'], r10_corr / float(3) + r10_corr / float(2))
        # Now do the comparison for the refereed values
        # The year range is the same, because the oldest paper is refereed
        for indicator in indicators:
            self.assertEqual(
                indic_ref[indicator],
                expected_results['indicators refereed'][indicator])
        self.assertAlmostEqual(
            indic_ref['tori'], expected_results['indicators refereed']['tori'])
        self.assertEqual(indic_ref['m'], float(indic_ref['h']) / float(yrange))
        # There are no refereed papers in previous 10 years, so Read10 is zero
        self.assertEqual(indic_ref['read10'], 0.0)


class TestPublicationHistogramsBibcodes(TestCase):

    '''Check if the publication histograms are returned for valid bibcodes'''

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

    def test_get_publication_histograms_bibcodes(self):
        '''Test getting just publication histograms when valid bibcodes
           are submitted'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset,
                             'types': ['histograms'],
                             'histograms': ['publications']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(r.json.keys(), [u'histograms', u'skipped bibcodes'])
        self.assertTrue(r.json['histograms'].keys(), ['publications'])
        hist = r.json['histograms']['publications']
        # First the publication histogram for all publications
        # Only compare the non-zero entries (the returned dictionary will
        # differ from year to year, since next year there will be an additional
        # zero)
        histograms = ['all publications',
                      'all publications normalized',
                      'refereed publications',
                      'refereed publications normalized']
        for histogram in histograms:
            # Get the expected values
            expected = expected_results['histograms'][
                'publications'][histogram]
            # Get the non-zero entries for the histogram we just generated
            nonzero = dict(
                [(year, freq) for year, freq in
                 hist[histogram].items() if freq != 0])
            # and compare
            self.assertEqual(nonzero, expected)


class TestUsageHistogramsBibcodes(TestCase):

    '''Check if the usage histograms are returned for valid bibcodes'''

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

    def test_get_reads_histograms_bibcodes(self):
        '''Test getting just usage histograms when valid bibcodes
           are submitted'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset,
                             'types': ['histograms'],
                             'histograms': ['reads']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(r.json.keys(), [u'histograms', u'skipped bibcodes'])
        self.assertTrue(r.json['histograms'].keys(), ['reads'])
        self.assertTrue(
            r.json['histograms']['reads'].keys(),
            ['all reads', 'refereed reads'])
        hist = r.json['histograms']['reads']
        # Every entry in the histogram for all papers should, by design,
        # equal the number of papers in the test set, from 1996 up to the
        # current year
        current_year = datetime.now().year
        expected = dict([(str(year), expected_results['basic stats'][
                        'number of papers']) for year in
                        range(1996, current_year + 1)])
        self.assertEqual(hist['all reads'], expected)
        # and for the same reason, every entry in the histogram for refereed
        # papers should equal the number of refereed papers
        expected = dict([(str(year), expected_results['basic stats refereed'][
                        'number of papers']) for year in
                        range(1996, current_year + 1)])
        self.assertEqual(hist['refereed reads'], expected)
        # For the normalized histograms, each entry should equal the
        # normalized paper count. Because we're dealing with a dictionary of
        # floats, we do things slightly differently:
        # Check that all entries are equal
        self.assertEqual(len(set(hist['all reads normalized'].values())), 1)
        # and then check that one entry has the expected value
        er = expected_results['basic stats']['normalized paper count']
        self.assertAlmostEqual(hist['all reads normalized'].values()[0], er)
        # Because the downloads have been constructed in the same way, we only
        # need to verify that the downloads histograms are the same as the
        # reads ones
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset,
                             'types': ['histograms'],
                             'histograms': ['downloads']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(r.json.keys(), [u'histograms', u'skipped bibcodes'])
        self.assertTrue(r.json['histograms'].keys(), ['downloads'])
        self.assertTrue(r.json['histograms']['downloads'].keys(), [
                        'all downloads', 'refereed downloads'])
        dhist = r.json['histograms']['downloads']
        self.assertEqual(hist['all reads'], dhist['all downloads'])
        self.assertEqual(hist['refereed reads'], dhist['refereed downloads'])
        self.assertEqual(
            hist['all reads normalized'],
            dhist['all downloads normalized'])
        self.assertEqual(
            hist['refereed reads normalized'],
            dhist['refereed downloads normalized'])


class TestCitationHistogramsBibcodes(TestCase):

    '''Check if the citation histograms are returned for valid bibcodes'''

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

    def test_get_citation_histograms_bibcodes(self):
        '''Test getting just citation histograms when valid bibcodes
           are submitted'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset,
                             'types': ['histograms'],
                             'histograms': ['citations']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(r.json.keys(), [u'histograms', u'skipped bibcodes'])
        self.assertTrue(r.json['histograms'].keys(), ['citations'])
        hist = r.json['histograms']['citations']
        # Histogram types
        histograms = [u'refereed to nonrefereed',
                      u'nonrefereed to nonrefereed',
                      u'nonrefereed to nonrefereed normalized',
                      u'nonrefereed to refereed',
                      u'refereed to refereed normalized',
                      u'refereed to nonrefereed normalized',
                      u'refereed to refereed',
                      u'nonrefereed to refereed normalized']
        # Check that they are all there
        self.assertEqual(r.json['histograms']['citations'].keys(), histograms)
        for histogram in histograms:
            # Get the expected values
            expected = expected_results['histograms']['citations'][histogram]
            # Get the non-zero entries for the histogram we just generated
            nonzero = dict(
                [(year, freq) for year, freq in hist[histogram].items() if
                 freq != 0])
            # and compare
            self.assertEqual(nonzero, expected)


class TestAllHistogramsBibcodes(TestCase):

    '''Check if all histograms are returned when no type is specified'''

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

    def test_get_all_histograms_bibcodes(self):
        '''Test getting all histograms when no specific type is specified'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset, 'types': ['histograms']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(r.json.keys(), [u'histograms', u'skipped bibcodes'])
        self.assertTrue(
            r.json['histograms'].keys(),
            ['publications', 'usage', 'citations'])


class TestTimeSeriesBibcodes(TestCase):

    '''Check if the time series are returned for valid bibcodes'''

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

    def test_get_timeseries_bibcodes(self):
        '''Test getting just time series when valid bibcodes are submitted'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset, 'types': ['timeseries']}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        self.assertTrue(r.json.keys(), [u'time series', u'skipped bibcodes'])
        ts = r.json['time series']
        # The time series get test over the range of publication years
        years = [int(b[:4]) for b in testset]
        yrange = range(min(years), max(years) + 1)
        indicators = ['h', 'g', 'i10', 'i100', 'read10']
        for indicator in indicators:
            serie = {str(y): ts[indicator][str(y)] for y in yrange}
            expected = {
                k: v for k, v in
                expected_results['time series'][indicator].items()}
            self.assertEqual(serie, expected)


class TestEverythingBibcodes(TestCase):

    '''Check if everything returned when no metrics type is specified'''

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

    def test_get_everything_bibcodes(self):
        '''Test getting everything when no specific metrics type
           is specified'''
        r = self.client.post(
            url_for('metrics'),
            content_type='application/json',
            data=json.dumps({'bibcodes': testset}))
        self.assertTrue(r.status_code == 200)
        # Check that the right info is returned; nothing more, nothing less
        expected_keys = ['basic stats', 'citation stats refereed',
                         'histograms', 'citation stats', 'time series',
                         'basic stats refereed', 'indicators refereed',
                         'skipped bibcodes', 'indicators']
        self.assertEqual(r.json.keys(), expected_keys)
        self.assertTrue(
            r.json['histograms'].keys(),
            ['publications', 'usage', 'citations'])


class TestMetricsSingleBibcode(TestCase):

    '''Check getting metrics for a single bibcode'''

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

    def test_get_metrics_single_bibcode(self):
        '''Test getting metrics for a single bibcode'''
        url = url_for('pubmetrics', bibcode='1997BoLMe..85..475M')
        r = self.client.get(url)
        # The response should have a status code 200
        self.assertTrue(r.status_code == 200)
        # The JSON should contain results for
        expected_keys = [u'basic stats',
                         u'citation stats refereed',
                         u'histograms',
                         u'citation stats',
                         u'basic stats refereed',
                         u'skipped bibcodes']
        self.assertEqual(r.json.keys(), expected_keys)
        # The histograms should consist of reads and citations
        self.assertEqual(r.json['histograms'].keys(), ['reads', 'citations'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
