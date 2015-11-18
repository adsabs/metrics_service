from flask import current_app, request
from flask.ext.restful import Resource
from flask.ext.discoverer import advertise
from metrics import generate_metrics
import time

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
        stime = time.time()
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
            if 'query' in request.json and request.json['query']:
                current_app.logger.warning('Metrics requested, but both bibcodes and query specified!')
                return {'Error': 'Unable to get results!',
                        'Error Info': 'Cannot send both bibcodes and query'}, 403
            bibcodes = map(str, request.json['bibcodes'])
            current_app.logger.info('Metrics requested for %s bibcodes'%len(bibcodes))
            if len(bibcodes) > current_app.config.get('METRICS_MAX_SUBMITTED'):
                current_app.logger.warning('Metrics requested for %s bibcodes. Maximum is: %s!'%(len(bibcodes),current_app.config.get('METRICS_MAX_SUBMITTED')))
                return {'Error': 'Unable to get results!',
                        'Error Info': 'No results: number of submitted \
                         bibcodes exceeds maximum number'}, 403
            elif len(bibcodes) == 0:
                current_app.logger.warning('Metrics requested, but no bibcodes supplied!')
                return {'Error': 'Unable to get results!',
                        'Error Info': 'No bibcodes found in POST body'}, 403
            elif len(bibcodes) == 1:
                current_app.logger.debug('Metrics requested for single record')
                if len(types) > 0:
                    types = [t for t in types if t in ['basic', 'citations', 'histograms']]
                if len(types) == 0:
                    types=['basic', 'citations', 'histograms']
                if len(histograms) > 0:
                    histograms = [h for h in histograms if h in ['reads', 'citations']]
                if len(histograms) == 0:
                    histograms=['reads', 'citations']
        elif 'query' in request.json:
            query = request.json['query']
            current_app.logger.info('Metrics requested for query: %s'%query)
        else:
            return {'Error': 'Unable to get results!',
                    'Error Info': 'Nothing to calculate metrics!'}, 403
        results = generate_metrics(
            bibcodes=bibcodes, query=query, tori=include_tori,
            types=types, histograms=histograms)
        # If the results contain an error message something went boink
        if "Error" in results:
            current_app.logger.error('Metrics request request blew up')
            return results, 500
        # otherwise we have real results or an empty dictionary
        if results:
            duration = time.time() - stime
            current_app.logger.info('Metrics request successfully completed in %s real seconds'%duration)
            return results
        else:
            current_app.logger.info('Metrics request returned empty result')
            return {'Error': 'Unable to get results!',
                    'Error Info': 'No data available to generate metrics'}, 200


class PubMetrics(Resource):

    """Get metrics for a single publication (identified by its bibcode)"""
    scopes = []
    rate_limit = [1000, 60 * 60 * 24]
    decorators = [advertise('scopes', 'rate_limit')]

    def get(self, bibcode):
        results = generate_metrics(bibcodes=[bibcode],
                                   types=['basic', 'citations', 'histograms'],
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
