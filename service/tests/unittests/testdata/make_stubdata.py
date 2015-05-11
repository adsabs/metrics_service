# The purpose of this script is to generate all the data (stub data and expected results) used
# by the unittests.
import itertools
import numpy as np
import simplejson as json
from collections import defaultdict
#
# DATA SECTION 
#
# This section contains all the data necessary to generate everything
#
# The relations here (i.e. numbers and citations are all constructed, so no need to check with the actual ones)
# Data dictionary for the publications in the test set
#
# Usage data will be skipped for the following reason: the metrics module assumes that
# the list with yearly counts will grow and checks that this list has the right amount
# of entries. The stubdata is static so this would be a problem. Therefore usage data is
# dynamically assigned in the unittest, taking into account the current year
#
testdata = {'1997BoLMe..85..475M':{
                'refereed':True,
                'author_num':5,
                'citations':['2006QJRMS.132..779R', '2008Sci...320.1622D', '1998PPGeo..22..553A'],
                'refereed_citations':['2006QJRMS.132..779R', '2008Sci...320.1622D']
             },
            '1997BoLMe..85...81M':{
                'refereed':True,
                'author_num':5,
                'citations':['1997BoLMe..85..475M', '1999BoLMe..92...65D'],
                'refereed_citations':['1997BoLMe..85..475M', '1999BoLMe..92...65D']
            },
            '1997ZGlGl..33..173H':{
                'refereed':True,
                'author_num':5,
                'citations':['1997BoLMe..85...81M','2001JGR...10633965B'],
                'refereed_citations':['1997BoLMe..85...81M','2001JGR...10633965B']               
            },
            '2014bbmb.book..243K':{
                'refereed':False,
                'author_num':2,
                'citations':['2012PLoSO...746428P','2014arXiv1404.3084H'],
                'refereed_citations':['2012PLoSO...746428P']                
            },
            '2012opsa.book..253H':{
                'refereed':False,
                'author_num':3,
                'citations':['2012PLoSO...746428P','2014arXiv1404.3084H','2014bbmb.book..243K'],
                'refereed_citations':['2012PLoSO...746428P']                
            }

}
# For the calculation of the Tori we need the number references in each citation
refnums = {'1997BoLMe..85...81M':3,
           '2001JGR...10633965B':30,
           '2006QJRMS.132..779R':1,
           '2008Sci...320.1622D':17,
           '1998PPGeo..22..553A':1,
           '1997BoLMe..85..475M':3,
           '1999BoLMe..92...65D':1,
           '2012PLoSO...746428P':1,
           '2014arXiv1404.3084H':1,
           '2014bbmb.book..243K':5
}
#
# CALCULATIONS SECTION
#
# This dictionary will be populated with the metrics results for the stub data, 
# in a format very similar to the actual metrics output
stub_metrics = {}
#
# First calculate the basic statistics
#
# First the numbers of papers and normalized paper count for all papers
stub_metrics['basic stats'] = {
    'number of papers': len(testdata), 
    'normalized paper count': sum([1.0/float(r['author_num']) for r in testdata.values()])
}
# and the same for just the refereed papers
stub_metrics['basic stats refereed'] = {'number of papers': len([r for r in testdata.values() if r['refereed']]), 
               'normalized paper count': sum([1.0/float(r['author_num']) for r in testdata.values() if r['refereed']])
}
#
# Next are the citation stats
#
stub_metrics['self-citations'] = [c for c in list(set(itertools.chain(*[r['citations'] for r in testdata.values()]))) if c in testdata]
stub_metrics['citation stats'] = {
    'number of citing papers': len(set(itertools.chain(*[r['citations'] for r in testdata.values()]))),
    'total number of citations': len(list(itertools.chain(*[r['citations'] for r in testdata.values()]))),
    'number of self-citations': len([p for p in list(itertools.chain(*[r['citations'] for r in testdata.values()])) if p in testdata]),
    'average number of citations': np.mean([len(r['citations']) for r in testdata.values()]),
    'median number of citations': np.median([len(r['citations']) for r in testdata.values()]),
    'normalized number of citations': sum([float(len(r['citations']))/float(r['author_num']) for r in testdata.values()]),
    'total number of refereed citations':len(list(itertools.chain(*[r['refereed_citations'] for r in testdata.values()]))),
    'average number of refereed citations': np.mean([len(r['refereed_citations']) for r in testdata.values()]),
    'median number of refereed citations': np.median([len(r['refereed_citations']) for r in testdata.values()]),
    'normalized number of refereed citations': sum([float(len(r['refereed_citations']))/float(r['author_num']) for r in testdata.values()])
}
#
# citation stats for just the refereed papers
#
stub_metrics['citation stats refereed'] = {
    'number of citing papers': len(set(itertools.chain(*[r['citations'] for r in testdata.values() if r['refereed']]))),
    'total number of citations': len(list(itertools.chain(*[r['citations'] for r in testdata.values() if r['refereed']]))),
    'number of self-citations': len([p for p in list(itertools.chain(*[r['citations'] for r in testdata.values() if r['refereed']])) if p in testdata]),
    'average number of citations': np.mean([len(r['citations']) for r in testdata.values() if r['refereed']]),
    'median number of citations': np.median([len(r['citations']) for r in testdata.values() if r['refereed']]),
    'normalized number of citations': sum([float(len(r['citations']))/float(r['author_num']) for r in testdata.values() if r['refereed']]),
    'total number of refereed citations':len(list(itertools.chain(*[r['refereed_citations'] for r in testdata.values() if r['refereed']]))),
    'average number of refereed citations': np.mean([len(r['refereed_citations']) for r in testdata.values() if r['refereed']]),
    'median number of refereed citations': np.median([len(r['refereed_citations']) for r in testdata.values() if r['refereed']]),
    'normalized number of refereed citations': sum([float(len(r['refereed_citations']))/float(r['author_num']) for r in testdata.values() if r['refereed']])
}
#
# Next are the indicators
#
# The 'm' index, because of the division by year range, will be calculated dynamically in the unittest code
#
# First the indicators for all papers
#
citations = [(i+1,n) for i,n in enumerate(sorted([len(r['citations']) for r in testdata.values()], reverse=True))]
stub_metrics['indicators'] = {
    'h': max([x[0] for x in citations if x[1] >= x[0]] or [0]),
    'g': max([i for (c,i) in zip(list(np.cumsum([x[1] for x in citations],axis=0)),[x[0] for x in citations]) if i**2 <= c] or [0]),
    'i10':len([x for x in citations if x[1] >= 10]),
    'i100':len([x for x in citations if x[1] >= 100]),
}
#
# Now calculate the indicators for the refereed publications
#
citations = [(i+1,n) for i,n in enumerate(sorted([len(r['citations']) for r in testdata.values() if r['refereed']], reverse=True))]

