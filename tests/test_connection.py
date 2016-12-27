import pytest
import asyncio
from panoramisk import Manager
from panoramisk import utils
from panoramisk.actions import Action


def message(msg):
    EOL = utils.EOL.encode('utf8')
    return EOL.join([l.strip() for l in msg.strip().split(b'\n')]) + EOL + EOL


def login(action_id):
    return message(b'''
    Response: Success
    ActionID: ''' + action_id.encode('utf8') + b'''
    Message: Authentication accepted
    ''')


def resp(action_id):
    return message(b'''
    Response: Success
    ActionID: ''' + action_id.encode('utf8') + b'''
    Message: Resp
    ''')


def pong(action_id):
    return message(b'''
    Response: Success
    ActionID: ''' + action_id.encode('utf8') + b'''
    Ping: Pong
    Timestamp: 1409169929.412068
    ''')


class Event:

    def __init__(self, event):
        self.event = event


class _Asterisk(asyncio.Protocol):

    def connection_made(self, transport):
        self.uuid = transport.get_extra_info('peername')
        self.transport = transport
        self.factory.clients[self.uuid] = self
        if not self.factory.started.done():
            self.factory.started.set_result(True)

    def data_received(self, data):
        data = data.decode('utf8')
        data = data.split(utils.EOL + utils.EOL)
        if data:
            if not self.factory._data_received.done():
                self.factory._data_received.set_result(True)
        for line in data:
            if not line.strip():
                continue
            a = Action()
            for kv in line.split('\n'):
                if ':' in kv:
                    k, v = kv.split(':', 1)
                    a[k] = v.strip()
            self.factory.actions.append(a)
            print(repr(a))  # debug
            if 'action' in a:
                if a['action'] == 'Login':
                    message = login(a['actionid'])
                elif a['action'] == 'Ping':
                    message = pong(a['actionid'])
                else:
                    message = resp(a['actionid'])
                print(repr(message))  # debug
                self.transport.write(message)


class Asterisk(object):

    clients = {}

    def __init__(self, loop, port):
        self.loop = loop
        self.port = port
        self.protocol = None

    @property
    def client(self):
        return list(self.clients.values())[0]

    @asyncio.coroutine
    def start(self):
        self.actions = []
        self.clients = {}
        self.started = asyncio.Future()
        self._data_received = asyncio.Future()
        self.protocol = _Asterisk()
        self.protocol.factory = self
        yield from self.loop.create_server(
            lambda: self.protocol, '127.0.0.1', self.port)
        return self.started

    @asyncio.coroutine
    def data_received(self):
        self._data_received = asyncio.Future()
        return self._data_received

    @asyncio.coroutine
    def stop(self):
        for client in self.clients.values():
            client.transport.close()


@pytest.mark.asyncio
def test_reconnection_without_lost(event_loop, unused_tcp_port_factory):
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
    yield from server.data_received()
    login = server.actions[0]
    assert login['action'] == 'Login'
    unused_tcp_port = unused_tcp_port_factory()

    print('Restart server on %s' % unused_tcp_port)
    server.port = unused_tcp_port
    manager.config['port'] = unused_tcp_port
    yield from server.stop()

    manager.send_action({'Action': 'Ping'})
    f = manager.send_action({'Action': 'Test', 'Command': 'test'})
    fully_booted = Event('FullyBooted')

    yield from asyncio.sleep(.1)
    assert manager.awaiting_actions
    yield from server.start()
    yield from asyncio.sleep(2)
    assert manager.awaiting_actions
    manager.dispatch(fully_booted)
    yield from asyncio.sleep(.5)
    assert not manager.awaiting_actions
    resp = yield from f
    yield from server.stop()

    login2 = server.actions[0]
    assert login2['action'] == 'Login'
    assert login['actionid'] != login2['actionid']

    test_action = server.actions[-1]
    assert test_action.id == resp.id
    assert test_action['action'] == 'Test'

