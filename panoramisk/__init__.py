# -*- coding: utf-8 -*-
from requests.auth import HTTPDigestAuth
from requests.structures import CaseInsensitiveDict
from requests.compat import str
from collections import defaultdict
from fnmatch import fnmatch
import requests
import logging
import time
import uuid

try:  # pragma: no cover
    import asyncio
    from asyncio.queues import Queue
except ImportError:  # pragma: no cover
    import trollius as asyncio  # NOQA
    from trollius.queues import Queue  # NOQA

EOL = '\r\n'


def action_id():
    uid = str(uuid.uuid4())
    i = 0
    j = 1
    while True:
        i += 1
        yield uid + '/' + str(j) + '/' + str(i)
        if i > 10000:  # pragma: no cover
            j += 1
            i = 0


class Action(dict):
    """Dict like object to handle actions. Generate action ids for you:

    .. code-block:: python

        >>> action = Action({'Action': 'Status'})
        >>> print(action)
        Action: Status
        ActionID: .../1/13
    """

    action_id = action_id()

    @property
    def id(self):
        if 'ActionID' not in self:
            self['ActionID'] = next(self.action_id)
        return self['ActionID']

    def __str__(self):
        if 'ActionID' not in self:
            self['ActionID'] = next(self.action_id)
        action = [': '.join(i) for i in sorted(self.items())]
        action.append(EOL)
        return EOL.join(action)


class Message(object):
    """Handle both Responses and Events with the same api:

    ..
        >>> resp = Message('response', 'Response body',
        ...                {'Response': 'Follows'})
        >>> event = Message('event', '',
        ...                {'Event': 'MeetmeEnd', 'Meetme': '4242'})

    Responses:

    .. code-block:: python

        >>> print(resp.type)
        response
        >>> bool(resp.success)
        True
        >>> resp.headers
        {'Response': 'Follows'}
        >>> print(resp.text)
        Response body
        >>> for line in resp.iter_lines():
        ...     print(resp.text)
        Response body

    Events:

    .. code-block:: python

        >>> print(event.type)
        event
        >>> print(event.name)
        MeetmeEnd
        >>> print(event['meetme'])
        4242
        >>> print(event.meetme)
        4242
        >>> print(event.unknown_header)
        None

    """

    def __init__(self, type, content, headers=None, matches=None):
        self.type = type
        self.text = content
        self.headers = CaseInsensitiveDict(headers)
        self.manager = self.name = None,
        self.matches = matches
        if self.type == 'event':
            self.name = self.headers['event']
        self.orig = None

    @property
    def success(self):
        """return True if a response status is Success or Follows:

        .. code-block:: python

            >>> resp = Message('response', '', {'Response': 'Success'})
            >>> print(resp.success)
            Success
            >>> resp.headers['Response'] = 'Failed'
            >>> resp.success
            False
        """
        if self.type == 'event':
            return True
        status = self.headers['response']
        if status in ('Success', 'Follows'):
            return 'Success'
        return False

    def __getitem__(self, attr):
        return self.headers[attr]

    def __getattr__(self, attr):
        return self.headers.get(attr, None)

    def __contains__(self, value):
        return value in self.headers

    def __repr__(self):
        return '<{0} {1}>'.format(
            self.type.title(), self.headers)

    def iter_lines(self):
        """Iter over response body"""
        for line in self.text.split('\n'):
            yield line

    @property
    def lheaders(self):
        """return headers with lower keys:

        .. code-block:: python

            >>> resp = Message('response', '', {'Ping': 'Pong'})
            >>> print(resp.lheaders)
            {'ping': 'Pong'}
        """
        h = {}
        for k, v in self.headers.items():
            h[k.lower()] = v
        return h

    @classmethod
    def from_line(cls, line, patterns=None):
            mlines = line.split(EOL)
            headers = CaseInsensitiveDict()
            content = ''
            if mlines[0].startswith('Event: '):
                type = 'event'
                name = mlines[0].split(': ', 1)[1]
                matches = []
                for pattern in patterns:
                    if fnmatch(name, pattern):
                        matches.append(pattern)
                if not matches:
                    return
            else:
                type = 'response'
                matches = []
                has_body = ('Response: Follows', 'Response: Fail')
                if mlines[0].startswith(has_body):
                    content = mlines.pop()
                    while not content and mlines:
                        content = mlines.pop()
            for mline in mlines:
                if ': ' in mline:
                    k, v = mline.split(': ', 1)
                    if k in headers:
                        o = headers.setdefault(k, [])
                        if not isinstance(o, list):
                            o = [o]
                        o.append(v)
                        headers[k] = o
                    else:
                        headers[k] = v
            return cls(type, content, headers, matches=matches)


