'''
Created on Oct 29, 2014

@author: ehenneken
'''
import sys
import os
from multiprocessing import Process, Queue, cpu_count
import simplejson as json
from database import db, AlchemyEncoder, MetricsModel

class PostgresQueryError(Exception):
    pass

class MetricsDataHarvester(Process):
    """
    Class to allow parallel retrieval of citation data from Mongo
    """
    def __init__(self, task_queue, result_queue):
        Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.session = db.session
    def run(self):
        while True:
            bibcode = self.task_queue.get()
            if bibcode is None:
                break
            try:
                result = self.session.query(MetricsModel).filter(MetricsModel.bibcode==bibcode).one()
                metr_data = json.dumps(result, cls=AlchemyEncoder)
                self.result_queue.put(json.loads(metr_data))
            except Exception, e:
                sys.stderr.write("Postgres metrics data query for %s blew up (%s)" % (bibcode,e))
                self.result_queue.put("Exception! Bibcode: %s" % bibcode)
        return

def get_metrics_data(**args):
    """
    Method to prepare the actual citation dictionary creation
    """
    # create the queues
    tasks = Queue()
    results = Queue()
    # how many threads are there to be used
    threads = args.get('threads',cpu_count())
    # get the bibcodes for which to get metrics data
    bibcodes = args.get('bibcodes',[])
    # initialize the "harvesters" (each harvester get the metrics data for a bibcode)
    harvesters = [ MetricsDataHarvester(tasks, results) for i in range(threads)]
    # start the harvesters
    for b in harvesters:
        b.start()
    # put the bibcodes in the tasks queue
    num_jobs = 0
    for bib in bibcodes:
        tasks.put(bib)
        num_jobs += 1
    # add some 'None' values at the end of the tasks list, to faciliate proper closure
    for i in range(threads):
        tasks.put(None)
    # gather all results into one metrics data dictionary
    metrics_data_dict = {}
    while num_jobs:
        data = results.get()
        if 'Exception' in data:
            num_jobs -= 1
            continue
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
        num_jobs -= 1
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
