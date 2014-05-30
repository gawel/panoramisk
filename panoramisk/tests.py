# -*- coding: utf-8 -*-
from unittest import TestCase
import panoramisk

try:  # pragma: no cover
    import asyncio
except ImportError:  # pragma: no cover
    import trollius as asyncio  # NOQA

try:
    from unittest import mock
except ImportError:
    import mock


class TestManager(TestCase):

    defaults = dict(
        async=False, testing=True,
        loop=mock.MagicMock(),
    )

    def setUp(self):
        patcher = mock.patch('requests.Session.get')
        session_get = patcher.start()
        self.response = panoramisk.Message(
            'response', '', {'Response': 'Follows'})
        session_get.return_value = self.response
        self.addCleanup(patcher.stop)

    def callFTU(self, **config):
        manager = panoramisk.Manager(**dict(
            self.defaults,
            **config))
        if manager.loop:
            protocol = panoramisk.Connection()
            protocol.connection_made(mock.MagicMock())
            protocol.responses = mock.MagicMock()
            future = asyncio.Future()
            future.set_result((mock.MagicMock(), protocol))
            manager.protocol = protocol
            manager.connection_made(future)
        return manager

    def test_connection(self):
        manager = self.callFTU(loop=None)
        self.assertTrue(manager.connect())
        self.assertTrue('bla')

    def test_action(self):
        manager = self.callFTU(use_http=True, url='http://host',
                               username='user', secret='passwd')
        self.response.text = 'Response: Success\r\nPing: Pong'
        self.assertIn('ping', manager.send_action({'Action': 'Ping'}))
        self.assertIn('ping', manager.send_action({'Action': 'Ping'}).lheaders)

        self.response.text = 'Response: Follows\r\nPing: Pong'
        self.assertIn('Ping', manager.send_action({'Action': 'Ping'}).text)

        self.response.text = 'Response: Success\r\nPing: Pong\r\nPing: Pong'
        self.assertIn('Ping', manager.send_action({'Action': 'Ping'}))
        self.assertEqual(manager.send_action({'Action': 'Ping'})['Ping'],
                         ['Pong', 'Pong'])

        self.response.text = 'Response: Follows\r\ncommand'
        resp = manager.send_command({'Action': 'Ping'})
        self.response.text = 'Response: Follows\r\ncommand\r\n'
        resp = manager.send_command({'Action': 'Ping'})
        self.assertTrue(resp.success)
        self.assertIn('command', resp.text)

    def test_action_class(self):
        action = panoramisk.Action({'Action': 'Ping'})
        self.assertNotEqual(action.id, panoramisk.Action().id)
        self.assertIn('ActionID', str(action))
        self.assertIn('ActionID', str(panoramisk.Action()))

    def test_action_failed(self):
        manager = self.callFTU(use_http=True, url='http://host')
        self.response.text = 'Response: Failed\r\ncommand'
        action = panoramisk.Action({'Action': 'Ping'})
        resp = manager.send_command(action)
        self.assertFalse(resp.success)
        self.assertIn('command', resp.iter_lines())

    @mock.patch('panoramisk.tests.asyncio.Task')
    def test_action_via_manager(self, *args):
        def callback():
            return True
        manager = self.callFTU(use_http=True)
        manager.responses = mock.MagicMock()
        manager.send_action({'Action': 'Ping'},
                            callback=callback)

    def test_action_error(self):
        manager = self.callFTU(use_http=True)
        self.assertFalse(manager.send_action({'Action': 'Ping'}).success)

    def test_close(self):
        manager = self.callFTU(use_http=True, url='http://host')
        manager.close()

    def test_events(self):
        future = asyncio.Future()

        def callback(event, manager):
            future.set_result(event)

        manager = self.callFTU(use_http=True, url='http://host')
        manager.register_event('Peer*', callback)
        event = panoramisk.Message.from_line('Event: PeerStatus',
                                             manager.callbacks)
        self.assertTrue(event.success)
        self.assertEqual(event['Event'], 'PeerStatus')
        self.assertIn('Event', event)
        manager.dispatch(event, event.matches)
        self.assertTrue(event is future.result())

        event = panoramisk.Message.from_line('Event: NoPeerStatus',
                                             manager.callbacks)
        self.assertTrue(event is None)


class TestProtocol(TestCase):

    def callback(*args):
        pass

    def callFTU(self):
        conn = panoramisk.Connection()
        conn.responses = mock.MagicMock()
        manager = panoramisk.Manager()
        manager.register_event('Peer*', self.callback)
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
        self.assertTrue(isinstance(conn.send({}), panoramisk.Action))
