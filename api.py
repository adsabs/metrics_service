import sys
from flask import Flask
from flask import request
from flask import jsonify
from flask import Blueprint
from flask.ext.restful import abort, Api, Resource
from config import config
from metrics_utils import generate_metrics

app_blueprint = Blueprint('api', __name__)
api = Api(app_blueprint)

class Metrics(Resource):

    def post(self):
        if not request.json or not 'bibcodes' in request.json:
            abort(400)
        bibcodes = map(lambda a: str(a), request.json['bibcodes'])

        try:
            results = generate_metrics(bibcodes=bibcodes)
        except Exception, err:
            sys.stderr.write('Unable to get results! (%s)' % err)
            abort(400)

        return jsonify(results)

    def get(self, bibcode):
       try:
           results = generate_metrics(bibcodes=[bibcode])
       except Exception, err:
            sys.stderr.write('Unable to get results! (%s)' % err)
            abort(400)
       return jsonify(results)

class Resources(Resource):
    def get(self):
      return config.RESOURCES
##
## Actually setup the Api resource routing here
##
api.add_resource(Metrics, '/metrics', '/metrics/<string:bibcode>')
api.add_resource(Resources, '/resources')

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(app_blueprint)
    app.run(debug=True)