stub_metrics['indicators refereed'] = {
    'h': max([x[0] for x in citations if x[1] >= x[0]] or [0]),
    'g': max([i for (c,i) in zip(list(np.cumsum([x[1] for x in citations],axis=0)),[x[0] for x in citations]) if i**2 <= c] or [0]),
    'i10':len([x for x in citations if x[1] >= 10]),
    'i100':len([x for x in citations if x[1] >= 100]),
}
# The Tori index for all papers: calculated as the sum over all papers: 1/(#references in citation * #authors in cited)
# where #references = max(5, actual #references)
tori = 0.0
for bibcode in testdata:
    for citation in testdata[bibcode]['citations']:
        # do not count self-citations
        if citation not in testdata:
            tori += 1.0/(float(testdata[bibcode]['author_num'])*max(5,refnums[citation]))
stub_metrics['indicators']['tori'] = tori
# and now for the refereed publications
tori = 0.0
for bibcode in testdata:
    if not testdata[bibcode]['refereed']:
        continue
    for citation in testdata[bibcode]['citations']:
        # do not count self-citations
        if citation not in testdata:
            tori += 1.0/(float(testdata[bibcode]['author_num'])*max(5,refnums[citation]))
stub_metrics['indicators refereed']['tori'] = tori
#
# Next are the publication histograms. We will only record non-zero values, because in the metrics service output
# the histogram will differ from year to year (adding one entry for each new year). We don't want unittests to fail
# just because we're one year further!
#
stub_metrics['histograms'] = {}
stub_metrics['histograms']['publications'] = {}
h = defaultdict(int)
hr= defaultdict(float)
for b,v in testdata.items():
    h[int(b[:4])] +=1
    hr[int(b[:4])] += 1.0/float(v['author_num'])
stub_metrics['histograms']['publications']['all publications'] = dict(h)
stub_metrics['histograms']['publications']['all publications normalized'] = dict(hr)
# Now for the refereed publications
h = defaultdict(int)
hr= defaultdict(float)
for b,v in testdata.items():
    if not v['refereed']:
        continue
    h[int(b[:4])] +=1
    hr[int(b[:4])] += 1.0/float(v['author_num'])
stub_metrics['histograms']['publications']['refereed publications'] = dict(h)
stub_metrics['histograms']['publications']['refereed publications normalized'] = dict(hr)
#
# Next are the citation histograms
#
stub_metrics['histograms']['citations'] = {}
# Citation histograms are for the following flavors (8 in total):
# 1. refereed to refereed publications
# 2. refereed to non-refereed publications
# 3. non-refereed to refereed publications
# 4. non-refereed to non-refereed publications
# and the normalized version of all of them
#
# First the refereed -> refereed flavor
#
h = defaultdict(int)
hr= defaultdict(float)
for v in testdata.values():
    if not v['refereed']:
        continue
    for c in v['refereed_citations']:
        h[int(c[:4])] +=1
        hr[int(c[:4])] += 1.0/float(v['author_num'])
stub_metrics['histograms']['citations']['refereed to refereed'] = dict(h)
stub_metrics['histograms']['citations']['refereed to refereed normalized'] = dict(hr)
#
# refereed to non-refereed
#
h = defaultdict(int)
hr= defaultdict(float)
for v in testdata.values():
    if v['refereed']:
        continue
    for c in v['refereed_citations']:
        h[int(c[:4])] +=1
        hr[int(c[:4])] += 1.0/float(v['author_num'])
