# -*- coding: utf-8 -*-
import time
import logging
import asyncio
from asyncio.queues import Queue

from .message import Message
from . import actions
from . import utils


class AMIProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.closed = False
        self.queue = Queue()
        self.responses = {}
        self.factory = None
        self.log = logging.getLogger(__name__)

    def is_closing(self):
        if self.closed:
            return True
        # py35
        is_closing = getattr(self.transport, 'is_closing', None)
        if is_closing is not None:
            return is_closing()
        return False

    def send(self, data, as_list=False):
        encoding = getattr(self, 'encoding', 'ascii')
        if not isinstance(data, actions.Action):
            if 'Command' in data:
                klass = actions.Command
            else:
                klass = actions.Action
            data = klass(data, as_list=as_list)
        if self.is_closing():
            self.factory.awaiting_actions.put_nowait((data, as_list))
        else:
            try:
                self.transport.write(str(data).encode(encoding))
            except Exception as e:
                self.factory.log.exception(e)
                self.factory.awaiting_actions.put_nowait((data, as_list))
            else:
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
            self.factory.dispatch(message)

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
