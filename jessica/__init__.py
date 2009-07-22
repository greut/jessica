# -*- coding: utf-8 -*-

VERSION = (0, 1, 1)
__author__ = "Yoan Blanc <yoan@dosimple.ch>"
__license__ = "BSD"

import logging

from amqplib import client_0_8 as amqp

try:
    import cPickle as pickle
except ImportError, e:
    import pickle


CONFIG = {"host": "localhost:5672",
          "userid": "guest",
          "password": "guest",
          "virtual_host": "/",
          "ssl": False,
          "insist": False,
          "durable": False,
          "pickle": False}


log = logging.getLogger("Jessica")


class Jessica(object):

    def __init__(self, config=None, **kwargs):
        if config is None:
            config = {}
        config = dict(CONFIG, **config)
        config.update(kwargs)
        log.debug("Config is: %s" % config)

        self.config = config

        self.connect()

    def __del__(self):
        log.info("Disconnecting from %(host)s" % self.config)
        self.chan.close()
        self.conn.close()

    def connect(self):
        log.info("Connecting to %(host)s" % self.config)
        self.conn = amqp.Connection(**self.config)
        self.chan = self.conn.channel()

    def build_message(self, message, durable=None, pickled=None, **kwargs):
        if durable is None:
            durable = self.config["durable"]
            if durable is True:
                kwargs["delivery_mode"] = 2

        if pickled is None:
            pickled = self.config["pickle"]

        if pickled:
            log.info("Message is pickled")
            message = pickle.dumps(message)

        msg = amqp.Message(message, **kwargs)

        return msg

    def send(self, exchange, message, **kwargs):
        log.info("Sending message to %s: %s" % (exchange,
                                                repr(message)))

        msg = self.build_message(message, **kwargs)

        self.chan.basic_publish(msg, exchange=exchange)


class JessicaMiddleware(Jessica):
    """WSGI Middleware that intercept messages posted into environ["Jessica"]
    and send them via AMQP"""

    def __init__(self, application, config=None, **kwargs):
        super(JessicaMiddleware, self).__init__(config, **kwargs)
        self.application = application

    def __call__(self, environ, start_response):
        environ["Jessica"] = []
        app_iter = self.application(environ, start_response)
        for exchange, message in environ["Jessica"]:
            self.send(exchange, message)
        for data in app_iter:
            yield data
        if hasattr(app_iter, "close"):
            app_iter.close()
