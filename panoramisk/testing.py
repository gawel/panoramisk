# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import manager
from . import utils


try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock  # NOQA


MagicMock = mock.MagicMock
patch = mock.patch
call = mock.call


class Connection(manager.Connection):

    debug_count = [0]

    def connection_made(self, transport):
        super(Connection, self).connection_made(transport)
        self.transport = MagicMock()

    def send(self, data, as_list=False):
        utils.IdGenerator.reset(uid='transaction_uid')
        future = super(Connection, self).send(data, as_list=as_list)
        if self.factory.stream is not None:
            with open(self.factory.stream, 'rb') as fd:
                resp = fd.read()
            self.data_received(resp)
            if not future.done():  # pragma: no cover
                print(self.responses)
                raise AssertionError("Future's result was never set")
        return future


class Manager(manager.Manager):

    fixtures_dir = None

    def __init__(self, **config):
        self.defaults.update(
            connection_class=Connection,
            stream=None)
        super(Manager, self).__init__(**config)

        self.stream = self.config.get('stream')
        self.loop = utils.asyncio.get_event_loop()

        protocol = Connection()
        protocol.factory = manager
        protocol.connection_made(mock.MagicMock())
        future = utils.asyncio.Future()
        future.set_result((mock.MagicMock(), protocol))
        self.protocol = protocol
        self.connection_made(future)

        utils.IdGenerator.reset(uid='transaction_uid')
        utils.EOL = '\n'
