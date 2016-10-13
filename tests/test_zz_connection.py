# -*- coding: utf-8 -*-
import pytest
import asyncio
from panoramisk import Manager
from panoramisk import utils
from panoramisk.actions import Action

EOL = utils.EOL.encode('utf8')


def login(action_id):
    return b'''
    Response: Success
    ActionID: ''' + action_id.encode('utf8') + '''
    Message: Authentication accepted
    '''.strip() + EOL + EOL


class _Asterisk(asyncio.Protocol):

    clients = {}

    def connection_made(self, transport):
        print(self)
        self.actions = []
        self.uuid = transport.get_extra_info('peername')
        self.transport = transport
        self.factory.clients[self.uuid] = self
        self.factory.started.set_result(True)

    def data_received(self, data):
        if not self.factory.data_received.done():
            self.factory.data_received.set_result(True)
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
                    message = login(a['actionid'])
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
        self.started = asyncio.Future()
        self.data_received = asyncio.Future()
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
    yield from server.data_received
    login = server.client.actions[0]
    assert login['action'] == 'Login'
    unused_tcp_port = unused_tcp_port_factory()
    print('Restart server on %s' % unused_tcp_port)
    server.port = unused_tcp_port
    manager.config['port'] = unused_tcp_port
    yield from server.stop()
    yield from server.start()
    yield from server.data_received
    login2 = server.client.actions[0]
    yield from server.stop()
    assert login2['action'] == 'Login'
    assert login['actionid'] != login2['actionid']