class Connection(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.closed = False
        self.queue = Queue()
        self.log = logging.getLogger(__name__)

    def data_received(self, data):
        encoding = getattr(self, 'encoding', 'ascii')
        data = data.decode(encoding, 'ignore')
        if not self.queue.empty():
            data = self.queue.get_nowait() + data
        lines = data.split(EOL+EOL)
        self.queue.put_nowait(lines.pop(-1))
        for line in lines:
            obj = Message.from_line(line, self.factory.callbacks)
            self.log.debug('data_received: %r', obj)
            if obj is None:
                continue
            if obj.type == 'event':
                self.factory.dispatch(obj, obj.matches)
            else:
                if obj.headers.get('Ping'):
                    continue
                self.responses.put_nowait(obj)

    def send(self, data):
        if not isinstance(data, Action):
            data = Action(data)
        self.transport.write(str(data).encode('utf8'))
        self.log.debug('send: %r', data)
        return data

    def connection_lost(self, exc):  # pragma: no cover
        if not self.closed:
            self.close()
            # wait a few before reconnect
            time.sleep(2)
            # reconnect
            self.factory.connect()

    def close(self):  # pragma: no cover
        if not self.closed:
            try:
                self.transport.close()
            finally:
                self.closed = True


class Manager(object):
    """Main object:

    .. code-block:: python

        manager = Manager(
            host='127.0.0.1',
            port=5038,
            ssl=False,
            encoding='utf8',
            loop=None,
        )
    """

    defaults = dict(
        host='127.0.0.1',
        port=5038,
        ssl=False,
        encoding='utf8',
        connection_class=Connection,
        loop=None,
    )

    def __init__(self, **config):
        self.config = dict(self.defaults, **config)
        self.loop = self.config['loop']
        self.log = config.get('log', logging.getLogger(__name__))
        self.callbacks = defaultdict(list)
        self.protocol = None
        self.http = None

    def connection_made(self, f):
        if getattr(self, 'protocol', None):
            self.protocol.close()
        try:
            transport, protocol = f.result()
        except OSError as e:  # pragma: no cover
            self.log.exception(e)
            self.loop.call_later(2, self.connect)
        else:
            self.log.info('Manager connected')
            self.protocol = protocol
            self.protocol.queue = Queue(loop=self.loop)
            self.protocol.factory = self
            self.protocol.log = self.log
            self.protocol.config = self.config
            self.protocol.encoding = self.encoding = self.config['encoding']
            self.responses = self.protocol.responses = Queue(loop=self.loop)
            if 'username' in self.config:
                action = Action({
                    'Action': 'Login',
                    'Username': self.config['username'],
                    'Secret': self.config['secret']})
                self.protocol.send(action)
            action = Action({'Command': 'http show status',
                             'Action': 'Command'})
            self.protocol.send(action)
            if 'url' not in self.config:
                # alway use http for now
                self.parse_http_config()
            self.loop.call_later(10, self.ping)

    def ping(self):  # pragma: no cover
        self.protocol.send({'Action': 'Ping'})
        self.loop.call_later(10, self.ping)

    def parse_http_config(self, future=None):  # pragma: no cover
        def recall():
            asyncio.Task(
                self.responses.get(), loop=self.loop
            ).add_done_callback(self.parse_http_config)
        if future is None:
            return recall()
        if 'use_http' not in self.config:
            resp = future.result()
            if 'HTTP Server Status:' not in resp.text:
                return recall()
            host, port, path = None, None, None
            for line in resp.iter_lines():
                if line.startswith('Server Enabled and Bound to'):
                    host = line.split(' ')[-1]
                    host, port = host.split(':')
                    if self.config['host'] == '127.0.0.1':
                        # allow ssh tunnels
                        host = '127.0.0.1'
                    self.config.update(
                        host=host,
                        http_port=port)
                elif '/arawman' in line:
                    path = True
                    break
            if host and port and path:
                self.config['use_http'] = 'true'

        if self.config.get('use_http', 'false') in ('true', True):
            self.config.setdefault('protocol', 'http')
            self.config['url'] = (
                '{protocol}://{host}:{http_port}/arawman'
            ).format(**self.config)
            self.log.info('Using http interface at %s', self.config['url'])

    def send_action_via_http(self, action, **kwargs):
        retries = kwargs.pop('_retries', 0)
        if 'url' not in self.config:
            return Message('response',
                           'No url available to perform the request (yet?)',
                           headers={'Response': 'Failed'})
        if self.http is None:
            self.http = requests.Session()
        if 'username' in self.config:
            auth = (self.config['username'], self.config['secret'])
            auth = HTTPDigestAuth(*auth)
            self.http.auth = auth
        try:
            resp = self.http.get(self.config['url'], params=action)
        except Exception as e:  # pragma: no cover
            self.log.exception(e)
            self.http = None
            if not retries:
                kwargs['_retries'] = 1
                return self.send_action_via_http(action, **kwargs)
            raise
        else:
            msg = Message.from_line(resp.text)
            msg.orig = resp
            return msg

    def send_action_via_manager(self, action, callback=None, **kwargs):
        self.protocol.send(Action(action, **kwargs))
        task = asyncio.Task(self.responses.get(self.loop), self.loop)
        if callback:
            task.add_done_callback(callback)
        return task

    def send_action(self, action, **kwargs):
        """Send an action to the server::

            >>> manager = Manager()
            >>> resp = manager.send_action({'Action': 'Status'})

        Return a response :class:`Message`.

        See https://wiki.asterisk.org/wiki/display/AST/AMI+Actions for more
        information on actions
        """
        if 'callback' in kwargs:
            return self.send_action_via_manager(action, **kwargs)
        action.update(**kwargs)
        return self.send_action_via_http(action)

    def send_command(self, command):
        """Send a command action to the server::

            >>> manager = Manager()
            >>> resp = manager.send_command('http show status')

        Return a response :class:`Message`.
        See https://wiki.asterisk.org/wiki/display/AST/ManagerAction_Command
        """
        action = Action({'Command': command, 'Action': 'Command'})
        res = self.send_action(action)
        return res

    def connect(self, loop=None):
        """connect to the server"""
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
        t = asyncio.Task(
            self.loop.create_connection(
                self.config['connection_class'],
                self.config['host'], self.config['port'],
                ssl=self.config['ssl']),
            loop=self.loop)
        t.add_done_callback(self.connection_made)
        return self.loop

    def register_event(self, pattern, callback):
        """register an event. See :class:`Message`:

        .. code-block:: python

            >>> def callback(event, manager):
            ...     print(event, manager)
            >>> manager = Manager()
            >>> manager.register_event('Meetme*', callback)
        """
        self.callbacks[pattern].append(callback)

    def dispatch(self, event, matches):
        event.manager = self
        for pattern in matches:
            for callback in self.callbacks[pattern]:
                for callback in self.callbacks[pattern]:
                    callback(event, self)

    def close(self):
        """Close the connection"""
        if getattr(self, 'protocol', None):
            self.protocol.close()
