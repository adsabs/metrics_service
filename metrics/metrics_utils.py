'''
Created on Oct 29, 2014

@author: ehenneken
'''
# general modules
import os
import operator
import sys
import time
import itertools
import simplejson as json
from multiprocessing import Pool, current_process
from multiprocessing import Manager
#
from flask import current_app
# methods to retrieve various types of data
from utils import get_metrics_data
# Every type of 'metric' is calculated in a 'model'
import metricsmodels

# Helper functions
def sort_list_of_lists(L, index, rvrs=True):
    """
    Sort a list of lists with 'index' as sort key
    """
    return sorted(L, key=operator.itemgetter(index), reverse=rvrs)
# Creation of data vectors for stats calculations
def make_vectors(pubs,metrics_dict):
    """
    Most of the metrics/histograms are calculated by manipulation of lists
    (e.g. sums and averages over a list of numbers). Each publication is 
    represented by a 'vector', which is essentially a data structure containing
    all information necessary to calculate metrics. The entries are as follows:
    0: bibcode
    1: refereed status
    2: number of citations
    3: number of refereed citations
    4: number of authors
    5: number of reads
    6: number of downloads
    7: reads number per year
    8: dictionary with pre-calculated data
    """
    attr_list = []
    for bibcode in pubs:
        vector = [str(bibcode)]
        vector.append(int(metrics_dict.get(bibcode,{}).get('refereed',False)))
        vector.append(metrics_dict.get(bibcode,{}).get('citation_num',0))
        vector.append(metrics_dict.get(bibcode,{}).get('refereed_citation_num',0))
        vector.append(metrics_dict.get(bibcode,{}).get('author_num',1))
        vector.append(sum(metrics_dict.get(bibcode,{}).get('reads',[])))
        vector.append(sum(metrics_dict.get(bibcode,{}).get('downloads',[])))
        vector.append(metrics_dict.get(bibcode,{}).get('reads',[]))
        vector.append(metrics_dict.get(bibcode,{}))
        attr_list.append(vector)
    return attr_list
# D. General data accumulation
def get_attributes(args):
    """
    Gather all data necessary for metrics calculations
    """
    # Get publication information
    bibcodes = map(lambda a: a.strip(), args['bibcodes'])
    # Get precomputed metrics data, key-ed on bibcode
    metrics_data = get_metrics_data(bibcodes=bibcodes)
    missing_bibcodes = filter(lambda a: a not in metrics_data.keys(), bibcodes)
    if len(missing_bibcodes) > 0:
        sys.stderr.write("Bibcodes found with missing metrics data: %s" % ",".join(missing_bibcodes))
    bibcodes = filter(lambda a: a not in missing_bibcodes, bibcodes)
    bibcodes_without_authnums = map(lambda b: b['bibcode'],filter(lambda a: a['author_num'] == 0, metrics_data.values()))
    if len(bibcodes_without_authnums):
        sys.stderr.write("Bibcodes found with author number equal to zero: %s" % ",".join(bibcodes_without_authnums))
    bibcodes = filter(lambda a: a not in bibcodes_without_authnums, bibcodes)
    # Get the number of citing papers
    Nciting = len(list(set(itertools.chain(*map(lambda a: a['citations'], metrics_data.values())))))
    # Nciting_ref refers to citation to the refereed papers in the set
    Nciting_ref = len(list(set(itertools.chain(*map(lambda b: b['citations'], filter(lambda a: a['refereed']==True,metrics_data.values()))))))
    # The attribute vectors will be used to calculate the metrics
    attr_list = make_vectors(bibcodes,metrics_data)
    # We sort the entries in the attribute list on citation count, which
    # will make e.g. the calculation of 'h' trivial
    attr_list = sort_list_of_lists(attr_list,2)

    return attr_list,Nciting,Nciting_ref

# E. Function to call individual model data generation functions
#    in parallel
def generate_data(model_class):
    model_class.generate_data()
    return model_class.results

# F. Format and export the end results
#    In theory we could build in other formats by e.g. a 'format=foo' in the
#    'args' and implementing an associated procedure in the method
def format_results(data_dict,**args):
    # We want to return JSON, and at the same time support backward compatibility
    # This is achieved by stucturing the resulting JSON into sections that
    # correspond with the output from the 'legacy' metrics module
    stats = ['publications', 'refereed_citations', 'citations', 'metrics','refereed_metrics']
    doc = {}
    doc['all stats'] = dict((k.replace('(Total)','').strip(),v) for d in data_dict for (k,v) in d.items() if '(Total)' in k and d['type'] in stats)
    doc['refereed stats'] = dict((k.replace('(Refereed)','').strip(),v) for d in data_dict for (k,v) in d.items() if '(Refereed)' in k and d['type'] in stats)
    reads = ['reads','downloads']
    doc['all reads'] = dict((k.replace('(Total)','').strip(),v) for d in data_dict for (k,v) in d.items() if '(Total)' in k and d['type'] in reads)
    doc['refereed reads'] = dict((k.replace('(Refereed)','').strip(),v) for d in data_dict for (k,v) in d.items() if '(Refereed)' in k and d['type'] in reads)
    doc['paper histogram'] = dict((k,v) for d in data_dict for (k,v) in d.items() if d['type'] == 'publication_histogram')
    doc['reads histogram'] = dict((k,v) for d in data_dict for (k,v) in d.items() if d['type'] == 'reads_histogram')
    doc['metrics series'] = dict((k,v) for d in data_dict for (k,v) in d.items() if d['type'] == 'metrics_series')
    a = dict((k,v) for d in data_dict for (k,v) in d.items() if d['type'] == 'all_citation_histogram')
    del a['type']
    b = dict((k,v) for d in data_dict for (k,v) in d.items() if d['type'] == 'refereed_citation_histogram')
    del b['type']
    c = dict((k,v) for d in data_dict for (k,v) in d.items() if d['type'] == 'non_refereed_citation_histogram')
    doc['citation histogram'] = dict((n, ":".join(["%s:%s"%(x,y) for (x,y) in zip(a[n],b[n])])) for n in set(a)|set(b))
    doc['citation histogram']['type'] = "citation_histogram"
    return doc

# General metrics engine
def generate_metrics(**args):
    # First we gather the necessary 'attributes' for all publications involved
    # (see above methods for more details)
    attr_list,num_cit,num_cit_ref = get_attributes(args)
    # What types of metrics are we gather (everything by default)
    stats_models = []
    # Retrieve which types of metrics are to be calculated
    model_types = args.get('types',current_app.config['METRICS_DEFAULT_MODELS'])
    # Instantiate the metrics classes, defined in the 'models' module
    for model_class in metricsmodels.data_models(models=model_types.split(',')):
        model_class.attributes = attr_list
        model_class.num_citing = num_cit
        model_class.num_citing_ref = num_cit_ref
        model_class.results = {}
        stats_models.append(model_class)
    # The metrics calculations are sent off in parallel
    po = Pool()
    rez = po.map_async(generate_data, stats_models)
    model_results = rez.get()
    # Now shape the results in the final format
    results = format_results(model_results)
    # Send the result back to our caller
    return results
