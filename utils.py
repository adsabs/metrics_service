'''
Created on Oct 29, 2014

@author: ehenneken
'''

# general module imports
import sys
import os
from multiprocessing import Process, Queue, cpu_count
import simplejson as json
# modules for querying PostgreSQL
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
# local imports
from config import config

__all__ = ['get_metrics_data']

class PostgresQueryError(Exception):
    pass

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

Base = declarative_base()

class MetricsModel(Base):
  __tablename__='metrics'

  id = Column(Integer,primary_key=True)
  bibcode = Column(String,nullable=False,index=True)
  refereed = Column(Boolean)
  rn_citations = Column(postgresql.REAL)
  rn_citation_data = Column(postgresql.JSON)
  rn_citations_hist = Column(postgresql.JSON)
  downloads = Column(postgresql.ARRAY(Integer))
  reads = Column(postgresql.ARRAY(Integer))
  an_citations = Column(postgresql.REAL)
  refereed_citation_num = Column(Integer)
  citation_num = Column(Integer)
  citations = Column(postgresql.ARRAY(String))
  refereed_citations = Column(postgresql.ARRAY(String))
  author_num = Column(Integer)
  an_refereed_citations = Column(postgresql.REAL)
  modtime = Column(DateTime)

class MetricsDataHarvester(Process):
    """
    Class to allow parallel retrieval of citation data from Mongo
    """
    def __init__(self, task_queue, result_queue):
        Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(engine)
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()
    def run(self):
        while True:
            bibcode = self.task_queue.get()
            if bibcode is None:
                break
            try:
                result = self.session.query(MetricsModel).filter(MetricsModel.bibcode==bibcode).one()
                metr_data = json.dumps(result, cls=AlchemyEncoder)
                self.result_queue.put(json.loads(metr_data))
            except PostgresQueryError, e:
                sys.stderr.write("Postgres metrics data query for %s blew up (%s)" % (bibcode,e))
                raise
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
