# -*- coding: utf-8 -*-
import logging
import time

from .message import Message
from .utils import asyncio
from . import actions
from . import errors
from . import utils


class AMIProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.closing = False
        self.queue = utils.Queue()
        self.responses = {}
        self.factory = None
        self.log = logging.getLogger(__name__)

    def send(self, data, as_list=False):
        encoding = getattr(self, 'encoding', 'ascii')
        if self.closing:
            raise errors.DisconnectedError(data)
        self.transport.write(str(data).encode(encoding))
        self.responses[data.id] = data
        if data.action_id:
            self.responses[data.action_id] = data
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
        if not self.queue.empty():
            data = self.queue.get_nowait() + data
        lines = data.split(utils.EOL+utils.EOL)
        self.queue.put_nowait(lines.pop(-1))
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
        elif 'Event' in message:
            if message['Event'] == 'Shutdown':
                self.connection_lost(message)
            self.factory.dispatch(message)

    def connection_lost(self, exc):  # pragma: no cover
        if not self.closing:
            self.close()
            self.factory.connection_lost(exc)

    def close(self):  # pragma: no cover
        if not self.closing:
            self.closing = True
            for idx in self.responses:
                if not self.responses[idx].future.done():
                    self.responses[idx].future.set_exception(errors.DisconnectedError(self.responses[idx]))
            self.transport.close()
            del self

