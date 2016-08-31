import os
# Specify token needed to query the API
METRICS_API_TOKEN = None
# Specify the maximum number of bibcodes allowed to get metrics for
METRICS_MAX_SUBMITTED = 3000
# Specify the maximum number of bibcodes allowed for simple metrics
METRICS_MAX_SIMPLE = 1000
# Specify endpoint for Solr queries
METRICS_SOLRQUERY_URL = 'https://api.adsabs.harvard.edu/v1/search/query'
# Specify where the metrics database lives
SQLALCHEMY_BINDS = {
    'metrics': 'postgresql+psycopg2://user:pwd@localhost:5432/metrics'}
# We don't use thise SQLAlchemy functionality
# see: http://stackoverflow.com/questions/33738467/sqlalchemy-who-needs-sqlalchemy-track-modifications
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Proper handling of database connections
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
# In what environment are we?
ENVIRONMENT = os.getenv('ENVIRONMENT', 'staging').lower()
# Config for logging
METRICS_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s\t%(process)d '
                      '[%(asctime)s]:\t%(message)s',
            'datefmt': '%m/%d/%Y %H:%M:%S',
        }
    },
    'handlers': {
        'file': {
            'formatter': 'default',
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/tmp/metrics_service.app.{}.log'.format(ENVIRONMENT),
        },
        'console': {
            'formatter': 'default',
            'level': 'INFO',
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
# Define the autodiscovery endpoint
DISCOVERER_PUBLISH_ENDPOINT = '/resources'
# Advertise its own route within DISCOVERER_PUBLISH_ENDPOINT
DISCOVERER_SELF_PUBLISH = False
