# -*- coding: utf-8 -*-
"""
    wsgi
    ~~~~

    entrypoint wsgi script
"""

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from service import app as metrics

application = DispatcherMiddleware(metrics.create_app(), mounts={})

if __name__ == "__main__":
    run_simple('0.0.0.0', 4000, application, use_reloader=False,
               use_debugger=True)
