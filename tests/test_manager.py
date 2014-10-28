# -*- coding: utf-8 -*-
from unittest import TestCase
import os
from panoramisk import testing
from panoramisk import message
from panoramisk.utils import asyncio

try:
    from unittest import mock
except ImportError:
    import mock


class TestManager(TestCase):

    defaults = dict(
        async=False, testing=True,
        loop=asyncio.get_event_loop()
    )

    test_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def callFTU(self, stream=None, **config):
        if stream:
            config['stream'] = os.path.join(self.test_dir, stream)
        manager = testing.Manager(**config)
        return manager

    def test_connection(self):
        manager = self.callFTU(loop=None)
        self.assertTrue(manager.connect())
        self.assertTrue('bla')

    def test_ping(self):
        manager = self.callFTU(stream='ping.yaml')
        future = manager.send_action({'Action': 'Ping'})
        self.assertIn('ping', future.result().lheaders)

    def test_queue_status(self):
        manager = self.callFTU(stream='queue_status.yaml')
        future = manager.send_action({'Action': 'QueueStatus',
                                      'Queue': 'xxxxxxxxxxxxxxxx-tous'})
        responses = future.result()
        self.assertEqual(len(responses), 9)

    def test_get_variable(self):
        manager = self.callFTU(stream='get_variable.yaml')
        future = manager.send_action({'Command': 'GET VARIABLE "PEERNAME"'})
        responses = future.result()
        self.assertEqual(len(responses), 2)

    def test_close(self):
        manager = self.callFTU()
        manager.close()

    def test_events(self):
        future = asyncio.Future()

        def callback(event, manager):
            future.set_result(event)

        manager = self.callFTU(use_http=True, url='http://host')
        manager.register_event('Peer*', callback)
        event = message.Message.from_line('Event: PeerStatus',
                                          manager.callbacks)
        self.assertTrue(event.success)
        self.assertEqual(event['Event'], 'PeerStatus')
        self.assertIn('Event', event)
        manager.dispatch(event, event.matches)
        self.assertTrue(event is future.result())

        event = message.Message.from_line('Event: NoPeerStatus',
                                          manager.callbacks)
        self.assertTrue(event is None)


class TestProtocol(TestCase):

    def callback(*args):
        pass

    def callFTU(self):
        conn = testing.Connection()
        manager = testing.Manager()
        manager.register_event('Peer*', self.callback)
        manager.loop = asyncio.get_event_loop()
        conn.connection_made(mock.MagicMock())
        conn.factory = manager
        return conn

    def test_received(self):
        conn = self.callFTU()
        conn.data_received(b'Event: None\r\n\r\n')
        conn.data_received(b'Event: PeerStatus\r\nPeer: gawel\r\n\r\n')
        conn.data_received(b'Response: Follows\r\nPeer: gawel\r\n\r\n')
        conn.data_received(b'Response: Success\r\nPing: Pong\r\n\r\n')

    def test_send(self):
        conn = self.callFTU()
        self.assertTrue(isinstance(conn.send({}), asyncio.Future))