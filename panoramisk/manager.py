# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
import re
import fnmatch
from .ami_protocol import AMIProtocol
from .utils import asyncio
from . import actions
from . import utils
from . import errors


class Manager(object):
    """Main object:

    .. code-block:: python

        >>> manager = Manager(
        ...    host='127.0.0.1',
        ...    port=5038,
        ...    ssl=False,
        ...    encoding='utf8')
    """

    defaults = dict(
        host='127.0.0.1',
        port=5038,
        events='on',
        ssl=False,
        encoding='utf8',
        protocol_factory=AMIProtocol,
        save_stream=None,
        loop=None,
        automatic_reconnection=True,
        auto_ping=True,
    )

    def __init__(self, **config):
        self.config = dict(self.defaults, **config)
        self.loop = self.config['loop']
        self.log = config.get('log', logging.getLogger(__name__))
        self.callbacks = defaultdict(list)
        self.protocol = None
        self.patterns = []
        self.save_stream = self.config.get('save_stream')
        self.authenticated = False
        self.authenticated_future = None
        self.pinger = None
        self.responses = {}
        self.waiting_actions = utils.Queue()

    def connection_made(self, f):
        if getattr(self, 'protocol', None):
            self.protocol.close()
        try:
            transport, protocol = f.result()
        except OSError as e:  # pragma: no cover
            self.log.error('Impossible to connect: %s', str(e.args))
            if self.config['automatic_reconnection']:
                self.log.info('Try to connect again in 2 seconds')
                self.loop.call_later(2, self.connect)
        else:
            self.log.debug('Manager connected')
            self.protocol = protocol
            self.protocol.queue = utils.Queue(loop=self.loop)
            self.protocol.factory = self
            self.protocol.log = self.log
            self.protocol.config = self.config
            self.protocol.encoding = self.encoding = self.config['encoding']
            if 'username' in self.config:
                self.authenticated = False
                self.authenticated_future = self.send_action({
                    'Action': 'Login',
                    'Username': self.config['username'],
                    'Secret': self.config['secret'],
                    'Events': self.config['events']})
                self.authenticated_future.add_done_callback(self.login)
            self.log.debug('username not in config file')
            self.pinger = self.loop.call_later(10, self.ping)

    def login(self, future):
        self.authenticated_future = None
        resp = future.result()
        self.authenticated = bool(resp.success)
        if self.authenticated:
            while not self.waiting_actions.empty():
                action = self.waiting_actions.get_nowait()
                self.send_action(action)
            if self.config['auto_ping']:
                self.pinger = self.loop.call_later(10, self.ping)
        return self.authenticated

    def ping(self):  # pragma: no cover
        self.pinger = self.loop.call_later(10, self.ping)
        self.send_action({'Action': 'Ping'})

    def send_action(self, action, as_list=False, **kwargs):
        """Send an :class:`~panoramisk.actions.Action` to the server:

        :param action: an Action or dict with action name and parameters to
                       send
        :type action: Action or dict or Command
        :param as_list: If True, the action Future will retrieve all responses
        :type as_list: boolean
        :return: a Future that will receive the response
        :rtype: asyncio.Future

        :Example:

        To retrieve answer in a coroutine::

            manager = Manager()
            resp = yield from manager.send_action({'Action': 'Status'})

        With a callback::

            manager = Manager()
            future = manager.send_action({'Action': 'Status'})
            future.add_done_callback(handle_status_response)

        See https://wiki.asterisk.org/wiki/display/AST/AMI+Actions for
        more information on actions
        """
        action.update(kwargs)
        if not isinstance(action, actions.Action):
            if 'Command' in action:
                klass = actions.Command
            else:
                klass = actions.Action
            action = klass(action, as_list=as_list)
        self.responses[action.id] = action
        if action.action_id:
            self.responses[action.action_id] = action
        action.future.add_done_callback(self.handle_future_messages)
        try:
            self.protocol.send(action, as_list=as_list)
        except errors.DisconnectedError:
            action.future.remove_done_callback(self.handle_future_messages)
            self.waiting_actions.put_nowait(action)
        # return action.future
        return action.high_level_future

    def handle_future_messages(self, future):
        try:
            result = first_response = future.result()
        except errors.DisconnectedError as e:
            if self.config['automatic_reconnection']:
                self.waiting_actions.put_nowait(e.action)
            else:
                e.action.high_level_future.set_exception(e)
        else:
            if isinstance(result, list):
                first_response = result[0]
            response = self.responses.pop(first_response['ActionID'])
            if response.action_id:
                self.responses.pop(response.action_id, None)
            response.high_level_future.set_result(result)

    def send_command(self, command, as_list=False):
        """Send a :class:`~panoramisk.actions.Command` to the server::

            manager = Manager()
            resp = manager.send_command('http show status')

        Return a response :class:`~panoramisk.message.Message`.
        See https://wiki.asterisk.org/wiki/display/AST/ManagerAction_Command
        """
        action = actions.Action({'Command': command, 'Action': 'Command'},
                                as_list=as_list)
        return self.send_action(action)

    def send_agi_command(self, channel, command, as_list=False):
        """Send a :class:`~panoramisk.actions.Command` to the server:

        :param channel: Channel name where to launch command. Ex: 'SIP/000000-00000a53'
        :type channel: String
        :param command: command to launch. Ex: 'GET VARIABLE async_agi_server'
        :type command: String
        :param as_list: If True, the action Future will retrieve all responses
        :type as_list: boolean
        :return: a Future that will receive the response
        :rtype: asyncio.Future

        :Example:

        ::

            manager = Manager()
            resp = manager.send_agi_command('SIP/000000-00000a53',
                                            'GET VARIABLE async_agi_server')


        Return a response :class:`~panoramisk.message.Message`.
        See https://wiki.asterisk.org/wiki/display/AST/Asterisk+11+ManagerAction_AGI
        """
        action = actions.Command({'Action': 'AGI',
                                  'Channel': channel,
                                  'Command': command},
                                 as_list=as_list)
        return self.send_action(action)

    def connect(self):
        """connect to the server"""
        if self.loop is None:  # pragma: no cover
            self.loop = asyncio.get_event_loop()
        t = asyncio.Task(
            self.loop.create_connection(
                self.config['protocol_factory'],
                self.config['host'], self.config['port'],
                ssl=self.config['ssl']),
            loop=self.loop)
        t.add_done_callback(self.connection_made)
        return t

    def register_event(self, pattern, callback=None):
        """register an event. See :class:`~panoramisk.message.Message`:

        .. code-block:: python

            >>> def callback(event, manager):
            ...     print(event, manager)
            >>> manager = Manager()
            >>> manager.register_event('Meetme*', callback)
            <function callback at 0x...>

        You can also use the manager as a decorator:

        .. code-block:: python

            >>> manager = Manager()
            >>> @manager.register_event('Meetme*')
            ... def callback(manager, event):
            ...     print(manager, event)
        """
        def _register_event(callback):
            self.patterns.append((pattern,
                                 re.compile(fnmatch.translate(pattern))))
            self.callbacks[pattern].append(callback)
            return callback
        if callback is not None:
            return _register_event(callback)
        else:
            return _register_event

    def dispatch(self, event):
        matches = []
        event.manager = self
        for pattern, regexp in self.patterns:
            match = regexp.match(event.event)
            if match is not None:
                matches.append(pattern)
                for callback in self.callbacks[pattern]:
                    ret = callback(self, event)
                    if (asyncio.iscoroutine(ret) or
                            isinstance(ret, asyncio.Future)):
                        asyncio.async(ret, loop=self.loop)
        return matches

    def close(self):
        """Close the connection"""
        if self.pinger:
            self.pinger.cancel()
            self.pinger = None
        if getattr(self, 'protocol', None):
            self.protocol.close()

    def connection_lost(self, exc):
        self.log.error('Connection lost')
        if self.pinger:
            self.pinger.cancel()
            self.pinger = None
        if self.config['automatic_reconnection']:
            self.log.info('Try to connect again in 2 seconds')
            self.loop.call_later(2, self.connect)
        else:
            raise errors.DisconnectedError(None)

    @classmethod
    def from_config(cls, filename_or_fd, section='asterisk'):
        return cls(**utils.config(filename_or_fd, section=section))
