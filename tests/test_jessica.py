#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import unittest

from webtest import TestApp
from mock import Mock

from jessica import Jessica


class JessicaMock(Jessica):
    """A fake Jessica that doesn't require a running AMQP server
    to be runned; sent messages are stored into `msgs`."""

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

    def testInit(self):
        jessica = JessicaMock()
        assert jessica

    def testSend(self):
        mock = JessicaMock()
        mock.send('Test', 'Hello, World!')

        assert mock.msgs[0][0] == 'Test'
        assert mock.msgs[0][1].body == 'Hello, World!'

    def testPickle(self):
        mock = JessicaMock({'pickle': True})
        mock.send('Test', 'Hello, World!')

        assert len(mock.msgs) == 1
        assert mock.msgs[0][0] == 'Test'
        assert pickle.loads(mock.msgs[0][1].body) =='Hello, World!'

        mock = JessicaMock(pickle=True)
        mock.send('Test', 'Hello, World!')

        assert len(mock.msgs) == 1
        assert mock.msgs[0][0] == 'Test'
        assert pickle.loads(mock.msgs[0][1].body) =='Hello, World!'

    def testDurable(self):
        mock = JessicaMock({'durable': True})
        mock.send('Test', 'Hello, World!')

        assert len(mock.msgs) == 1
        assert mock.msgs[0][0] == 'Test'
        assert mock.msgs[0][1].properties['delivery_mode'] == 2

        mock = JessicaMock(durable=True)
        mock.send('Test', 'Hello, World!')

        assert mock.msgs[0][1].properties['delivery_mode'] == 2


if __name__ == '__main__':
    unittest.main()
