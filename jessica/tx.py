from twisted.internet import reactor, defer, protocol
from twisted.python import log

from txamqp.spec import load
from txamqp.client import TwistedDelegate
from txamqp.protocol import AMQClient
from txamqp.content import Content


class TwistedJessica(AMQClient):
    """AMQP Client for Twisted, use send_message"""

    spec = "specs/amqp0-8.xml"
    auth = {"LOGIN": "guest",
            "PASSWORD": "guest"}
    host = "localhost"
    port = 5672

    def __init__(self, exchange, durable=False):
        self.exchange = exchange
        self.durable = durable
        self._queue = defer.DeferredQueue()
        self.start()

    def __repr__(self):
        return "<%s (%s)>" % (self.__class__.__name__, self.exchange)

    @defer.inlineCallbacks
    def errConnection(self, *args):
        log.err(args)

    @defer.inlineCallbacks
    def gotConnection(self, conn):
        yield conn.start(self.auth)
        self._chan = chan = yield conn.channel(1)
        yield chan.channel_open()

        try:
            yield self._queue.get().addCallback(self._send_message)
        except Exception, e:
            log.err(e)
            log.err(str(e))


        yield chan.channel_close()
        chan0 = yield conn.channel(0)
        yield chan0.connection_close()

    def _send_message(self, message):
        msg = Content(message)
        
        if self.durable:
            msg["delivery_mode"] = 2

        self._chan.basic_publish(exchange=self.exchange,
                                 content=msg,
                                 routing_key="")

        return self._queue.get().addCallback(self._send_message)

    def send_message(self, message):
        self._queue.put(message)

    def start(self):
        spec = load(self.spec)

        delegate = TwistedDelegate()
        self.client = protocol.ClientCreator(
            reactor,
            AMQClient,
            delegate=delegate,
            vhost="/",
            spec=spec).connectTCP(self.host,
                                  self.port)

        self.client.addCallback(self.gotConnection)
        self.client.addErrback(self.errConnection)
