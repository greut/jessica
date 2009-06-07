#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import unittest

from webtest import TestApp
from mock import Mock

from jessica import JessicaMiddleware


class JessicaMock(JessicaMiddleware):
    """A fake Jessica that doesn't require a running AMQP server
    to be runned; sent messages are stored into `msgs`.
    """
    def __init__(self, *args, **kwargs):
        super(JessicaMock, self).__init__(*args, **kwargs)
        self.msgs = []

    def basic_publish(self, msg, exchange):
        self.msgs.append((exchange, msg))

    def connect(self):
        self.chan = Mock()
        self.chan.basic_publish = self.basic_publish

    def __del__(self):
        pass


class TestJessica(unittest.TestCase):
    @staticmethod
    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        environ['Jessica'].append(['Test', 'Hello, World!'])
        return ['Hello, world!']

    @staticmethod
    def app2(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        environ['Jessica'].append(('Test', 'Hello, World!'))
        environ['Jessica'].append(('Test', 'Hallo!'))
        return ['Hello, world!']

    def testInit(self):
        JessicaMock(lambda args: args)

    def testSend(self):
        mock = JessicaMock(self.app)
        app = TestApp(mock)
        res = app.get('/')
        assert mock.msgs[0][0] == 'Test'
        assert mock.msgs[0][1].body == 'Hello, World!'
        assert res.body == 'Hello, world!'
    
    def testPickle(self):
        mock = JessicaMock(self.app, {'pickle': True})
        
        app = TestApp(mock)
        res = app.get('/')
        
        assert len(mock.msgs) == 1
        assert mock.msgs[0][0] == 'Test'
        assert pickle.loads(mock.msgs[0][1].body) =='Hello, World!'
    
    def testDurable(self):
        mock = JessicaMock(self.app, {'durable': True})
        
        app = TestApp(mock)
        res = app.get('/')
        assert len(mock.msgs) == 1
        assert mock.msgs[0][0] == 'Test'
        assert mock.msgs[0][1].properties['delivery_mode'] == 2

    def testMultiple(self):
        mock = JessicaMock(self.app2)

        app = TestApp(mock)
        res = app.get('/')
        assert len(mock.msgs) == 2
        assert mock.msgs[1][1].body == 'Hallo!'


if __name__ == '__main__':
    unittest.main()

