# -*- coding: utf-8 -*-
from collections import defaultdict
from fnmatch import fnmatch
import logging
import time
import uuid

from requests.structures import CaseInsensitiveDict
from requests.compat import str


try:  # pragma: no cover
    import asyncio
    from asyncio.queues import Queue
except ImportError:  # pragma: no cover
    import trollius as asyncio  # NOQA
    from trollius.queues import Queue  # NOQA

EOL = '\r\n'


class IdGenerator(object):

    instances = []

    def __init__(self, prefix):
        self.instances.append(self)
        self.prefix = prefix
        self.uid = str(uuid.uuid4())
        self.generator = self.get_generator()

    def get_generator(self):
        i = 0
        j = 1
        while True:
            i += 1
            yield self.prefix + '/' + self.uid + '/' + str(j) + '/' + str(i)
            if i > 10000:  # pragma: no cover
                j += 1
                i = 0

    @classmethod
    def reset(cls, uid=None):
        for instance in cls.instances:
            if uid:
                instance.uid = uid
            instance.generator = instance.get_generator()

    def __call__(self):
        return next(self.generator)


class Action(dict):
    """Dict like object to handle actions. Generate action ids for you:

    ..
        >>> IdGenerator.reset('myuuid')

    .. code-block:: python

        >>> action = Action({'Action': 'Status'})
        >>> print(action) # doctest: +NORMALIZE_WHITESPACE
        Action: Status
        ActionID: action/myuuid/1/1
    """

    action_id_generator = IdGenerator('action')

    def __init__(self, *args, **kwargs):
        self.as_list = kwargs.pop('as_list', False)
        super(Action, self).__init__(*args, **kwargs)
        if 'ActionID' not in self:
            self['ActionID'] = self.action_id_generator()
        self.responses = []
        self.future = asyncio.Future()

    @property
    def id(self):
        return self['ActionID']

    def __str__(self):
        action = [': '.join(i) for i in sorted(self.items())]
        action.append(EOL)
        return EOL.join(action)

    @property
    def multi(self):
        if self.as_list:
            return True
        elif 'Start' in self.responses[0].headers.get('SubEvent', ''):
            return True
        elif 'will follow' in self.responses[0].headers.get('Message', ''):
            return True
        elif 'Complete' in self.responses[0].headers.get('Event', ''):
            return True
        return False

    @property
    def completed(self):
        print(self.responses)
        if 'Complete' in self.responses[-1].headers.get('Event', ''):
            return True
        elif not self.multi:
            return True
        return False

    def add_message(self, message):
        self.responses.append(message)
        if self.completed:
            if self.multi:
                self.future.set_result(self.responses)
            else:
                self.future.set_result(self.responses[0])
            return True


class Command(Action):
    """Dict like object to handle actions. Generate action ids for you:

    ..
        >>> IdGenerator.reset('myuuid')

    .. code-block:: python

        >>> command = Command({'Command' : 'Do something'})
        >>> print(command) # doctest: +NORMALIZE_WHITESPACE
        Action: AGI
        ActionID: action/myuuid/1/1
        Command: Do something
        CommandID: command/myuuid/1/1
    """

    command_id_generator = IdGenerator('command')

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        if 'Action' not in self:
            self['Action'] = 'AGI'
        if 'CommandID' not in self:
            self['CommandID'] = self.command_id_generator()

    @property
    def id(self):
        return self['CommandID']


