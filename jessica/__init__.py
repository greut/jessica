# -*- coding: utf-8 -*-

VERSION = (0, 1, 2)
__author__ = "Yoan Blanc <yoan@dosimple.ch>"
__license__ = "BSD"

import logging

from socket import error
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
          "pickled": False,
          "dummy": False}


log = logging.getLogger("Jessica")


class Jessica(object):

    def __init__(self, config=None, **kwargs):
        if config is None:
            config = {}
        config = dict(CONFIG, **config)
        config.update(kwargs)
        log.debug("Config is: %s" % config)

        self.config = config
        self.queue = []
        
        if not self.config["dummy"]:
            self.connect()

    def __del__(self):
        if hasattr(self, "chan"):
            self.chan.close()
            self.conn.close()

    def connect(self):
        log.info("Connecting to %(host)s" % self.config)
        self.conn = amqp.Connection(**self.config)
        self.chan = self.conn.channel()

        while len(self.queue):
            exchange, queue, kwargs = self.queue.pop()
            self.send(exchange, queue, **kwargs)

    def build_message(self, message, durable=None, pickled=None, **kwargs):
        if durable is None:
            durable = self.config["durable"]
            if durable is True:
                kwargs["delivery_mode"] = 2

        if pickled is None:
            pickled = self.config["pickled"]

        if pickled:
            log.info("Message is pickled")
            message = pickle.dumps(message)

        return amqp.Message(message, **kwargs)

    def send(self, exchange, message, **kwargs):
        log.info("Sending message to %s: %s" % (exchange,
                                                repr(message)))

        if not self.config["dummy"]:
            msg = self.build_message(message, **kwargs)
            try:
                self.chan.basic_publish(msg, exchange=exchange)
            except error, e:
                log.error(e)
                self.queue.push((exchange, message, kwargs))
                self.connect()


class JessicaMiddleware(Jessica):
    """WSGI Middleware that intercept messages posted into environ["Jessica"]
    and send them via AMQP"""

    def __init__(self, application, config=None, **kwargs):
        super(JessicaMiddleware, self).__init__(config, **kwargs)
        self.application = application

    def __call__(self, environ, start_response):
        environ["Jessica"] = []
        app_iter = self.application(environ, start_response)
 
        for data in app_iter:
            yield data
        if hasattr(app_iter, "close"):
            app_iter.close()
        
        for exchange, message in environ["Jessica"]:
            self.send(exchange, message)
