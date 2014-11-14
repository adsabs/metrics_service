import os
from flask import Flask, g
from views import blueprint, Resources, Metrics, PubMetrics
from flask.ext.restful import Api
from client import Client

def create_app():
  api = Api(blueprint)
  api.add_resource(Resources, '/resources')
  api.add_resource(Metrics, '/')
  api.add_resource(PubMetrics, '/<string:bibcode>')

  app = Flask(__name__, static_folder=None)
  app.url_map.strict_slashes = False
  app.config.from_object('metrics.config')
  try:
    app.config.from_object('metrics.local_config')
  except ImportError:
    pass
  app.register_blueprint(blueprint)
  app.client = Client(app.config['CLIENT'])
  return app
