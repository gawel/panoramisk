# -*- coding: utf-8 -*-
import pytest
import asyncio
from panoramisk import Manager
from panoramisk import utils
from panoramisk.actions import Action

EOL = utils.EOL.encode('utf8')

LOGIN = b'''
Response: Success
ActionID: %s
Message: Authentication accepted
'''.strip() + EOL + EOL


class _Asterisk(asyncio.Protocol):

    clients = {}

    def connection_made(self, transport):
        print(self)
        self.actions = []
        self.uuid = transport.get_extra_info('peername')
        self.factory.clients[self.uuid] = self
        self.transport = transport

    def data_received(self, data):
        data = data.decode('utf8')
        for line in data.split(utils.EOL + utils.EOL):
            a = Action()
            for kv in line.split(utils.EOL):
                if ':' in kv:
                    k, v = kv.split(':', 1)
                    a[k] = v.strip()
            self.actions.append(a)
            print(repr(a))  # debug
            if 'action' in a:
                if a['action'] == 'Login':
                    message = LOGIN % a['actionid'].encode('utf8')
                    self.transport.write(message)


class Asterisk(object):

    clients = {}

    def __init__(self, loop, port):
        self.data_received = []
        self.loop = loop
        self.port = port
        self.protocol = None

    @property
    def client(self):
        return list(self.clients.values())[0]

    @asyncio.coroutine
    def start(self):
        self.clients = {}
        self.protocol = _Asterisk()
        self.protocol.factory = self
        yield from self.loop.create_server(
            lambda: self.protocol, '127.0.0.1', self.port)
        return self.protocol

    @asyncio.coroutine
    def stop(self):
        for client in self.clients.values():
            client.transport.close()


@pytest.mark.asyncio
def test_basic_reconnection(event_loop, unused_tcp_port_factory):
    unused_tcp_port = unused_tcp_port_factory()
    print('Start server on %s' % unused_tcp_port)
    manager = Manager(loop=event_loop,
                      host='127.0.0.1',
                      port=unused_tcp_port,
                      username='user',
                      secret='secret')
    server = Asterisk(event_loop, unused_tcp_port)
    yield from server.start()
    yield from manager.connect()
    yield from asyncio.sleep(.1)
    login = server.client.actions[0]
    assert login['action'] == 'Login'
    unused_tcp_port = unused_tcp_port_factory()
    print('Restart server on %s' % unused_tcp_port)
    server.port = unused_tcp_port
    manager.config['port'] = unused_tcp_port
    yield from server.stop()
    yield from server.start()
    yield from asyncio.sleep(.1)
    yield from server.stop()
    login2 = server.client.actions[0]
    assert login2['action'] == 'Login'
    assert login['actionid'] != login2['actionid']
