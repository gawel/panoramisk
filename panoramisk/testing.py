# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs

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
        future = super(Connection, self).send(data, as_list=as_list)
        self.get_stream()
        if future.done():
            return future
        else:
            raise AssertionError("Future's result was never set")

    def get_stream(self):
        if self.factory.stream is not None:
            with codecs.open(self.factory.stream, encoding='utf8') as fd:
                resp = fd.read()
            self.data_received(resp)


class Manager(panoramisk.Manager):

    def __init__(self, **config):
        self.defaults['connection_class'] = Connection
        super(Manager, self).__init__(**config)
        self.stream = config.get('stream')
        panoramisk.IdGenerator.reset(uid='transaction_uid')
        panoramisk.EOL = '\n'
