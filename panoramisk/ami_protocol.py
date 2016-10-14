import logging
import asyncio
from collections import deque

from .message import Message
from . import actions
from . import utils


class AMIProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.closed = False
        self.queue = deque()
        self.responses = {}
        self.factory = None
        self.log = logging.getLogger(__name__)

    def send(self, data, as_list=False):
        encoding = getattr(self, 'encoding', 'ascii')
        if not isinstance(data, actions.Action):
            if 'Command' in data:
                klass = actions.Command
            else:
                klass = actions.Action
            data = klass(data, as_list=as_list)
        data.as_list = as_list
        self.responses[data.id] = data
        if data.action_id:
            self.responses[data.action_id] = data
        try:
            self.transport.write(str(data).encode(encoding))
        except Exception:  # pragma: no cover
            self.log.exception('Fail to send %r' % data)
        return data.future

    def data_received(self, data):
        encoding = getattr(self, 'encoding', 'ascii')
        data = data.decode(encoding, 'ignore')
        if getattr(self.factory, 'save_stream', None):  # pragma: no cover
            stream = self.factory.save_stream
            if hasattr(stream, 'write'):
                stream.write(data.encode(encoding))
            else:
                with open(stream, 'a+') as fd:
                    fd.write(data.encode(encoding))
        # Very verbose, uncomment only if necessary
        # self.log.debug('data received: "%s"', data)
        if self.queue:
            data = self.queue.popleft() + data
        lines = data.split(utils.EOL+utils.EOL)
        self.queue.append(lines.pop(-1))
        for line in lines:
            # Because sometimes me receive only one EOL from Asterisk
            line = line.strip()
            # Very verbose, uncomment only if necessary
            # self.log.debug('message received: "%s"', line)
            message = Message.from_line(line)
            self.log.debug('message interpreted: %r', message)
            if message is None:
                continue
            self.handle_message(message)

    def handle_message(self, message):
        response = self.responses.get(message.id)
        if response is None and message.action_id:
            response = self.responses.get(message.action_id)
        if response is not None:
            if response.add_message(message):
                # completed; dequeue
                self.responses.pop(response.id)
                if response.action_id:
                    self.responses.pop(response.action_id, None)
        elif 'event' in message:
            if message['event'].lower() == 'shutdown':
                self.connection_lost(message)
            self.factory.dispatch(message)

    def connection_lost(self, exc):
        if not self.closed:
            self.close()
            self.factory.connection_lost(exc)

    def close(self):
        if self.factory and self.responses:
            uuids = set()
            forgetable_actions = self.factory.forgetable_actions
            awaiting_actions = self.factory.awaiting_actions
            for k in list(self.responses.keys()):
                action = self.responses.pop(k)
                if action.id in uuids:
                    continue
                elif action['action'].lower() in forgetable_actions:
                    uuids.add(action.id)
                    continue
                elif action.future.done():  # pragma: no cover
                    uuids.add(action.id)
                    continue
                uuids.add(action.id)
                awaiting_actions.append(action)
        if not self.closed:
            try:
                self.transport.close()
            finally:
                self.closed = True
