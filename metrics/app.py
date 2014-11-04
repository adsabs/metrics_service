import os
from flask import Flask, g
from views import blueprint, Resources, UnixTime, Metrics, PubMetrics
from flask.ext.restful import Api

def create_app():
  api = Api(blueprint)
  api.add_resource(Resources, '/resources')
  api.add_resource(UnixTime, '/time')
  api.add_resource(Metrics, '/metrics')
  api.add_resource(PubMetrics, '/metrics/<string:bibcode>')

  app = Flask(__name__, static_folder=None)
  app.url_map.strict_slashes = False
  app.config.from_object('metrics.config')
  try:
    app.config.from_object('metrics.local_config')
  except ImportError:
    pass
  app.register_blueprint(blueprint)
  return app
