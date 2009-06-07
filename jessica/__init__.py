# -*- coding: utf-8 -*-

VERSION = (0, 1, 0)
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
        logging.info("Disconnecting from %(host)s" % self.config)
        self.chan.close()
        self.conn.close()

    def connect(self):
        logging.info("Connecting to %(host)s" % self.config)
        self.conn = amqp.Connection(**self.config)
        self.chan = self.conn.channel()

    def build_message(self, message):
        if self.config["pickle"]:
            log.info("Message is pickled")
            message = pickle.dumps(message)

        msg = amqp.Message(message)

        if self.config["durable"]:
            log.info("Message is durable")
            msg.properties["delivery_mode"] = 2

        return msg

    def send(self, exchange, message):
        logging.info("Sending message to %s: %s" % (exchange,
                                                    repr(message)))

        msg = self.build_message(message)

        self.chan.basic_publish(msg, exchange=exchange)


class JessicaMiddleware(Jessica):
    """WSGI Middleware that intercept messages posted into environ["Jessica"]
    and send them via AMQP
    """
    def __init__(self, application, config=None, **kwargs):
        super(JessicaMiddleware, self).__init__(config, **kwargs)
        self.application = application

    def __call__(self, environ, start_response):
        environ["Jessica"] = []
        response = self.application(environ, start_response)
        for exchange, message in environ["Jessica"]:
            self.send(exchange, message)
        return response
