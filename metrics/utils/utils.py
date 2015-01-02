'''
Created on Oct 29, 2014

@author: ehenneken
'''
import sys
import os
import simplejson as json
from sqlalchemy import or_

from database import db, AlchemyEncoder, MetricsModel

class PostgresQueryError(Exception):
    pass

def get_metrics_data(**args):
    """
    Method to prepare the actual citation dictionary creation
    """
    bibcodes = args.get('bibcodes',[])
    metrics_data_dict = {}
    querydata = []
    for bibcode in bibcodes:
        querydata.append(MetricsModel.bibcode=='%s'%bibcode)
    condition = or_(*querydata)
    results = db.session.query(MetricsModel).filter(condition).all()
    for result in results:
        mdata = json.dumps(result, cls=AlchemyEncoder)
        data = json.loads(mdata)
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