stub_metrics['histograms']['citations']['refereed to nonrefereed'] = dict(h)
stub_metrics['histograms']['citations']['refereed to nonrefereed normalized'] = dict(hr)
#
# non-refereed to refereed
#
h = defaultdict(int)
hr= defaultdict(float)
for v in testdata.values():
    if not v['refereed']:
        continue
    for c in list(set(v['citations']).difference(set(v['refereed_citations']))):
        h[int(c[:4])] +=1
        hr[int(c[:4])] += 1.0/float(v['author_num'])
stub_metrics['histograms']['citations']['nonrefereed to refereed'] = dict(h)
stub_metrics['histograms']['citations']['nonrefereed to refereed normalized'] = dict(hr)
#
# non-refereed to non-refereed
#
h = defaultdict(int)
hr= defaultdict(float)
for v in testdata.values():
    if v['refereed']:
        continue
    for c in list(set(v['citations']).difference(set(v['refereed_citations']))):
        h[int(c[:4])] +=1
        hr[int(c[:4])] += 1.0/float(v['author_num'])
stub_metrics['histograms']['citations']['nonrefereed to nonrefereed'] = dict(h)
stub_metrics['histograms']['citations']['nonrefereed to nonrefereed normalized'] = dict(hr)
#
# And finally the time series
#
series = {}
h = {}
g = {}
i10= {}
i100= {}
r10 = {}
tori= {}
years = [int(b[:4]) for b in testdata.keys()]
# Instead of having a year range going up to now, we take the max of the years. 
# All indicators will remain constant after this max
yrange = range(min(years),max(years)+1)
for year in yrange:
    biblist = [b for b in testdata.keys() if int(b[:4]) <= year]
    citations = sorted([len([int(c[:4]) for c in v['citations'] if int(c[:4]) <= year]) for p,v in testdata.items() if p in biblist], reverse=True)
    h[year] = max([i for i,n in enumerate(citations) if i <= n])
    try:
        g[year] = max([i for i,n in enumerate(np.cumsum(citations,axis=0)) if i**2 <= n])
    except:
        g[year] = 0
    i10[year] = len([c for c in citations if c >= 10])
    i100[year]= len([c for c in citations if c >= 100])
    if year < 1996:
        r10[year] = 0.0
    else:
        r10[year] = sum([1.0/float(testdata[p]['author_num']) for p in biblist if int(p[:4]) > year-10])

    tori_y = 0.0
    for bibcode in biblist:
        for citation in testdata[bibcode]['citations']:
            # Skip citations that are too recent
            if int(citation[:4]) > year:
                continue
            # do not count self-citations
            if citation not in testdata:
                tori_y += 1.0/(float(testdata[bibcode]['author_num'])*max(5,refnums[citation]))
    tori[year] = tori_y

series['i10'] = i10
series['i100']= i100
series['h'] = h
series['g'] = g
series['read10'] = r10
series['tori'] = tori
stub_metrics['time series'] = series
#
# DATA EXPORT SECTION
#
# First save the expected results
#
with open('expected_results', 'wb') as fp:
    json.dump(stub_metrics, fp)
#
# Finally, save all the stub data used to create the mock data in the unittests
#
# First the publications in the test set (for which we need more data)
#
n = 1
for b,v in testdata.items():
    data = {}
    citdata = []
    ofile = "%s.json" % b
    data['bibcode'] = b
    data['id'] = n
    data['refereed'] = v['refereed']
    data['author_num'] = v['author_num']
    data['citations'] = v['citations']
    data['refereed_citations'] = v['refereed_citations']
    data['reads'] = []
    data['downloads'] = []
    data['citation_num'] = len(v['citations'])
    data['refereed_citation_num'] = len(v['refereed_citations'])
    for cit in v['citations']:
        citdata.append({'bibcode':cit, 'ref_norm': 1.0/float(max(5,refnums[cit])), 'auth_norm':1.0/float(v['author_num']), 'pubyear':int(b[:4]), 'cityear':int(c[:4])})
    data['rn_citation_data'] = citdata
    with open(ofile, 'wb') as fp:
        json.dump(data, fp)
    n+=1
#
# Now we create the stub data for the citations, for which we only need
# a small subset of data
#
refereed_citations = list(itertools.chain(*[d['refereed_citations'] for d in testdata.values()]))
for b in refnums:
    if b in testdata:
    # SKip the self-citations
        continue
    ofile = '%s.json' % b
    data = {}
    data['bibcode'] = b
    data['id'] = n
    data['refereed'] = True
    if b not in refereed_citations:
        data['refereed'] = False
    data['reads'] = []
    data['downloads'] = []
    data['citation_num'] = 0
    data['reference_num'] = refnums[b]
    data['refereed_citation_num'] = 0
    data['rn_citation_data'] = []
    data['citations'] = []
    data['refereed_citations'] = []
    data['author_num'] = 1
    with open(ofile, 'wb') as fp:
        json.dump(data, fp)
    n+=1
