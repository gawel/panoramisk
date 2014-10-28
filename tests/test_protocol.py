# -*- coding: utf-8 -*-
from panoramisk.utils import asyncio
from panoramisk import testing
import pytest


@pytest.fixture
def conn(request):

    def callback(*args):
        pass

    manager = testing.Manager()
    manager.register_event('Peer*', callback)
    return manager.protocol


def test_received(conn):
    conn.data_received(b'Event: None\r\n\r\n')
    conn.data_received(b'Event: PeerStatus\r\nPeer: gawel\r\n\r\n')
    conn.data_received(b'Response: Follows\r\nPeer: gawel\r\n\r\n')
    conn.data_received(b'Response: Success\r\nPing: Pong\r\n\r\n')


def test_send(conn):
    assert isinstance(conn.send({}), asyncio.Future)
