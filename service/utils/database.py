'''
Created on April 9, 2015

@author: ehenneken
'''
from flask import current_app, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects import postgresql

db = SQLAlchemy()

# A class to help bind in raw SQL queries
class Bind(object):
    def __init__(self, bind_key):
        self.bind = db.get_engine(current_app, bind_key)
    def execute(self, query, params=None):
        return db.session.execute(query, params, bind=self.bind)

class MetricsModel(db.Model):
  __tablename__='metrics'
  __bind_key__ ='metrics'
  id = Column(Integer,primary_key=True)
  bibcode = Column(String,nullable=False,index=True)
  refereed = Column(Boolean)
  rn_citations = Column(postgresql.REAL)
  rn_citation_data = Column(postgresql.JSON)
  downloads = Column(postgresql.ARRAY(Integer))
  reads = Column(postgresql.ARRAY(Integer))
  an_citations = Column(postgresql.REAL)
  refereed_citation_num = Column(Integer)
  citation_num = Column(Integer)
  reference_num= Column(Integer)
  citations = Column(postgresql.ARRAY(String))
  refereed_citations = Column(postgresql.ARRAY(String))
  author_num = Column(Integer)
  an_refereed_citations = Column(postgresql.REAL)
  modtime = Column(DateTime)

def get_identifiers(bibcodes):
    bibstr = ",".join(map(lambda a: "\'%s\'"%a,bibcodes))
    rawSQL = "SELECT id,bibcode FROM metrics WHERE bibcode = ANY (ARRAY[%s]) ORDER BY citation_num DESC"
    SQL = rawSQL % bibstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    return dict([(r.bibcode,r.id) for r in results])

def get_basic_stats_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)"%a,IDs))
    rawSQL = "SELECT bibcode,refereed,reads,downloads,author_num FROM metrics WHERE id = ANY (VALUES %s)"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    res = [r for r in results]
    return res

def get_publication_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)"%a,IDs))
    rawSQL = "SELECT bibcode,refereed,author_num FROM metrics WHERE id = ANY (VALUES %s)"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    res = [r for r in results]
    return res

def get_citation_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)"%a,IDs))
    rawSQL = "SELECT bibcode,refereed,citation_num,refereed_citation_num,author_num FROM metrics WHERE id = ANY (VALUES %s) AND citation_num <> 0 ORDER BY citation_num DESC"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    res = [r for r in results]
    return res

def get_citations(IDs):
    IDstr = ",".join(map(lambda a: "(%s)"%a,IDs))
    rawSQL = "SELECT bibcode,refereed,citations,refereed_citations,author_num FROM metrics WHERE id = ANY (VALUES %s) AND citation_num <> 0"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    res = [r for r in results]
    return res

def get_indicator_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)"%a,IDs))
    rawSQL = "SELECT bibcode,refereed,citation_num FROM metrics WHERE id = ANY (VALUES %s) AND citation_num <> 0 ORDER BY citation_num DESC"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    res = [r for r in results]
    return res

def get_usage_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)"%a,IDs))
    rawSQL = "SELECT bibcode,refereed,reads,downloads,author_num FROM metrics WHERE id = ANY (VALUES %s) AND array_length(reads, 1) > 0"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    res = [r for r in results]
    return res

def get_tori_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)"%a,IDs))
    rawSQL = "SELECT id,bibcode,refereed,rn_citation_data,author_num FROM metrics WHERE id = ANY (VALUES %s) AND citation_num <> 0"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    res = [r for r in results]
    return res
