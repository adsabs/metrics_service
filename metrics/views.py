from flask import current_app, Blueprint, request
from flask.ext.restful import Resource
import time
import inspect
import sys

from utils.metrics import generate_metrics

blueprint = Blueprint(
      'metrics',
      __name__,
      static_folder=None,
)

class Metrics(Resource):
    """computes all metrics on the POST body"""
    scopes = []
    def post(self):
        if not request.json or not 'bibcodes' in request.json:
            return {'msg': 'no bibcodes found in POST body'}, 400
        bibcodes = map(str, request.json['bibcodes'])
        if len(bibcodes) > current_app.config['MAX_INPUT']:
            return {'msg': 'number of submitted bibcodes exceeds maximum number'}, 400
        try:
            results = generate_metrics(bibcodes=bibcodes)
        except Exception, err:
            return {'msg': 'Unable to get results! (%s)' % err}, 500

        return results

class PubMetrics(Resource):
    """Get metrics for a single publication (identified by its bibcode)"""
    scopes = []
    def get(self, bibcode):
       try:
           results = generate_metrics(bibcodes=[bibcode], types='statistics,histograms')
       except Exception, err:
           return {'msg': 'Unable to get results! (%s)' % err}, 500
       return results

class Resources(Resource):
  '''Overview of available resources'''
  scopes = []
  rate_limit = [1000,60*60*24]
  def get(self):
    func_list = {}

    clsmembers = [i[1] for i in inspect.getmembers(sys.modules[__name__], inspect.isclass)]
    for rule in current_app.url_map.iter_rules():
      f = current_app.view_functions[rule.endpoint]
      #If we load this webservice as a module, we can't guarantee that current_app only has these views
      if not hasattr(f,'view_class') or f.view_class not in clsmembers:
        continue
      methods = f.view_class.methods
      scopes = f.view_class.scopes
      rate_limit = f.view_class.rate_limit
      description = f.view_class.__doc__
      func_list[rule.rule] = {'methods':methods,'scopes': scopes,'description': description,'rate_limit':rate_limit}
    return func_list, 200
