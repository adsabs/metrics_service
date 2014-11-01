import os

_basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

APP_NAME = "metrics"

class AppConfig(object):
    
    RESOURCES = [
                    {
                        '/metrics/': {
                            'allowed': ['POST',],
                            'scope': 'oauth:metrics:read', #this is an arbitrary string, and adsws will take care of this, but this lets each app decide which permissions adsws should enforce
                            'description': 'computes all metrics on the POST body',
                            } 
                    },
                    {
                        '/metrics/<string:bibcode>': {
                            'allowed':['GET',],
                            'scope':'oauth:metrics:read',
                            'description': 'Get metrics for a single publication (identified by its bibcode)',
                            }
                    },
                    {
                        '/resources': {
                            'allowed':['GET',],
                            'scope':'oauth:resources:read',
                            'description': 'Get this overview',
                            }
                    },
                ]
    SQLALCHEMY_DATABASE_URI = ''
    METRICS_DEFAULT_MODELS = 'statistics,histograms,metrics,series'
    
try:
    from local_config import LocalConfig
except ImportError:
    LocalConfig = type('LocalConfig', (object,), dict())
    
for attr in filter(lambda x: not x.startswith('__'), dir(LocalConfig)):
    setattr(AppConfig, attr, LocalConfig.__dict__[attr])
    
config = AppConfig
