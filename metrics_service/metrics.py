'''
Created on April 8, 2015

@author: ehenneken
'''
from future import standard_library
standard_library.install_aliases()
from builtins import zip
from builtins import range
from flask import current_app, request
import sys
import time
import os
import urllib.request, urllib.parse, urllib.error
import itertools
#import simplejson as json
import json
import numpy as np
import cytoolz as cy
from math import sqrt
from collections import defaultdict
from operator import itemgetter
from datetime import date, datetime
from .models import get_identifiers
from .models import get_basic_stats_data
from .models import get_citations
from .models import get_citation_data
from .models import get_publication_data
from .models import get_usage_data
from .models import get_indicator_data
from .models import get_tori_data
from .models import get_citations_single

# Helper methods
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)

def chunks(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_norm_histo(l):
    d = defaultdict(list)
    for tag, num in l:
        d[tag].append(num)
    return {k: sum(v) for k, v in d.items()}


def merge_dictionaries(x, y):
    '''Given two dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    z.update(y)
    return z

# Main engine: retrieves the desired statistics


def generate_metrics(**args):
    result = {}
    usage_data = None
    citdata = None
    citlists = None
    selfcits = None
    tdata = None
    metrics_types = args.get('types', [])
    # If we don't have any metrics type, return empty results
    if len(metrics_types) == 0:
        return result
    tori = args.get('tori', True)
    # First retrieve the data we need for our calculations
    bibcodes, bibcodes_ref, identifiers, skipped = get_record_info(
        bibcodes=args.get('bibcodes', []), query=args.get('query', None))
#    if len(bibcodes) == 1 and len(metrics_types) == 0:
#        metrics_types = ['basic', 'citations', 'histograms']
    # If no identifiers were returned, return empty results
    if len(identifiers) == 0:
        return result
    # Record the bibcodes that fell off the wagon
    result['skipped bibcodes'] = skipped
    # If there are skipped records, create a log message
    if len(skipped) > 0:
        current_app.logger.warning('Found %s skipped bibcodes in metrics request: %s'%(len(skipped),",".join(skipped)))
    # Start calculating the required statistics and indicators
    citdata = usage_data = citlists = selfcits = None
    if 'basic' in metrics_types:
        basic_stats, basic_stats_refereed, usage_data = \
            get_basic_stats(identifiers)
        result['basic stats'] = basic_stats
        result['basic stats refereed'] = basic_stats_refereed
    if 'citations' in metrics_types:
        cite_stats, cite_stats_refereed, citdata, selfcits, citlists = \
            get_citation_stats(identifiers, bibcodes, bibcodes_ref)
        result['citation stats'] = cite_stats
        result['citation stats refereed'] = cite_stats_refereed
    if 'histograms' in metrics_types:
        hists = {}
        hist_types = args.get('histograms')
        if 'publications' in hist_types and len(identifiers) > 1:
            hists['publications'] = get_publication_histograms(identifiers)
        if 'reads' in hist_types:
            hists['reads'] = get_usage_histograms(identifiers, data=usage_data)
        if 'downloads' in hist_types and len(identifiers) > 1:
            hists['downloads'] = get_usage_histograms(
                identifiers, usage_type='downloads', data=usage_data)
        if 'citations' in hist_types:
            hists['citations'] = get_citation_histograms(
                identifiers, data=citlists)
        result['histograms'] = hists
    if 'indicators' in metrics_types:
        indicators = {}
        indic, indic_ref = get_indicators(
            identifiers, data=citdata, usagedata=usage_data)
        if tori:
            tori, tori_ref, riq, riq_ref, tdata = get_tori(
                identifiers, bibcodes, self_cits=selfcits)
            indic['tori'] = tori
            indic['riq'] = riq
            indic_ref['tori'] = tori_ref
            indic_ref['riq'] = riq_ref
        else:
            indic['tori'] = 'NA'
            indic['riq'] = 'NA'
            indic_ref['tori'] = 'NA'
            indic_ref['riq'] = 'NA'
        result['indicators'] = indic
        result['indicators refereed'] = indic_ref
    if 'timeseries' in metrics_types or 'time series' in metrics_types:
        result['time series'] = get_time_series(
            identifiers,
            bibcodes,
            data=citlists,
            usagedata=usage_data,
            tori_data=tdata,
            include_tori=tori,
            self_cits=selfcits)
    # The next line takes care of mapping numpy float64 and int64 values to regular floats and integers
    # (JSON serialization fails for numpy float64 and int64 classes)
    res = json.loads(json.dumps(result, cls=MyEncoder))
    return res

# Data retrieval methods
# A. Data before we any sort of computation
# Get bibcodes, identifiers and establish bibcodes for which we have no data
# (which could be because the bibcode is invalid or because something went
# wrong creating the database record fort that publication)


def get_record_info(**args):
    # Did we get bibcodes?
    if args.get('bibcodes', []):
        IDmap = get_identifiers(args['bibcodes'])
        IDs = [x[1] for x in IDmap]
        bibs = [x[0] for x in IDmap]
        bibs_ref = [x[0] for x in IDmap if x[2]]
        missing = [b for b in args['bibcodes'] if b not in bibs]
        return bibs, bibs_ref, IDs, missing
    else:
        return {"Error": "Unable to get results!",
                "Error Info": "Unsupported metrics request",
                "Status Code": 200}

# Get citations, self-citations


def get_selfcitations(identifiers, bibcodes):
    data = get_citations(identifiers)
    # record the actual self-citations so that we can use that
    # information later on in the calculation of the Tori
    try:
        selfcits = [
            (set(p.citations).intersection(set(bibcodes)), p.refereed)
            for p in data]
    except:
        selfcits = [([], False)]
        return data, selfcits, 0, 0, 0, 0
    Nself = sum([len(c[0]) for c in selfcits])
    Nself_refereed = sum([len(c[0]) * c[1] for c in selfcits])
    Nciting = len(set(itertools.chain(*[p.citations for p in data])))
    Nciting_ref = len(
    set(itertools.chain(*[p.citations for p in data if p.refereed])))
    return data, selfcits, Nself, Nself_refereed, Nciting, Nciting_ref

# B. Statistics functions
# The basic stats function gets the publication and usage stats


def get_basic_stats(identifiers):
    # basic stats for all publications
    bs = {}
    # basic stats for refereed publications`
    bsr = {}
    # Get the data to calculate the basic stats
    data = get_basic_stats_data(identifiers)
    # First get the number of (refereed) papers
    bs['number of papers'] = len(identifiers)
    bsr['number of papers'] = len([p for p in data if p.refereed])
    # Next get the (refereed) normalized paper count
    bs['normalized paper count'] = np.sum(
        np.array([1.0 / float(p.author_num) for p in data]), dtype=float)
    bsr['normalized paper count'] = np.sum(
        np.array([1.0 / float(p.author_num) for p in data if p.refereed]), dtype=float)
    # Get the total number of reads
    year = datetime.now().year
    Nentries = year - 1996 + 1
    reads = [p.reads for p in data if p.reads and len(p.reads) == Nentries]
    reads_ref = [
        p.reads for p in data if p.refereed and p.reads and
        len(p.reads) == Nentries]
    reads_totals = [sum(r) for r in reads]
    reads_ref_totals = [sum(r) for r in reads_ref]
    bs['total number of reads'] = np.sum(reads_totals or [0], dtype=int)
    bsr['total number of reads'] = np.sum(reads_ref_totals or [0], dtype=int)
    # Get the average number of reads
    try:
        bs['average number of reads'] = float(bs['total number of reads'])/float(bs['number of papers'])
    except:
        bs['average number of reads'] = 0.0
    try:
        bsr['average number of reads'] = float(bsr['total number of reads'])/float(bsr['number of papers'])
    except:
        bsr['average number of reads'] = 0.0
    # Get the median number of reads
    bs['median number of reads'] = np.median(reads_totals or [0])
    bsr['median number of reads'] = np.median(reads_ref_totals or [0])
    # Get the normalized number of reads
    # bs['normalized number of reads'] = \
    # np.sum([np.array(p.reads)/float(p.author_num)
    # for p in data if p.reads and len(p.reads) == Nentries])
    # bsr['normalized number of reads'] = \
    # sum([p.reads[-1] for p in data if p.refereed and
    # p.reads and len(p.reads) == Nentries])
    # and finally, get the recent reads
    bs['recent number of reads'] = sum(
        [p.reads[-1] for p in data if p.reads and len(p.reads) == Nentries])
    bsr['recent number of reads'] = sum(
        [p.reads[-1] for p in data if p.refereed and p.reads and
         len(p.reads) == Nentries])
    # Do the same for the downloads
    downloads = [
        p.downloads for p in data if p.downloads and
        len(p.downloads) == Nentries]
    downloads_ref = [p.downloads for p in data if p.refereed and
                     p.downloads and len(p.downloads) == Nentries]
    downloads_totals = [sum(d) for d in downloads]
    downloads_ref_totals = [sum(d) for d in downloads_ref]
    bs['total number of downloads'] = np.sum(downloads_totals or [0], dtype=int)
    bsr['total number of downloads'] = np.sum(downloads_ref_totals or [0], dtype=int)
    # Get the average number of downloads
    bs['average number of downloads'] = np.mean(downloads_totals or [0], dtype=float)
    bsr['average number of downloads'] = np.mean(downloads_ref_totals or [0], dtype=float)
    # Get the median number of downloads
    bs['median number of downloads'] = np.median(downloads_totals or [0])
    bsr['median number of downloads'] = np.median(downloads_ref_totals or [0])
    # Get the normalized number of downloads
    # bs['normalized number of downloads'] = \
    # np.sum([np.array(p.downloads)/float(p.author_num) for p in data if
    # p.downloads and len(p.downloads) == Nentries])
    # bsr['normalized number of downloads'] = \
    # np.sum([np.array(p.downloads)/float(p.author_num) for p in data if
    # p.refereed and p.downloads and len(p.downloads) == Nentries])
    # and finally, get the recent number of downloads
    bs['recent number of downloads'] = sum(
        [p.downloads[-1] for p in data if p.downloads and
         len(p.downloads) == Nentries])
    bsr['recent number of downloads'] = sum(
        [p.downloads[-1] for p in data if p.refereed and p.downloads and
         len(p.downloads) == Nentries])
    # Return both results and the data (which will get used later on
    # if the usage histograms are required)
    return bs, bsr, data

# The citation stats function gets statistics for citations


def get_citation_stats(identifiers, bibcodes, bibcodes_ref):
    data = selfcits = citdata = None
    # citation stats for all publications
    cs = {}
    # citation stats for refereed publications
    csr = {}
    # Get the data to compute the citation statistics
    # First get data with just the numbers
    data = get_citation_data(identifiers)
    Nzero = len(bibcodes) - len(data)
    Nzero_ref = len(bibcodes_ref) - \
        len([p.citation_num for p in data if p.refereed])
    citnums = [p.citation_num for p in data] + [0] * Nzero
    ref_citnums = [p.refereed_citation_num for p in data] + [0] * Nzero
    citnums_ref = [
        p.citation_num for p in data if p.refereed] + [0] * Nzero_ref
    ref_citnums_ref = [
        p.refereed_citation_num for p in data if p.refereed] + [0] * Nzero_ref
    # Next, get more detailed citation information
    # (with data to be used later on)
    # citdata    : data structure with citation data for reuse later on
    # selfcits   : data structure with self-citations
    # Nself      : number of self-citations
    # Nself_ref  : number of self-citations for refereed publications
    # Nciting    : number of citing papers
    # Nciting_ref: number of citing papers for refereed publications
    citdata, selfcits, Nself, Nself_ref, Nciting, Nciting_ref = \
        get_selfcitations(identifiers, bibcodes)
    # The number of unique citing papers and the number of self-citations
    cs['number of citing papers'] = Nciting
    csr['number of citing papers'] = Nciting_ref
    cs['number of self-citations'] = Nself
    self_citations = list(itertools.chain(*[list(e[0]) for e in selfcits if len(e[0]) > 0]))
    cs['self-citations'] = self_citations
    csr['number of self-citations'] = Nself_ref
    # The citation stats
    # Total number of citations
    cs['total number of citations'] = np.sum(
        [p.citation_num for p in data] or [0], dtype=int)
    csr['total number of citations'] = np.sum(
        [p.citation_num for p in data if p.refereed] or [0], dtype=int)
    # Average number of citations
    cs['average number of citations'] = np.mean(citnums or [0], dtype=float)
    csr['average number of citations'] = np.mean(citnums_ref or [0], dtype=float)
    # Median number of citations
    cs['median number of citations'] = np.median(citnums or [0])
    csr['median number of citations'] = np.median(citnums_ref or [0])
    # Normalized number of citations
    cs['normalized number of citations'] = np.sum(
        [float(p.citation_num) / float(p.author_num) for p in data] or [0], dtype=float)
    csr['normalized number of citations'] = np.sum(
        [float(p.citation_num) / float(p.author_num) for p in data if
         p.refereed] or [0], dtype=float)
    # The refereed citations stats
    ##
    cs['total number of refereed citations'] = np.sum(
        [p.refereed_citation_num for p in data]or [0], dtype=int)
    csr['total number of refereed citations'] = np.sum(
        [p.refereed_citation_num for p in data if p.refereed] or [0], dtype=int)
    cs['average number of refereed citations'] = np.mean(ref_citnums or [0], dtype=float)
    csr['average number of refereed citations'] = np.mean(
        ref_citnums_ref or [0], dtype=float)
    cs['median number of refereed citations'] = np.median(ref_citnums or [0])
    csr['median number of refereed citations'] = np.median(
        ref_citnums_ref or [0])
    cs['normalized number of refereed citations'] = np.sum(
        [float(p.refereed_citation_num) / float(p.author_num) for
         p in data] or [0], dtype=float)
    csr['normalized number of refereed citations'] = np.sum(
        [float(p.refereed_citation_num) / float(p.author_num) for
         p in data if p.refereed] or [0], dtype=float)
    # Send the results back
    return cs, csr, data, selfcits, citdata


def get_publication_histograms(identifiers):
    ph = {}
    current_year = datetime.now().year
    # Get necessary data
    data = get_publication_data(identifiers)
    # Get the publication histogram
    years = [int(p.bibcode[:4]) for p in data]
    nullhist = [(y, 0) for y in range(min(years), current_year + 1)]
    yearhist = cy.frequencies(years)
    ph['all publications'] = merge_dictionaries(dict(nullhist), yearhist)
    years_ref = [int(p.bibcode[:4]) for p in data if p.refereed]
    yearhist = cy.frequencies(years_ref)
    ph['refereed publications'] = merge_dictionaries(dict(nullhist), yearhist)
    # Get the normalized publication histogram
    tmp = [(int(p.bibcode[:4]), 1.0 / float(p.author_num)) for p in data]
    ph['all publications normalized'] = get_norm_histo(nullhist + tmp)
    tmp = [(int(p.bibcode[:4]), 1.0 / float(p.author_num))
           for p in data if p.refereed]
    ph['refereed publications normalized'] = get_norm_histo(nullhist + tmp)
    return ph


def get_usage_histograms(identifiers, usage_type='reads', data=None):
    uh = {}
    # Get necessary data if nothing was provided
    if not data:
        data = get_usage_data(identifiers)
    # Determine the current year (so that we know how many entries to expect
    # in usage lists)
    year = datetime.now().year
    Nentries = year - 1996 + 1
    zeros = [[0] * Nentries]
    if usage_type == 'reads':
        # Get all reads data and sum up the individual lists
        usage_data = [
            p.reads for p in data if p.reads and len(p.reads) == Nentries]
        usage = [sum(sublist)
                 for sublist in zip(*usage_data or zeros)]
        # and also get the normalized reads
        usage_data = [np.array(p.reads, dtype=int) / float(p.author_num)
                      for p in data if p.reads and len(p.reads) == Nentries]
        usage_norm = [sum(sublist)
                      for sublist in zip(*usage_data or zeros)]
        # Do the same for just the refereed publications
        usage_data = [p.reads for p in data if p.refereed and p.reads and
                      len(p.reads) == Nentries]
        usage_ref = [sum(sublist)
                     for sublist in zip(*usage_data or zeros)]
        # and also get the normalized version
        usage_data = [np.array(p.reads, dtype=int) / float(p.author_num)
                      for p in data if p.refereed and p.reads and
                      len(p.reads) == Nentries]
        usage_ref_norm = [sum(sublist)
                          for sublist in zip(*usage_data or zeros)]
    else:
        usage_type = 'downloads'
        # Get all downloads data and sum up the individual lists
        usage_data = [
            p.downloads for p in data if p.downloads and
            len(p.downloads) == Nentries]
        usage = [sum(sublist)
                 for sublist in zip(*usage_data or zeros)]
        # and also get the normalized version
        usage_data = [np.array(p.downloads, dtype=int) / float(p.author_num)
                      for p in data if p.downloads and
                      len(p.downloads) == Nentries]
        usage_norm = [sum(sublist)
                      for sublist in zip(*usage_data or zeros)]
        # Do the same for just the refereed publications
        usage_data = [p.downloads for p in data if p.refereed and
                      p.downloads and len(p.downloads) == Nentries]
        usage_ref = [sum(sublist)
                     for sublist in zip(*usage_data or zeros)]
        # and also get the normalized version
        usage_data = [np.array(p.downloads, dtype=int) / float(p.author_num)
                      for p in data if p.refereed and p.downloads and
                      len(p.downloads) == Nentries]
        usage_ref_norm = [sum(sublist)
                          for sublist in zip(*usage_data or zeros)]
        # Construct the histograms (index 0 corresponds with year 1996)
    uh['all %s' % usage_type] = dict(
        [(1996 + i, v) for i, v in enumerate(usage)])
    uh['all %s normalized' % usage_type] = dict(
        [(1996 + i, v) for i, v in enumerate(usage_norm)])
    uh['refereed %s' % usage_type] = dict(
        [(1996 + i, v) for i, v in enumerate(usage_ref)])
    uh['refereed %s normalized' % usage_type] = dict(
        [(1996 + i, v) for i, v in enumerate(usage_ref_norm)])
    return uh


def get_citation_histograms(identifiers, data=None):
    ch = {}
    current_year = datetime.now().year
    # Get necessary data if nothing was provided
    if not data:
        data = get_citations(identifiers)
    if len(data) == 0:
        data = get_citations(identifiers, no_zero=False)
    years = [int(p.bibcode[:4]) for p in data]
    # First gather all necessary data
    # refereed -> refereed
    rr_data = [([int(c[:4]) for c in p.refereed_citations],
                1.0 / float(p.author_num)) for p in data if p.refereed]
    # refereed -> non-refereed
    rn_data = [([int(c[:4]) for c in p.citations if c in p.refereed_citations],
                1.0 / float(p.author_num)) for p in data if not p.refereed]
    # non-refereed -> refereed
    nr_data = [([int(c[:4]) for c in list(set(p.citations).difference(
        set(p.refereed_citations)))], 1.0 / float(p.author_num)) for
        p in data if p.refereed]
    # non-refereed -> non-refereed
    nn_data = [([int(c[:4]) for c in p.citations if
                 c not in p.refereed_citations],
                1.0 / float(p.author_num)) for p in data if not p.refereed]
    # First construct the regular histograms
    max_year = current_year
    rr_hist = cy.frequencies(list(itertools.chain(*[d[0] for d in rr_data])))
    rn_hist = cy.frequencies(list(itertools.chain(*[d[0] for d in rn_data])))
    nr_hist = cy.frequencies(list(itertools.chain(*[d[0] for d in nr_data])))
    nn_hist = cy.frequencies(list(itertools.chain(*[d[0] for d in nn_data])))
    # From the years of the citations, determine the maximum
    cityears = list(dict(rr_hist).keys()) + list(dict(rn_hist).keys()) + list(dict(nr_hist).keys()) + list(dict(nn_hist).keys())
    max_year = max(cityears or [0])
    # If this year lies in the future, set the "current year" to that year
    if max_year > current_year:
        current_year = max_year
    # Get the earliest citation
    try:
        min_year = min(cityears)
        nullhist = [(y, 0) for y in range(min_year, current_year + 1)]
    except:
        nullhist = [(y, 0) for y in range(min(years), current_year + 1)]
    if len(nullhist) == 0:
        nullhist = [(min(years), 0)]
    # Now create the histograms with zeroes for year without values
    ch['refereed to refereed'] = merge_dictionaries(dict(nullhist), rr_hist)
    ch['refereed to nonrefereed'] = merge_dictionaries(dict(nullhist), rn_hist)
    ch['nonrefereed to refereed'] = merge_dictionaries(dict(nullhist), nr_hist)
    ch['nonrefereed to nonrefereed'] = merge_dictionaries(
        dict(nullhist), nn_hist)
    min_year = min(list(ch['refereed to refereed'].keys()) +
                   list(ch['refereed to nonrefereed'].keys()) +
                   list(ch['nonrefereed to refereed'].keys()) +
                   list(ch['nonrefereed to nonrefereed'].keys()))
    nullhist = [(y, 0) for y in range(min_year, current_year + 1)]
    # Normalized histograms need a different approach
    tmp = list(itertools.chain(*[[(d, x[1]) for d in x[0]] for x in rr_data]))
    ch['refereed to refereed normalized'] = get_norm_histo(nullhist + tmp)
    tmp = list(itertools.chain(*[[(d, x[1]) for d in x[0]] for x in rn_data]))
    ch['refereed to nonrefereed normalized'] = get_norm_histo(nullhist + tmp)
    tmp = list(itertools.chain(*[[(d, x[1]) for d in x[0]] for x in nr_data]))
    ch['nonrefereed to refereed normalized'] = get_norm_histo(nullhist + tmp)
    tmp = list(itertools.chain(*[[(d, x[1]) for d in x[0]] for x in nn_data]))
    ch['nonrefereed to nonrefereed normalized'] = get_norm_histo(
        nullhist + tmp)
    return ch


def get_indicators(identifiers, data=None, usagedata=None):
    ind = {}
    ind_ref = {}
    # Get the necessary data if we did not get any
    if not data:
        data = get_indicator_data(identifiers)
    if not usagedata:
        usagedata = get_usage_data(identifiers)
    # Organize the citations with a running index (the citation
    # data is already ordered from most to least cited)
    citations = [(i + 1, p.citation_num) for i, p in enumerate(data)]
    # First the Hirsch index
    ind['h'] = max([x[0] for x in citations if x[1] >= x[0]] or [0])
    # Next the g index
    ind['g'] = max([i for (c, i) in zip(list(np.cumsum([x[1] for
                    x in citations], axis=0)), [x[0] for x in citations]) if
                    i**2 <= c] or [0])
    # The number of paper with 10 or more citations (i10)
    ind['i10'] = len([x for x in citations if x[1] >= 10])
    # The number of paper with 100 or more citations (i100)
    ind['i100'] = len([x for x in citations if x[1] >= 100])
    # The m index is the g index divided by the range of publication years
    yrange = datetime.now().year - \
        min([int(p.bibcode[:4]) for p in usagedata]) + 1
    # In the annoying case where all pubs are from next year, the above should be just 1
    yrange = max(yrange, 1)
    ind['m'] = float(ind['h']) / float(yrange)
    # The read10 index is calculated from current reads for papers published
    # in the last 10 years, normalized by number of authors
    year = datetime.now().year
    Nentries = year - 1996 + 1
    ind['read10'] = sum([float(p.reads[-1]) / float(p.author_num)
                         for p in usagedata if
                         int(p.bibcode[:4]) > year - 10 and p.reads and
                         len(p.reads) == Nentries])
    d0 = date(datetime.now().year, 1, 1)
    d1 = date(datetime.now().year, datetime.now().month, datetime.now().day)
    d2 = date(datetime.now().year, 12, 31)
    delta = (d1 - d0).days + 1
    ndays = (d2 - d0).days + 1
    try:
        r10_corr = float(ndays)/float(delta)
    except:
        r10_corr = 1.0
    ind['read10'] = ind['read10']*r10_corr
    # Now all the values for the refereed publications
    citations = [(i + 1, n) for i, n in enumerate([p.citation_num for p in
                                                   data if p.refereed])]
    # First the Hirsch index
    ind_ref['h'] = max([x[0] for x in citations if x[1] >= x[0]] or [0])
    # Next the g index
    ind_ref['g'] = max([i for (c, i) in zip(list(np.cumsum(
        [x[1] for x in citations], axis=0)), [x[0] for x in citations]) if
        i**2 <= c] or [0])
    # The number of paper with 10 or more citations (i10)
    ind_ref['i10'] = len([x for x in citations if x[1] >= 10])
    # The number of paper with 100 or more citations (i100)
    ind_ref['i100'] = len([x for x in citations if x[1] >= 100])
    # The m index is the g index divided by the range of publication years
    yrange_ref = datetime.now().year - \
        min([int(p.bibcode[:4]) for p in usagedata]) + 1
    # In the annoying case where all pubs are from next year, the above should be just 1
    yrange_ref = max(yrange_ref, 1)
    ind_ref['m'] = float(ind_ref['h']) / float(yrange_ref)
    # The read10 index is calculated from current reads for papers published
    # in the last 10 years, normalized by number of authors
    year = datetime.now().year
    Nentries = year - 1996 + 1
    ind_ref['read10'] = sum([float(p.reads[-1]) / float(p.author_num)
                             for p in usagedata if p.refereed and
                             int(p.bibcode[:4]) > year - 10 and
                             p.reads and len(p.reads) == Nentries])
    ind_ref['read10'] = ind_ref['read10']*r10_corr
    # Send results back
    return ind, ind_ref

def get_tori(identifiers, bibcodes, self_cits=None):
    # Get additional data necessary for Tori calculation
    data = get_tori_data(identifiers)
    if len(data) == 0:
        return 0, 0, 0, 0, []
    # If we did not get self-citations, retrieve them
    if not self_cits:
        self_cits = get_selfcitations(identifiers, bibcodes)[1]
    self_citations = set((itertools.chain(*[x[0] for x in self_cits])))
    # Now we can calculate the Tori index
    tori_data = [p for p in list(itertools.chain(
        *[p.rn_citation_data for p in data if p.rn_citation_data])) if
        p['bibcode'] not in self_citations and 'pubyear' in p]
    tori_data_ref = [p for p in list(itertools.chain(
        *[p.rn_citation_data for p in data if p.refereed and
            p.rn_citation_data])) if p['bibcode'] not in self_citations]
    try:
        tori = np.sum(
            np.array([r['auth_norm'] * r['ref_norm'] for r in tori_data]), dtype=float)
        tori_ref = np.sum(
            np.array([r['auth_norm'] * r['ref_norm'] for r in tori_data_ref]), dtype=float)
    except:
        return 0, 0, 0, 0, tori_data
    # The riq index follows from the Tori index and the year range
    #yrange = datetime.now().year - min([int(b[:4]) for b in bibcodes]) + 1
    yrange = max([int(b[:4]) for b in bibcodes]) - min([int(b[:4]) for b in bibcodes]) + 1
    #yrange_ref = datetime.now().year - \
    #    min([int(p.bibcode[:4]) for p in data]) + 1
    # In the annoying case where all pubs are from next year, the above should be just 1
    yrange = max(yrange, 1)
    riq = int(1000.0 * sqrt(float(tori)) / float(yrange))
    riq_ref = int(1000.0 * sqrt(float(tori_ref)) / float(yrange))
    # Send the results back
    return tori, tori_ref, riq, riq_ref, tori_data

def get_time_series(identifiers, bibcodes, data=None, usagedata=None,
                    tori_data=None, include_tori=True, self_cits=None):
    series = {}
    i10 = {}
    i100 = {}
    h = {}
    g = {}
    r10 = {}
    tori = {}
    # Get data if nothing was supplied
    if not data:
        data = get_citations(identifiers)
    if not usagedata:
        usagedata = get_usage_data(identifiers)
    if not self_cits and include_tori:
        self_cits = get_selfcitations(identifiers, bibcodes)[1]
        self_citations = set((itertools.chain(*[x[0] for x in self_cits])))
    if not tori_data and include_tori:
        tdata = get_tori_data(identifiers)
        tori_data = [p for p in list(itertools.chain(
            *[p.rn_citation_data for p in tdata if p.rn_citation_data])) if
            p['bibcode'] not in self_citations and 'pubyear' in p]
    # Determine the year range
    Nentries = datetime.now().year - 1996 + 1
    years = [int(b[:4]) for b in bibcodes]
    yrange = list(range(min(years), datetime.now().year + 1))
    d0 = date(datetime.now().year, 1, 1)
    d1 = date(datetime.now().year, datetime.now().month, datetime.now().day)
    d2 = date(datetime.now().year, 12, 31)
    delta = (d1 - d0).days + 1
    ndays = (d2 - d0).days + 1
    try:
       r10_corr = float(ndays)/float(delta)
    except:
       r10_corr = 1.0
    for year in yrange:
        biblist = [b for b in bibcodes if int(b[:4]) <= year]
        citations = sorted([len([int(c[:4]) for c in p.citations if int(
            c[:4]) <= year]) for p in data if
            p.bibcode in biblist], reverse=True)
        if year < 1996:
            r10[year] = 0.0
        else:
            idx = year - 1996
            r10[year] = sum([float(p.reads[idx]) / float(p.author_num) for
                             p in usagedata if p.bibcode in biblist and int(
                p.bibcode[:4]) > year - 10 and p.reads and
                len(p.reads) == Nentries])
        try:
            h[year] = max([i for i, n in enumerate(citations, 1) if i <= n])
            g[year] = max(
                [i for i, n in enumerate(np.cumsum(citations, axis=0), 1) if
                 i**2 <= n])
        except:
            h[year] = 0
            g[year] = 0
        i10[year] = len([c for c in citations if c >= 10])
        i100[year] = len([c for c in citations if c >= 100])
        if include_tori:
            tori[year] = np.sum(np.array([r['auth_norm'] * r['ref_norm'] for
                                          r in tori_data if
                                          r['pubyear'] <= year and
                                          r['cityear'] <= year]))
    # When all papers are from next year, the following would fail,
    # and therefore we just skip it
    try:
        r10[datetime.now().year] = r10[datetime.now().year] * r10_corr
    except:
        pass
    series['i10'] = i10
    series['i100'] = i100
    series['h'] = h
    series['g'] = g
    series['read10'] = r10
    if include_tori:
        series['tori'] = tori

    return series

def single_citation_report(bibc):
    histograms = {}
    current_year = datetime.now().year
    Nentries = current_year - 1996 + 1
    zeros = [[0] * Nentries]
    data = get_citations_single(bibc)
    try:
        cityears = [int(b[:4]) for b in data[0].citations]
    except:
        cityears = []
    try:
        refcityears = [int(b[:4]) for b in data[0].refereed_citations]
    except:
        refcityears = []
    try:
        reads = [int(r) for r in data[0].reads]
    except:
        reads = zeros
    try:
        downloads = [int(d) for d in data[0].downloads]
    except:
        downloads = zeros

    nullhist = [(y, 0) for y in range(min(cityears+refcityears), current_year + 1)]
    cithist = cy.frequencies(cityears)
    refcithist = cy.frequencies(refcityears)
    histograms['citations'] = merge_dictionaries(dict(nullhist), cithist)
    histograms['ref_citations'] = merge_dictionaries(dict(nullhist), refcithist)
    # Have the histograms start at the publication year
    histograms['reads'] = dict([(1996 + i, v) for i, v in enumerate(reads) if 1996+i >= int(bibc[:4])])
    histograms['downloads'] = dict([(1996 + i, v) for i, v in enumerate(downloads) if 1996+i >= int(bibc[:4])])

    return histograms
