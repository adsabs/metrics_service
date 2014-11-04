from flask import current_app
from flask.ext.restful import Resource
import time

from metrics_utils import generate_metrics

class Metrics(Resource):
    """computes all metrics on the POST body"""
    scopes = 'oauth:metrics:read'
    def post(self):
        if not request.json or not 'bibcodes' in request.json:
            return {'msg': 'no bibcodes found in POST body'}, 400
        bibcodes = map(lambda a: str(a), request.json['bibcodes'])
        print bibcodes
        try:
            results = generate_metrics(bibcodes=bibcodes)
        except Exception, err:
            return {'msg': 'Unable to get results! (%s)' % err}, 500

        return results

class PubMetrics(Resource):
    """Get metrics for a single publication (identified by its bibcode)"""
    scopes = 'oauth:metrics:read'
    def get(self, bibcode):
       try:
           results = generate_metrics(bibcodes=[bibcode])
       except Exception, err:
           return {'msg': 'Unable to get results! (%s)' % err}, 500
       return results

class Resources(Resource):
  '''Overview of available resources'''
  scopes = ['oauth:sample_application:read','oauth_sample_application:logged_in']
  def get(self):
    func_list = {}
    for rule in current_app.url_map.iter_rules():
      func_list[rule.rule] = {'methods':current_app.view_functions[rule.endpoint].methods,
                              'scopes': current_app.view_functions[rule.endpoint].view_class.scopes,
                              'description': current_app.view_functions[rule.endpoint].view_class.__doc__,
                              }
    return func_list, 200

class UnixTime(Resource):
  '''Returns the unix timestamp of the server'''
  scopes = ['oauth:sample_application:read','oauth_sample_application:logged_in']
  def get(self):
    return {'now': time.time()}, 200
