'''
Created on Oct 29, 2014

@author: ehenneken
'''
import sys
import os
import simplejson as json
from database import db

metrics_fields = ['id','bibcode','refereed','rn_citations','rn_citation_data','rn_citations_hist',
                   'downloads','reads','an_citations','refereed_citation_num','citation_num','citations',
                   'refereed_citations','author_num','an_refereed_citations']

def get_metrics_data(**args):
    """
    Method to prepare the actual citation dictionary creation
    """
    bibcodes = args.get('bibcodes',[])
    metrics_data_dict = {}
    SQL = "SELECT * FROM metrics WHERE bibcode IN (%s)" % ",".join(map(lambda a: "\'%s\'"%a,bibcodes))
    results = db.session.execute(SQL)
    for result in results:
        data = {}
        for field in metrics_fields:
            data[field] = result[metrics_fields.index(field)]
        try:
            rn_citations, rn_hist, n_self = remove_self_citations(bibcodes,data)
            data['rn_citations'] = rn_citations
            data['rn_citations_hist'] = rn_hist
            data['number_of_self_citations'] = n_self
        except:
            pass
        try:
            metrics_data_dict[data['bibcode']] = data
        except:
            pass

    return metrics_data_dict

def remove_self_citations(biblist,datadict):
    # Remove all the entries in "datadict['rn_citation_data']" where the bibcode is
    # in the supplied list of bibcodes
    result = filter(lambda a: a['bibcode'] not in biblist, datadict['rn_citation_data'])
    Nself  = len(filter(lambda a: a['bibcode'] in biblist, datadict['rn_citation_data']))
    rn_hist = {}
    for item in result:
        try:
            rn_hist[item['bibcode'][:4]] += item['ref_norm']
        except:
            rn_hist[item['bibcode'][:4]] = item['ref_norm']

    # Now we can aggregate the individual contributions to the overall normalized count
    return sum(map(lambda a: a['ref_norm'], result)), rn_hist, Nself
