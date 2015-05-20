from flask import current_app, Blueprint, request
from flask.ext.restful import Resource
from flask.ext.discoverer import advertise
import time
import inspect
import sys

from utils.metrics import generate_metrics

blueprint = Blueprint(
    'metrics',
    __name__,
    static_folder=None,
)

allowed_types = [
    'basic', 'citations', 'histograms', 'indicators', 'timeseries']
allowed_histograms = ['publications', 'reads', 'downloads', 'citations']


class Metrics(Resource):

    """computes metrics on the POST body"""
    scopes = []
    rate_limit = [1000, 60 * 60 * 24]
    decorators = [advertise('scopes', 'rate_limit')]

    def post(self):
        bibcodes = []
        query = None
        try:
            include_tori = request.json['tori']
        except:
            include_tori = True
        # Force that we either have a valid metrics type or all types
        try:
            types = [t for t in request.json['types'] if t in allowed_types]
        except:
            types = []
        types = types or allowed_types
        # Same with histogram type
        try:
            histograms = request.json['histograms']
        except:
            histograms = []
        histograms = histograms or allowed_histograms
        if 'bibcodes' in request.json:
            bibcodes = map(str, request.json['bibcodes'])
            if len(bibcodes) > current_app.config.get('METRICS_MAX_SUBMITTED'):
                return {'Error': 'Unable to get results!',
                        'Error Info': 'No results: number of submitted \
                         bibcodes exceeds maximum number'}, 200
            elif len(bibcodes) == 0:
                return {'Error': 'Unable to get results!',
                        'Error Info': 'No bibcodes found in POST body'}, 200
        elif 'query' in request.json:
            query = request.json['query']
        else:
            return {'Error': 'Unable to get results!',
                    'Error Info': 'Nothing to calculate metrics!'}, 200
        results = generate_metrics(
            bibcodes=bibcodes, query=query, tori=include_tori,
            types=types, histograms=histograms)
        # If the results contain an error message something went boink
        if "Error" in results:
            return results, 500
        # otherwise we have real results or an empty dictionary
        if results:
            return results
        else:
            return {'Error': 'Unable to get results!',
                    'Error Info': 'No data available to generate metrics'}, 200


class PubMetrics(Resource):

    """Get metrics for a single publication (identified by its bibcode)"""
    scopes = []
    rate_limit = [1000, 60 * 60 * 24]
    decorators = [advertise('scopes', 'rate_limit')]

    def get(self, bibcode):
        results = generate_metrics(bibcodes=[bibcode],
                                   types=['basic', 'histograms'],
                                   histograms=['reads', 'citations'])
        # If the results contain an error message something went boink
        if "Error" in results:
            return results, 500
        # otherwise we have real results or an empty dictionary
        if results:
            return results
        else:
            return {'Error': 'Unable to get results!',
                    'Error Info': 'No data available to generate metrics'}, 200
