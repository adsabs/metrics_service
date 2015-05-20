METRICS_SECRET_KEY = 'this should be changed'
METRICS_MAX_SUBMITTED = 1000
METRICS_CHUNK_SIZE = 1000
METRICS_MAX_HITS = 100000
METRICS_SOLRQUERY_URL = 'https://api.adsabs.harvard.edu/v1/search/query'
SQLALCHEMY_BINDS = {
    'metrics': 'postgresql+psycopg2://user:pwd@localhost:5432/metrics'}
# Define the autodiscovery endpoint
DISCOVERER_PUBLISH_ENDPOINT = '/resources'
# Advertise its own route within DISCOVERER_PUBLISH_ENDPOINT
DISCOVERER_SELF_PUBLISH = False
