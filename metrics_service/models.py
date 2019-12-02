'''
Created on April 9, 2015

@author: ehenneken
'''
from flask import current_app, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.result import ResultProxy
from sqlalchemy.ext.declarative import declarative_base
import sys
import psycopg2

Base = declarative_base()

class MetricsModel(Base):
    __tablename__ = 'metrics'
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

def execute_SQL_query(query):
    with current_app.session_scope() as session:
        results = session.execute(query).fetchall()
        return results

def get_identifiers(bibcodes):
    bibstr = ",".join(map(lambda a: "\'%s\'" % a, bibcodes))
    rawSQL = "SELECT id,bibcode,refereed FROM metrics WHERE \
              bibcode = ANY (ARRAY[%s]) ORDER BY citation_num DESC"
    SQL = rawSQL % bibstr
    results = execute_SQL_query(SQL)
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
    results = execute_SQL_query(SQL)
    return results


def get_publication_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,author_num FROM metrics \
              WHERE id = ANY (VALUES %s)"
    SQL = rawSQL % IDstr
    results = execute_SQL_query(SQL)
    return results


def get_citation_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,citation_num,refereed_citation_num,\
              author_num FROM metrics WHERE id = ANY (VALUES %s) AND \
              citation_num <> 0 ORDER BY citation_num DESC"
    SQL = rawSQL % IDstr
    results = execute_SQL_query(SQL)
    return results


def get_citations(IDs, no_zero=True):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    if no_zero:
        rawSQL = "SELECT bibcode,refereed,citations,refereed_citations,author_num \
              FROM metrics WHERE id = ANY (VALUES %s) AND citation_num <> 0"
    else:
        rawSQL = "SELECT bibcode,refereed,citations,refereed_citations,author_num \
              FROM metrics WHERE id = ANY (VALUES %s)"
    SQL = rawSQL % IDstr
    results = execute_SQL_query(SQL)
    return results


def get_indicator_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,citation_num FROM metrics \
              WHERE id = ANY (VALUES %s) AND citation_num <> 0 \
              ORDER BY citation_num DESC"
    SQL = rawSQL % IDstr
    results = execute_SQL_query(SQL)
    return results


def get_usage_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT bibcode,refereed,reads,downloads,author_num \
              FROM metrics WHERE id = ANY (VALUES %s) \
              AND array_length(reads, 1) > 0"
    SQL = rawSQL % IDstr
    results = execute_SQL_query(SQL)
    return results


def get_tori_data(IDs):
    IDstr = ",".join(map(lambda a: "(%s)" % a, IDs))
    rawSQL = "SELECT id,bibcode,refereed,rn_citation_data,author_num \
              FROM metrics WHERE id = ANY (VALUES %s) \
              AND citation_num <> 0"
    SQL = rawSQL % IDstr
    results = execute_SQL_query(SQL)
    return results

def get_citations_single(bibcode):
    SQL = "SELECT citations, refereed_citations, reads, downloads FROM metrics WHERE bibcode = '%s'" % bibcode
    results = execute_SQL_query(SQL)
    return results
