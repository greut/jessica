"""
WSGI/PasteDeploy application bootstrap module.
"""
from jessica import JessicaMiddleware

def make_filter(global_conf, **app_conf):
    """
    PasteDeploy WSGI application factory.

    Called by PasteDeply (or a compatable WSGI application host) to create the
    whut WSGI application.
    """
    pickled = app_conf.get("pickled") == "True"
    durable = app_conf.get("durable") == "True"
    dummy = app_conf.get("dummy") == "True"
    
    def filter(app):
        return JessicaMiddleware(app,
                                 pickled=pickled,
                                 durable=durable,
                                 dummy=dummy)
    return filter

