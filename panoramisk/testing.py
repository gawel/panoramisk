# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import panoramisk


try:
    from unittest import mock
except ImportError:
    import mock


MagicMock = mock.MagicMock
patch = mock.patch
call = mock.call


class Connection(panoramisk.Connection):

    debug_count = [0]

    def connection_made(self, transport):
        super(Connection, self).connection_made(transport)
        self.transport = MagicMock()

    def send(self, data, as_list=False):
        panoramisk.IdGenerator.reset(uid='transaction_uid')
        future = super(Connection, self).send(data, as_list=as_list)
        self.get_stream(future)
        return future

    def get_stream(self, future):
        if self.factory.stream is not None:
            with open(self.factory.stream, 'rb') as fd:
                resp = fd.read()
            self.data_received(resp)
            if not future.done():
                print(self.responses)
                raise AssertionError("Future's result was never set")


class Manager(panoramisk.Manager):

    def __init__(self, **config):
        self.defaults['connection_class'] = Connection
        super(Manager, self).__init__(**config)
        self.stream = config.get('stream')
        panoramisk.IdGenerator.reset(uid='transaction_uid')
        panoramisk.EOL = '\n'
