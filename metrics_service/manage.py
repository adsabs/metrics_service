from __future__ import absolute_import
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
#from models import db
from .app import create_app

app_ = create_app()

#app_.config.from_pyfile('config.py')
#try:
#    app_.config.from_pyfile('local_config.py')
#except IOError:
#    pass

#migrate = Migrate(app_, db)
manager = Manager(app_)

manager.add_command('db', MigrateCommand)

@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app_.wsgi_app = ProfilerMiddleware(app_.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app_.run()

if __name__ == '__main__':
    manager.run()