class Message(object):
    """Handle both Responses and Events with the same api:

    ..
        >>> resp = Message('response', 'Response body',
        ...                {'Response': 'Follows'})
        >>> event = Message('event', '',
        ...                {'Event': 'MeetmeEnd', 'Meetme': '4242'})

    Responses:

    .. code-block:: python

        >>> print(resp.message_type)
        response
        >>> bool(resp.success)
        True
        >>> resp.headers
        {'Response': 'Follows'}
        >>> print(resp.content)
        Response body
        >>> for line in resp.iter_lines():
        ...     print(resp.content)
        Response body

    Events:

    .. code-block:: python

        >>> print(event.message_type)
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

    def __init__(self, message_type, content, headers=None, matches=None):
        self.message_type = message_type
        self.content = content
        self.headers = CaseInsensitiveDict(headers)
        self.manager = self.name = None,
        self.matches = matches
        if self.message_type == 'event':
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
        if self.message_type == 'event':
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
        return '<{0} headers:{1} content:"{2}">'.format(
            self.message_type.title(), self.headers, self.content)

    def iter_lines(self):
        """Iter over response body"""
        for line in self.content.split('\n'):
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
                message_type = 'event'
                name = mlines[0].split(': ', 1)[1]
                matches = []
                for pattern in patterns:
                    if fnmatch(name, pattern):
                        matches.append(pattern)
                if not matches and not mlines[-1].startswith('ActionID: '):
                    return
            else:
                message_type = 'response'
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
            return cls(message_type, content, headers, matches=matches)


class Connection(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.closed = False
        self.queue = Queue()
        self.responses = {}
        self.commands = {}
        self.factory = None
        self.log = logging.getLogger(__name__)

    def send(self, data, as_list=False):
        if not isinstance(data, Action):
            if 'Command' in data:
                klass = Command
            else:
                klass = Action
            data = klass(data, as_list=as_list)
        self.transport.write(str(data).encode('utf8'))
        self.responses[data.id] = data
        return data.future

    def data_received(self, data):
        encoding = getattr(self, 'encoding', 'ascii')
        data = data.decode(encoding, 'ignore')
        # Very verbose, uncomment only if necessary
        # self.log.debug('data received: "%s"', data)
        if not self.queue.empty():
            data = self.queue.get_nowait() + data
        lines = data.split(EOL+EOL)
        self.queue.put_nowait(lines.pop(-1))
        for line in lines:
            # Because sometimes me receive only one EOL from Asterisk
            line = line.strip()
            # Very verbose, uncomment only if necessary
            # self.log.debug('message received: "%s"', line)
            obj = Message.from_line(line, self.factory.callbacks)
            self.log.debug('message interpreted: %r', obj)
            if obj is None:
                continue

            response = None
            if 'CommandID' in obj.headers:
                response = self.responses.get(obj.headers['CommandID'])
            if response is None and 'ActionID' in obj.headers:
                response = self.responses.get(obj.headers['ActionID'])

            if response is not None:
                if response.add_message(obj):
                    # completed; dequeue
                    self.responses.pop(response.id)
            elif obj.message_type == 'event':
                self.factory.dispatch(obj, obj.matches)

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
            self.responses = self.protocol.responses = {}
            if 'username' in self.config:
                action = Action({
                    'Action': 'Login',
                    'Username': self.config['username'],
                    'Secret': self.config['secret']})
                self.protocol.send(action)
            self.loop.call_later(10, self.ping)

    def ping(self):  # pragma: no cover
        self.protocol.send({'Action': 'Ping'})
        self.loop.call_later(10, self.ping)

    def send_action(self, action, as_list=False, **kwargs):
        """
            Send an action to the server via manager::

            :param action: an Action or dict with action name and parameters to
                           send
            :type action: Action or dict
            :param as_list: If action send multiple responses, retrieve all
                            responses via future
            :type as_list: boolean
            :return: a Future will receive the response
            :rtype: asyncio.Future

            :Example:

                    manager = Manager()
                    resp = manager.send_action({'Action': 'Status'})

                To retrieve answer in a coroutine:

                    manager = Manager()
                    resp = yield from manager.send_action(
                        {'Action': 'Status'})

                With a callback:

                    manager = Manager()
                    future = manager.send_action(
                        {'Action': 'Status'})
                    future.add_done_callback(handle_status_response)

                See https://wiki.asterisk.org/wiki/display/AST/AMI+Actions for
                more
                information on actions
        """
        action.update(kwargs)
        return self.protocol.send(action, as_list=as_list)

    def send_command(self, command, agi=False, as_list=False):
        """Send a command action to the server::

            manager = Manager()
            resp = manager.send_command('http show status')

        Return a response :class:`Message`.
        See https://wiki.asterisk.org/wiki/display/AST/ManagerAction_Command
        """
        if agi:
            action = Command({'Command': command, 'Action': 'AGI'},
                             as_list=True)
        else:
            action = Action({'Command': command, 'Action': 'Command'},
                            as_list=as_list)
        return self.send_action(action)

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
        return t

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
