from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from models import db
from app import create_app

app_ = create_app()

app_.config.from_pyfile('config.py')
try:
    app_.config.from_pyfile('local_config.py')
except IOError:
    pass

migrate = Migrate(app_, db)
manager = Manager(app_)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
