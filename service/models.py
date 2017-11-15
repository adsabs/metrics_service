'''
Created on April 9, 2015

@author: ehenneken
'''
from flask import current_app, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.result import ResultProxy
import sys

db = SQLAlchemy()

# A class to help bind in raw SQL queries


class Bind(object):

    def __init__(self, bind_key):
        self.bind = db.get_engine(current_app, bind_key)

    def execute(self, query, params=None):
        results = db.session.execute(query, params, bind=self.bind)
        # Create a list of results
        res = [r for r in results]
        # Commit the transaction to the database
        db.session.commit()
        # and close the connection
        if isinstance(results, ResultProxy):
            results.close()
        # Return the ResultProxy object
        return res

class MetricsModel(db.Model):
    __tablename__ = 'metrics'
    __bind_key__ = 'metrics'
    id = Column(Integer, primary_key=True)
    bibcode = Column(String, nullable=False, index=True, unique=True)
    
    an_citations = Column(postgresql.REAL)
    an_refereed_citations = Column(postgresql.REAL)
    author_num = Column(Integer, default=1)
    citations = Column(postgresql.ARRAY(String), default=[])
    citation_num = Column(Integer, default=0)
    downloads = Column(postgresql.ARRAY(Integer),default=[])
    reads = Column(postgresql.ARRAY(Integer), default=[])
    refereed = Column(Boolean, default=False)
    refereed_citations = Column(postgresql.ARRAY(String), default=[])
    refereed_citation_num = Column(Integer, default=0)
    reference_num = Column(Integer, default=0)
    rn_citations = Column(postgresql.REAL)
    rn_citation_data = Column(postgresql.JSON)
    modtime = Column(DateTime)
    

def get_identifiers(bibcodes):
    bibstr = ",".join(map(lambda a: "\'%s\'" % a, bibcodes))
    rawSQL = "SELECT id,bibcode,refereed FROM metrics WHERE \
              bibcode = ANY (ARRAY[%s]) ORDER BY citation_num DESC"
    SQL = rawSQL % bibstr
    db.metrics = Bind('metrics')
    results = db.metrics.execute(SQL)
    # For compatibility with unittests
    try:
        res = [(r[1], r[0], r[2]) for r in results]
    except:
        res = [(r.bibcode, r.id, r.refereed) for r in results]
    return res

def get_basic_stats_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,reads,downloads,author_num FROM \
              metrics WHERE id = ANY (VALUES %s)"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    res = db.metrics.execute(SQL)
    return res


def get_publication_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,author_num FROM metrics \
              WHERE id = ANY (VALUES %s)"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    res = db.metrics.execute(SQL)
    return res


def get_citation_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,citation_num,refereed_citation_num,\
              author_num FROM metrics WHERE id = ANY (VALUES %s) AND \
              citation_num <> 0 ORDER BY citation_num DESC"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    res = db.metrics.execute(SQL)
    return res


def get_citations(IDs, no_zero=True):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    if no_zero:
        rawSQL = "SELECT bibcode,refereed,citations,refereed_citations,author_num \
              FROM metrics WHERE id = ANY (VALUES %s) AND citation_num <> 0"
    else:
        rawSQL = "SELECT bibcode,refereed,citations,refereed_citations,author_num \
              FROM metrics WHERE id = ANY (VALUES %s)"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    res = db.metrics.execute(SQL)
    return res


def get_indicator_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,citation_num FROM metrics \
              WHERE id = ANY (VALUES %s) AND citation_num <> 0 \
              ORDER BY citation_num DESC"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    res = db.metrics.execute(SQL)
    return res


def get_usage_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,reads,downloads,author_num \
              FROM metrics WHERE id = ANY (VALUES %s) \
              AND array_length(reads, 1) > 0"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    res = db.metrics.execute(SQL)
    return res


def get_tori_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT id,bibcode,refereed,rn_citation_data,author_num \
              FROM metrics WHERE id = ANY (VALUES %s) \
              AND citation_num <> 0"
    SQL = rawSQL % IDstr
    db.metrics = Bind('metrics')
    res = db.metrics.execute(SQL)
    return res
