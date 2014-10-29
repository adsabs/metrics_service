import sys
from flask import Flask
from flask import request
from flask import jsonify
from flask.ext.restful import abort, Api, Resource
from config import config
from metrics_utils import generate_metrics

app = Flask(__name__)
api = Api(app)

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
##
## Actually setup the Api resource routing here
##
api.add_resource(Metrics, '/metrics')

if __name__ == '__main__':
    app.run(debug=True)