LOG_STDOUT = True
# Specify token needed to query the API
METRICS_API_TOKEN = None
# Specify the maximum number of bibcodes allowed to get metrics for
METRICS_MAX_SUBMITTED = 3000
# Specify the maximum number of bibcodes allowed for simple metrics
METRICS_MAX_SIMPLE = 1000
# Specify the maximum number of bibcodes allowed for individual metrics
METRICS_MAX_DETAIL = 6000
# Specify where the metrics database lives
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://user:pwd@localhost:5432/metrics'
SQLALCHEMY_ECHO = False
# We don't use thise SQLAlchemy functionality
# see: http://stackoverflow.com/questions/33738467/sqlalchemy-who-needs-sqlalchemy-track-modifications
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Proper handling of database connections
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
# Define the autodiscovery endpoint
DISCOVERER_PUBLISH_ENDPOINT = '/resources'
# Advertise its own route within DISCOVERER_PUBLISH_ENDPOINT
DISCOVERER_SELF_PUBLISH = False
